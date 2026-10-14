from datetime import datetime, timedelta

from django.core import mail
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    AppliedJobs,
    ApplicantProfile,
    ApplicantSkills,
    ApplicantWorkExperience,
    EmployerProfile,
    GovernmentInternshipProgram,
    Jobs,
    OfferedJobs,
    SpecialProgramForEmploymentOfStudents,
    User,
)
from .services.profile_sensitivity import (
    classify_profile_changes,
    mark_profile_for_reverification,
)
from .service import generate_complete_peso_matrix
from .views import EnrollBeneficiaryView, SpecialProgramsListView


class ProfileFieldSensitivityTests(SimpleTestCase):
    def test_applicant_phone_changes_are_sensitive_but_minor_address_edits_are_not(self):
        classification = classify_profile_changes(
            ApplicantProfile,
            {
                'education_level',
                'skill_welding',
                'phone_number',
                'mobile_number_secondary',
                'landline_number',
                'house_street',
                'municipality',
            },
        )

        self.assertEqual(
            classification.sensitive_fields,
            frozenset({
                'education_level',
                'skill_welding',
                'municipality',
                'phone_number',
                'mobile_number_secondary',
                'landline_number',
            }),
        )
        self.assertEqual(
            classification.non_sensitive_fields,
            frozenset({'house_street'}),
        )
        self.assertTrue(classification.requires_reverification)

        address_only = classify_profile_changes(
            ApplicantProfile,
            {'house_street', 'barangay'},
        )
        self.assertFalse(address_only.requires_reverification)

    def test_applicant_skills_and_work_history_are_sensitive(self):
        skills = classify_profile_changes(ApplicantSkills, {'skill_name'})
        work = classify_profile_changes(
            ApplicantWorkExperience,
            {'company', 'position', 'dates'},
        )

        self.assertTrue(skills.requires_reverification)
        self.assertEqual(skills.sensitive_fields, frozenset({'skill_name'}))
        self.assertTrue(work.requires_reverification)
        self.assertEqual(
            work.sensitive_fields,
            frozenset({'company', 'position', 'dates'}),
        )

    def test_employer_phone_changes_are_sensitive_but_other_contact_edits_are_not(self):
        classification = classify_profile_changes(
            EmployerProfile,
            {
                'tin_number',
                'business_permit',
                'business_name',
                'mobile_number',
                'telephone_number',
                'email',
            },
        )

        self.assertEqual(
            classification.sensitive_fields,
            frozenset({
                'tin_number',
                'business_permit',
                'business_name',
                'mobile_number',
                'telephone_number',
            }),
        )
        self.assertEqual(
            classification.non_sensitive_fields,
            frozenset({'email'}),
        )

    def test_user_profile_picture_is_non_sensitive_and_unclassified_fields_fail_safe(self):
        classification = classify_profile_changes(
            User,
            {'profile_picture', 'new_credential_field'},
        )

        self.assertEqual(
            classification.non_sensitive_fields,
            frozenset({'profile_picture'}),
        )
        self.assertEqual(
            classification.sensitive_fields,
            frozenset({'new_credential_field'}),
        )


class ProfileReverificationStatusTests(TestCase):
    def setUp(self):
        self.applicant_user = User.objects.create_user(
            username='reverify-applicant',
            email='reverify-applicant@example.com',
            password='test-password',
            role='applicant',
        )
        self.applicant = ApplicantProfile.objects.create(
            user=self.applicant_user,
            first_name='Reverify',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            status='approved',
        )
        self.employer_user = User.objects.create_user(
            username='reverify-employer',
            email='reverify-employer@example.com',
            password='test-password',
            role='employer',
        )
        self.employer = EmployerProfile.objects.create(
            user=self.employer_user,
            business_name='Reverify Employer',
            verification_status='verified',
        )

    def test_sensitive_applicant_change_moves_approved_profile_to_reverification_pending(self):
        changed = mark_profile_for_reverification(
            self.applicant,
            {'phone_number'},
        )

        self.assertTrue(changed)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'reverify_pending')

    def test_non_sensitive_applicant_change_keeps_approved_profile(self):
        changed = mark_profile_for_reverification(
            self.applicant,
            {'house_street'},
        )

        self.assertFalse(changed)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'approved')

    def test_sensitive_employer_change_moves_verified_profile_to_reverification_pending(self):
        changed = mark_profile_for_reverification(
            self.employer,
            {'business_permit'},
        )

        self.assertTrue(changed)
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.verification_status, 'reverify_pending')


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='CAPESONNECT System <system@example.com>',
)
class HelpViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='help-admin',
            email='help-admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin)

    def test_support_report_is_sent_to_system_email_with_admin_as_reply_to(self):
        response = self.client.post(reverse('AdminSide:account_help'), {
            'subject': 'Cannot approve applicant',
            'message': 'The approval page shows an error.',
        })

        self.assertRedirects(response, reverse('AdminSide:account_help'))
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['capessonect650@gmail.com'])
        self.assertEqual(sent_email.reply_to, [self.admin.email])
        self.assertEqual(sent_email.from_email, 'CAPESONNECT System <system@example.com>')
        self.assertIn('The approval page shows an error.', sent_email.body)

    def test_support_report_requires_subject_and_message(self):
        response = self.client.post(reverse('AdminSide:account_help'), {
            'subject': '',
            'message': '   ',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['support_modal_open'])
        self.assertContains(response, 'Enter both a subject and a description of the issue.')
        self.assertEqual(mail.outbox, [])


class DashboardViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='dashboard-admin',
            email='dashboard-admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin)

    def create_applicant(self, username):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='test-password',
        )
        return ApplicantProfile.objects.create(
            user=user,
            first_name='Test',
            last_name=username,
            date_of_birth='1995-01-01',
            sex='F',
            civil_status='single',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            education_level='college',
        )

    def create_employer(self, username):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='test-password',
            role='employer',
        )
        return EmployerProfile.objects.create(
            user=user,
            business_name=f'{username} business',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            contact_person='Test Contact',
            mobile_number='09123456789',
            email=f'{username}-profile@example.com',
        )

    def test_reverification_profiles_are_prioritized_in_pending_approvals(self):
        applicant = self.create_applicant('dashboard-reverify-applicant')
        applicant.status = 'reverify_pending'
        applicant.save(update_fields=['status'])
        employer = self.create_employer('dashboard-reverify-employer')
        employer.verification_status = 'reverify_pending'
        employer.save(update_fields=['verification_status'])

        response = self.client.get(reverse('AdminSide:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(applicant, response.context['pending_approvals'])
        self.assertIn(employer, response.context['pending_approvals'])
        self.assertContains(response, 'Updated - Needs Audit')

    def test_stat_cards_show_database_metrics_and_keep_their_destinations(self):
        today = timezone.localdate()
        previous_month_last_day = today.replace(day=1) - timedelta(days=1)
        previous_month_start = previous_month_last_day.replace(day=1)
        previous_month_registration = timezone.make_aware(
            datetime.combine(previous_month_start + timedelta(days=5), datetime.min.time())
        )

        previous_applicants = [
            self.create_applicant('dashboard-applicant-old-1'),
            self.create_applicant('dashboard-applicant-old-2'),
        ]
        for applicant in previous_applicants:
            ApplicantProfile.objects.filter(pk=applicant.pk).update(
                created_at=previous_month_registration
            )
        current_applicant = self.create_applicant('dashboard-applicant-current')

        previous_employer = self.create_employer('dashboard-employer-old')
        EmployerProfile.objects.filter(pk=previous_employer.pk).update(
            created_at=previous_month_registration
        )
        self.create_employer('dashboard-employer-current')

        employer = self.create_employer('dashboard-job-employer')
        urgent_job = Jobs.objects.create(
            employer=employer,
            job_title='Expiring soon',
            job_description='Test job posting.',
            place_of_work='Carigara, Leyte',
            salary='1000.00',
            vacancy=1,
            job_posting_expiry=today + timedelta(days=3),
        )
        Jobs.objects.create(
            employer=employer,
            job_title='Expiring later',
            job_description='Test job posting.',
            place_of_work='Carigara, Leyte',
            salary='1000.00',
            vacancy=1,
            job_posting_expiry=today + timedelta(days=14),
        )

        current_referral = OfferedJobs.objects.create(
            applicant=current_applicant,
            offered_job=urgent_job,
            status='hired',
        )
        previous_week_start = today - timedelta(days=today.weekday() + 1)
        OfferedJobs.objects.create(
            applicant=previous_applicants[0],
            offered_job=urgent_job,
            status='near_hire',
        )
        OfferedJobs.objects.filter(status='near_hire').update(
            date_offered=timezone.make_aware(
                datetime.combine(previous_week_start, datetime.min.time())
            )
        )
        AppliedJobs.objects.create(
            applicant=current_applicant,
            applied_job=urgent_job,
            status='hired',
        )
        AppliedJobs.objects.create(
            applicant=previous_applicants[1],
            applied_job=urgent_job,
            status='near_hire',
        )

        response = self.client.get(reverse('AdminSide:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['applicant_count'], 3)
        self.assertEqual(response.context['applicant_change_display'], '-50%')
        self.assertEqual(response.context['monthly_new_employers'], 2)
        self.assertEqual(response.context['active_job_count'], 2)
        self.assertEqual(response.context['urgent_job_count'], 1)
        self.assertEqual(response.context['referral_count'], 2)
        self.assertEqual(response.context['weekly_referral_count'], 1)
        self.assertEqual(response.context['placement_count'], 2)
        self.assertEqual(response.context['placement_rate'], 50.0)
        self.assertEqual(response.context['near_hire_count'], 2)
        self.assertContains(response, reverse('AdminSide:applicants_list'))
        self.assertContains(response, reverse('AdminSide:employer_list'))
        self.assertContains(response, f'{reverse("AdminSide:job_postings_list")}?status=Active')
        self.assertContains(response, f'{reverse("AdminSide:referrals_list")}?status=hired')
        self.assertContains(response, f'{reverse("AdminSide:referrals_list")}?status=near_hire')


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='CAPESONNECT System <system@example.com>',
)
class ApplicantVerificationEmailTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='applicant-verify-email-admin',
            email='applicant-verify-email-admin@example.com',
            password='test-password',
        )
        self.applicant_user = User.objects.create_user(
            username='applicant-verify-email-user',
            email='applicant-verify-email@example.com',
            password='test-password',
            role='applicant',
        )
        self.applicant = ApplicantProfile.objects.create(
            user=self.applicant_user,
            first_name='Email',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
        )
        self.client.force_login(self.admin)

    def test_verifying_applicant_sends_account_verified_email_once(self):
        url = reverse(
            'AdminSide:applicant_verification',
            kwargs={'uuid': self.applicant.uuid},
        )

        response = self.client.post(url, {'action': 'verify'})

        self.assertRedirects(response, url)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'approved')
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, [self.applicant_user.email])
        self.assertEqual(
            sent_email.subject,
            'Your CAPESONNECT account has been verified',
        )
        self.assertIn('account has been verified', sent_email.body)
        self.assertIn('apply for available job opportunities', sent_email.body)

        self.client.post(url, {'action': 'verify'})
        self.assertEqual(len(mail.outbox), 1)

    def test_applicant_approval_from_registry_sends_verified_email(self):
        response = self.client.post(
            reverse('AdminSide:applicants_list'),
            {
                'applicant_uuid': str(self.applicant.uuid),
                'status': 'approved',
            },
        )

        self.assertRedirects(response, reverse('AdminSide:applicants_list'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.applicant_user.email])


class JobVacancyCreateViewTests(TestCase):
    def test_post_creates_active_vacancy_for_verified_employer(self):
        admin = User.objects.create_user(
            username='vacancy-admin',
            email='vacancy-admin@example.com',
            password='test-password',
        )
        employer_user = User.objects.create_user(
            username='verified-employer',
            email='verified-employer@example.com',
            password='test-password',
            role='employer',
        )
        employer = EmployerProfile.objects.create(
            user=employer_user,
            business_name='Verified Test Employer',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            contact_person='Test Contact',
            mobile_number='09123456789',
            email='verified-employer-profile@example.com',
            verification_status='verified',
        )
        self.client.force_login(admin)

        response = self.client.post(reverse('AdminSide:job_create'), {
            'employer': employer.pk,
            'job_title': 'Vacancy workflow test',
            'job_description': 'A complete test vacancy description.',
            'nature_of_work': 'permanent',
            'place_of_work': 'Carigara, Leyte',
            'salary': '1000.00',
            'vacancy': '1',
            'work_experience_months': '0',
            'job_posting_expiry': '2099-12-31',
        })

        self.assertRedirects(response, reverse('AdminSide:job_postings_list'))
        job = Jobs.objects.get(job_title='Vacancy workflow test')
        self.assertEqual(job.employer, employer)
        self.assertEqual(job.status, 'Active')


class AdminLoginViewTests(TestCase):
    def test_repeated_invalid_credentials_show_only_one_current_message(self):
        client = Client()
        login_url = reverse('AdminSide:admin_login')
        error_message = 'Invalid administrator credentials! Please Try Again.'

        for _ in range(2):
            response = client.post(login_url, {'username': 'invalid', 'password': 'invalid'})

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, error_message)
            self.assertEqual(response.content.decode().count(error_message), 1)


class EnrollBeneficiaryViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = EnrollBeneficiaryView()

    def test_get_instance_uses_the_configured_program_model(self):
        beneficiary = SpecialProgramForEmploymentOfStudents.objects.create(
            first_name='Ana',
            last_name='Rivera',
            sex='F',
            date_of_birth='2000-01-01',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1000.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
        )

        request = self.factory.get('/special-programs/enroll/', {'edit': beneficiary.uuid, 'program': 'spes'})
        instance = self.view.get_instance(request, {'model': SpecialProgramForEmploymentOfStudents})

        self.assertEqual(instance, beneficiary)

    def test_special_program_list_view_handles_search_query(self):
        request = self.factory.get('/special-programs/', {'program': 'spes', 'search': 'Ana'})
        response = SpecialProgramsListView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_edit_form_shows_unsaved_changes_warning_when_switching_programs(self):
        beneficiary = SpecialProgramForEmploymentOfStudents.objects.create(
            first_name='Ana',
            last_name='Rivera',
            sex='F',
            date_of_birth='2000-01-01',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1000.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
        )

        client = Client()
        response = client.get(f'/special-programs/enroll/?program=spes&edit={beneficiary.uuid}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please finish or save your changes before switching programs')

    def test_enroll_post_preserves_municipality_and_barangay_from_current_form_fields(self):
        client = Client()
        response = client.post('/special-programs/enroll/?program=spes', {
            'first_name': 'Ana',
            'middle_name': '',
            'last_name': 'Rivera',
            'sex': 'F',
            'date_of_birth': '2000-01-01',
            'phone_number': '09123456789',
            'barangay': 'Poblacion',
            'municipality': 'Carigara',
            'province': 'Leyte',
            'region': 'VIII',
            'zip_code': '6529',
            'daily_salary': '1000',
            'start_date': '2024-01-01',
            'end_date': '2024-02-01',
            'education_level': 'college',
        })

        self.assertEqual(response.status_code, 302)
        beneficiary = SpecialProgramForEmploymentOfStudents.objects.get(first_name='Ana')
        self.assertEqual(beneficiary.municipality, 'Carigara')
        self.assertEqual(beneficiary.barangay, 'Poblacion')

    def test_generate_complete_peso_matrix_counts_special_program_data(self):
        SpecialProgramForEmploymentOfStudents.objects.create(
            first_name='Ana',
            last_name='Rivera',
            sex='F',
            date_of_birth='2000-01-01',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1000.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
            has_graduated=True,
            has_nc_certification=True,
            is_absorbed_by_employer=True,
        )

        GovernmentInternshipProgram.objects.create(
            first_name='Luis',
            last_name='Santos',
            sex='F',
            date_of_birth='1999-02-02',
            phone_number='09123456790',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            region='Region VIII',
            zip_code='6519',
            daily_salary='1200.00',
            start_date='2024-01-01',
            end_date='2024-02-01',
            education_level='college',
            has_nc_certification=True,
            is_absorbed_by_agency=True,
        )

        current_year = timezone.now().year
        current_month = timezone.now().month
        metrics = generate_complete_peso_matrix(current_year, current_month)

        self.assertEqual(metrics['spes_college'], 1)
        self.assertEqual(metrics['spes_graduates'], 1)
        self.assertEqual(metrics['spes_nc'], 1)
        self.assertEqual(metrics['spes_absorbed'], 1)
        self.assertEqual(metrics['gip_total'], 1)
        self.assertEqual(metrics['gip_female'], 1)
        self.assertEqual(metrics['gip_graduates_nc'], 1)
        self.assertEqual(metrics['gip_absorbed'], 1)

from datetime import datetime, timedelta

from django.core import mail
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .models import (
    AppliedJobs,
    ApplicantProfile,
    ApplicantSkills,
    ApplicantWorkExperience,
    EmployerProfile,
    GovernmentInternshipProgram,
    Jobs,
    Notification,
    OfferedJobs,
    ProfileChangeLog,
    SpecialProgramForEmploymentOfStudents,
    User,
)
from .services.profile_sensitivity import (
    capture_profile_changes,
    classify_profile_changes,
    clear_profile_changes,
    has_current_supporting_document,
    mark_profile_for_reverification,
    record_profile_changes,
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

    def test_user_profile_picture_and_email_are_non_sensitive_and_unknown_fields_fail_safe(self):
        classification = classify_profile_changes(
            User,
            {'profile_picture', 'email', 'new_credential_field'},
        )

        self.assertEqual(
            classification.non_sensitive_fields,
            frozenset({'profile_picture', 'email'}),
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

    def test_profile_change_log_keeps_only_sensitive_changes_for_current_review(self):
        self.applicant.phone_number = '09987654321'
        changes = capture_profile_changes(self.applicant)
        self.applicant.save()
        change_log = record_profile_changes(
            self.applicant,
            self.applicant_user,
            changes,
        )

        self.assertEqual(
            change_log.changes['phone_number'],
            {
                'label': 'Phone Number',
                'old': '',
                'new': '09987654321',
            },
        )
        self.assertIsNone(change_log.reviewed_at)

        self.applicant.house_street = 'New Street'
        non_sensitive_changes = capture_profile_changes(self.applicant)
        self.assertEqual(set(non_sensitive_changes), {'house_street'})
        self.applicant.save()
        reviewed_log = record_profile_changes(
            self.applicant,
            self.applicant_user,
            non_sensitive_changes,
        )
        self.assertIsNone(reviewed_log)
        self.assertEqual(
            ProfileChangeLog.objects.filter(applicant=self.applicant).count(),
            1,
        )

    def test_profile_change_logs_are_cleared_after_approval(self):
        ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={'phone_number': {'label': 'Phone Number', 'old': '', 'new': '123'}},
        )

        clear_profile_changes(self.applicant)

        self.assertFalse(ProfileChangeLog.objects.filter(applicant=self.applicant).exists())

    def test_new_verified_profile_change_starts_a_fresh_audit_cycle(self):
        ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={'education_level': {'label': 'Education Level', 'old': 'High School', 'new': 'College'}},
            reviewed_at=timezone.now(),
        )
        self.applicant.phone_number = '09123456789'
        self.applicant.save()

        fresh_log = record_profile_changes(
            self.applicant,
            self.applicant_user,
            {'phone_number': {'label': 'Phone Number', 'old': '', 'new': '09123456789'}},
        )

        self.assertEqual(ProfileChangeLog.objects.filter(applicant=self.applicant).count(), 1)
        self.assertEqual(
            fresh_log.changes,
            {'phone_number': {'label': 'Phone Number', 'old': '', 'new': '09123456789'}},
        )

    def test_education_proof_must_be_newer_than_unreviewed_education_changes(self):
        ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={
                'school_university': {
                    'label': 'School University',
                    'old': 'Old School',
                    'new': 'New School',
                },
            },
        )
        ApplicantProfile.objects.filter(pk=self.applicant.pk).update(
            education_proof_document='applicant_docs/education_proofs/proof.pdf',
            education_proof_uploaded_at=timezone.now() - timedelta(minutes=1),
        )
        self.applicant.refresh_from_db()

        self.assertFalse(has_current_supporting_document(self.applicant))

        ApplicantProfile.objects.filter(pk=self.applicant.pk).update(
            education_proof_uploaded_at=timezone.now() + timedelta(seconds=1),
        )
        self.applicant.refresh_from_db()
        self.assertTrue(has_current_supporting_document(self.applicant))


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

    def test_notification_header_api_returns_ten_latest_notifications(self):
        for index in range(11):
            Notification.objects.create(
                recipient=self.admin,
                title=f'Notification {index}',
                message=f'Message {index}',
                notification_type='NEW_APPLICANT',
            )

        response = self.client.get(
            reverse('AdminSide:notifications_header_api'),
        )

        self.assertEqual(response.status_code, 200)
        notifications = response.json()['notifications']
        self.assertEqual(len(notifications), 10)
        self.assertEqual(notifications[0]['title'], 'Notification 10')
        self.assertNotIn('Notification 0', [item['title'] for item in notifications])

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

    def test_applicant_modification_audit_opens_from_review_button_and_clears_on_approval(self):
        self.applicant.status = 'reverify_pending'
        self.applicant.save(update_fields=['status'])
        log = ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={
                'phone_number': {
                    'label': 'Phone Number',
                    'old': '09123456789',
                    'new': '09987654321',
                },
            },
        )
        url = reverse(
            'AdminSide:applicant_verification',
            kwargs={'uuid': self.applicant.uuid},
        )

        page = self.client.get(url)

        self.assertContains(page, 'Review Updates')
        self.assertContains(
            page,
            reverse(
                'AdminSide:applicant_modification_audit',
                kwargs={'uuid': self.applicant.uuid},
            ),
        )
        self.assertNotContains(page, '09123456789')

        audit_url = reverse(
            'AdminSide:applicant_modification_audit',
            kwargs={'uuid': self.applicant.uuid},
        )
        audit_page = self.client.get(audit_url)
        self.assertContains(audit_page, 'Field')
        self.assertContains(audit_page, 'Old Value')
        self.assertContains(audit_page, 'New Value')
        self.assertContains(audit_page, 'Date and Time')
        self.assertContains(audit_page, 'Phone Number')
        self.assertContains(audit_page, '09123456789')
        self.assertContains(audit_page, '09987654321')

        response = self.client.post(url, {'action': 'verify'})

        self.assertRedirects(response, url)
        self.assertFalse(ProfileChangeLog.objects.filter(pk=log.pk).exists())
        self.assertNotContains(self.client.get(url), 'Review Updates')

    def test_applicant_verification_displays_latest_education_form_values(self):
        ApplicantProfile.objects.filter(pk=self.applicant.pk).update(
            school_status_yes=True,
            edu_college_level=True,
            school_university='Updated State University',
            course_program='Updated Engineering Program',
            year_graduated_attended='2025-05',
            award_1='Updated Academic Award',
            education_level='high_school',
            school_name='Previous School',
            year_graduated='2000',
        )
        url = reverse(
            'AdminSide:applicant_verification',
            kwargs={'uuid': self.applicant.uuid},
        )

        response = self.client.get(url)

        self.assertContains(response, 'Currently in school')
        self.assertContains(response, 'Yes')
        self.assertContains(response, 'College Level')
        self.assertContains(response, 'Updated State University')
        self.assertContains(response, 'Updated Engineering Program')
        self.assertContains(response, '2025-05')
        self.assertContains(response, 'Updated Academic Award')
        self.assertNotContains(response, 'Previous School')

    def test_applicant_verification_links_education_proof_document(self):
        ApplicantProfile.objects.filter(pk=self.applicant.pk).update(
            education_proof_document=(
                'applicant_docs/education_proofs/diploma.pdf'
            ),
            education_proof_uploaded_at=timezone.now(),
        )
        storage = ApplicantProfile._meta.get_field(
            'education_proof_document'
        ).storage
        url = reverse(
            'AdminSide:applicant_verification',
            kwargs={'uuid': self.applicant.uuid},
        )

        with patch.object(
            storage,
            'url',
            return_value='https://files.example/diploma.pdf',
        ):
            response = self.client.get(url)

        self.assertContains(response, 'Profile Proof Documents')
        self.assertContains(
            response,
            'href="https://files.example/diploma.pdf"',
        )
        self.assertContains(
            response,
            'View diploma / transcript / graduation certificate',
        )

    def test_reverification_approval_requires_current_education_proof(self):
        self.applicant.status = 'reverify_pending'
        self.applicant.save(update_fields=['status'])
        ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={
                'school_university': {
                    'label': 'School University',
                    'old': 'Old School',
                    'new': 'New School',
                },
            },
        )
        url = reverse(
            'AdminSide:applicant_verification',
            kwargs={'uuid': self.applicant.uuid},
        )

        blocked_response = self.client.post(url, {'action': 'verify'})

        self.assertRedirects(blocked_response, url)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'reverify_pending')

        upload_time = timezone.now()
        ApplicantProfile.objects.filter(pk=self.applicant.pk).update(
            education_proof_document='applicant_docs/education_proofs/proof.pdf',
            education_proof_uploaded_at=upload_time,
        )

        response = self.client.post(url, {'action': 'verify'})

        self.assertRedirects(response, url)
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'approved')

    def test_applicant_registry_cannot_bypass_supporting_document_approval_gate(self):
        self.applicant.status = 'reverify_pending'
        self.applicant.save(update_fields=['status'])

        response = self.client.post(
            reverse('AdminSide:applicants_list'),
            {
                'applicant_uuid': str(self.applicant.uuid),
                'status': 'approved',
            },
        )

        self.assertRedirects(
            response,
            reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': self.applicant.uuid},
            ),
        )
        self.applicant.refresh_from_db()
        self.assertEqual(self.applicant.status, 'reverify_pending')

    def test_employer_modification_audit_opens_from_review_button_and_clears_on_approval(self):
        employer_user = User.objects.create_user(
            username='employer-delta-user',
            email='employer-delta@example.com',
            password='test-password',
            role='employer',
        )
        employer = EmployerProfile.objects.create(
            user=employer_user,
            business_name='Delta Employer',
            verification_status='reverify_pending',
        )
        log = ProfileChangeLog.objects.create(
            employer=employer,
            changed_by=employer_user,
            changes={
                'mobile_number': {
                    'label': 'Mobile Number',
                    'old': '09123456789',
                    'new': '09987654321',
                },
            },
        )
        url = reverse(
            'AdminSide:employer_verification',
            kwargs={'uuid': employer.uuid},
        )

        page = self.client.get(url)

        self.assertContains(page, 'Review Updates')
        audit_url = reverse(
            'AdminSide:employer_modification_audit',
            kwargs={'uuid': employer.uuid},
        )
        self.assertContains(page, audit_url)
        self.assertNotContains(page, '09123456789')
        audit_page = self.client.get(audit_url)
        self.assertContains(audit_page, 'Mobile Number')
        self.assertContains(audit_page, '09123456789')
        self.assertContains(audit_page, '09987654321')

        response = self.client.post(url, {'action': 'approve'})

        self.assertRedirects(response, url)
        self.assertFalse(ProfileChangeLog.objects.filter(pk=log.pk).exists())

    def test_applicant_audit_shows_education_proof_beside_changed_information(self):
        self.applicant.status = 'reverify_pending'
        self.applicant.save(update_fields=['status'])
        ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={
                'phone_number': {
                    'label': 'Phone Number',
                    'old': 'OLD VERIFIED VALUE',
                    'new': 'OLD REVIEWED VALUE',
                },
            },
            reviewed_at=timezone.now(),
        )
        ProfileChangeLog.objects.create(
            applicant=self.applicant,
            changed_by=self.applicant_user,
            changes={
                'school_university': {
                    'label': 'School University',
                    'old': 'Old University',
                    'new': 'New University',
                },
                'supporting_doc': {
                    'label': 'Supporting Document',
                    'old': 'applicant_docs/supporting_docs/old.pdf',
                    'new': 'applicant_docs/supporting_docs/new.pdf',
                },
                'education_proof_document': {
                    'label': 'Education Proof Document',
                    'old': '',
                    'new': 'applicant_docs/education_proofs/diploma.pdf',
                },
            },
        )
        ApplicantProfile.objects.filter(pk=self.applicant.pk).update(
            education_proof_document=(
                'applicant_docs/education_proofs/diploma.pdf'
            ),
        )
        storage = ApplicantProfile._meta.get_field(
            'education_proof_document'
        ).storage
        audit_url = reverse(
            'AdminSide:applicant_modification_audit',
            kwargs={'uuid': self.applicant.uuid},
        )

        with patch.object(
            storage,
            'url',
            side_effect=lambda name: f'https://files.example/{name}',
        ):
            page = self.client.get(audit_url)

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Supporting Document')
        self.assertContains(page, 'href="https://files.example/applicant_docs/education_proofs/diploma.pdf"')
        self.assertContains(page, 'New University')
        self.assertNotContains(
            page,
            '<span class="text-slate-400">—</span>',
        )
        self.assertNotContains(page, 'applicant_docs/supporting_docs/old.pdf')
        self.assertNotContains(page, 'applicant_docs/supporting_docs/new.pdf')
        self.assertNotContains(page, 'Education Proof Document')
        self.assertNotContains(page, 'OLD VERIFIED VALUE')
        self.assertNotContains(page, 'OLD REVIEWED VALUE')

    def test_employer_audit_shows_registration_document_beside_changed_information(self):
        employer_user = User.objects.create_user(
            username='employer-file-audit-user',
            email='employer-file-audit@example.com',
            password='test-password',
            role='employer',
        )
        employer = EmployerProfile.objects.create(
            user=employer_user,
            business_name='File Audit Employer',
            verification_status='reverify_pending',
        )
        ProfileChangeLog.objects.create(
            employer=employer,
            changed_by=employer_user,
            changes={
                'business_name': {
                    'label': 'Business Name',
                    'old': 'Old Business Name',
                    'new': 'Updated Business Name',
                },
                'business_permit': {
                    'label': 'Business Permit',
                    'old': 'employer_docs/old-permit.pdf',
                    'new': 'employer_docs/new-permit.pdf',
                },
            },
        )
        EmployerProfile.objects.filter(pk=employer.pk).update(
            business_permit='employer_docs/new-permit.pdf',
        )
        storage = EmployerProfile._meta.get_field('business_permit').storage
        audit_url = reverse(
            'AdminSide:employer_modification_audit',
            kwargs={'uuid': employer.uuid},
        )

        with patch.object(
            storage,
            'url',
            side_effect=lambda name: f'https://files.example/{name}',
        ):
            page = self.client.get(audit_url)

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Supporting Document')
        self.assertContains(page, 'href="https://files.example/employer_docs/new-permit.pdf"')
        self.assertContains(page, 'Updated Business Name')
        self.assertNotContains(
            page,
            '<span class="text-slate-400">—</span>',
        )
        self.assertNotContains(page, 'employer_docs/old-permit.pdf')
        self.assertNotContains(page, 'Business Permit</th>')

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


class EnrollBeneficiaryLookupTests(TestCase):
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
        request.user = User.objects.create_superuser(
            username='special-program-search-admin',
            email='special-program-search-admin@example.com',
            password='test-password',
        )
        response = SpecialProgramsListView.as_view()(request)

        self.assertEqual(response.status_code, 200)


class AdminListPaginationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='list-pagination-admin',
            email='list-pagination-admin@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin)

    def test_admin_lists_show_at_most_ten_records_per_page(self):
        applicants = []
        employers = []
        for index in range(11):
            applicant_user = User.objects.create_user(
                username=f'list-applicant-{index}',
                email=f'list-applicant-{index}@example.com',
                password='test-password',
                role='applicant',
            )
            applicants.append(ApplicantProfile.objects.create(
                user=applicant_user,
                first_name=f'Applicant{index}',
                last_name='Pagination',
                date_of_birth='1995-01-01',
                sex='F',
            ))

            employer_user = User.objects.create_user(
                username=f'list-employer-{index}',
                email=f'list-employer-{index}@example.com',
                password='test-password',
                role='employer',
            )
            employers.append(EmployerProfile.objects.create(
                user=employer_user,
                business_name=f'Employer {index}',
            ))

        jobs = []
        for index in range(11):
            jobs.append(Jobs.objects.create(
                employer=employers[index],
                job_title=f'Pagination Job {index}',
                job_description='Test vacancy',
                place_of_work='Carigara',
                salary=10000,
                vacancy=1,
                job_posting_expiry='2099-12-31',
            ))
            OfferedJobs.objects.create(
                applicant=applicants[index],
                offered_job=jobs[index],
            )
            SpecialProgramForEmploymentOfStudents.objects.create(
                first_name=f'Beneficiary{index}',
                last_name='Pagination',
                sex='F',
                date_of_birth='2000-01-01',
                phone_number='09123456789',
                barangay='Poblacion',
                municipality='Carigara',
                province='Leyte',
                region='Region VIII',
                zip_code='6519',
                daily_salary=1000,
                start_date='2024-01-01',
                end_date='2024-02-01',
                education_level='college',
            )

        list_requests = (
            (
                'AdminSide:applicants_list',
                'applicants',
            ),
            (
                'AdminSide:job_postings_list',
                'jobs',
            ),
            (
                'AdminSide:employer_list',
                'employers',
            ),
            (
                'AdminSide:referrals_list',
                'application_statuses',
            ),
            (
                'AdminSide:special_programs_list',
                'beneficiaries',
            ),
        )
        query_params = {
            'AdminSide:special_programs_list': '?program=spes',
        }
        for url_name, context_name in list_requests:
            suffix = query_params.get(url_name, '')
            response = self.client.get(reverse(url_name) + suffix)

            self.assertEqual(response.status_code, 200, url_name)
            self.assertEqual(len(response.context[context_name]), 10, url_name)
            self.assertEqual(response.context['page_obj'].paginator.num_pages, 2, url_name)
            self.assertIn('date added', response.content.decode().lower())

        applicant_page = self.client.get(reverse('AdminSide:applicants_list'))
        self.assertContains(applicant_page, 'VIEW')
        job_page = self.client.get(reverse('AdminSide:job_postings_list'))
        self.assertContains(job_page, 'VIEW')


class EnrollBeneficiaryViewTests(TestCase):
    def setUp(self):
        admin = User.objects.create_superuser(
            username='enroll-beneficiary-admin',
            email='enroll-beneficiary-admin@example.com',
            password='test-password',
        )
        self.client.force_login(admin)

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

        response = self.client.get(
            reverse('AdminSide:enroll_beneficiary'),
            {'program': 'spes', 'edit': beneficiary.uuid},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please finish or save your changes before switching programs')

    def test_enroll_post_preserves_municipality_and_barangay_from_current_form_fields(self):
        response = self.client.post(reverse('AdminSide:enroll_beneficiary'), {
            'program': 'spes',
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

        self.assertEqual(response.status_code, 200)
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

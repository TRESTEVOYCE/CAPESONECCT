from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from AdminSide.models import (
    ApplicantProfile,
    AppliedJobs,
    EmployerProfile,
    Jobs,
    Notification,
    ProfileChangeLog,
    User,
)
from .forms import ApplicantDocumentsForm, ApplicantEducationForm


class ApplicantProfileOnboardingTests(TestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            username='onboarding-applicant',
            email='onboarding-applicant@example.com',
            password='test-password',
            role='applicant',
        )
        self.client = Client()
        self.client.force_login(self.applicant)

    def test_personal_information_get_does_not_create_an_incomplete_profile(self):
        response = self.client.get(reverse('personal_info'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ApplicantProfile.objects.filter(user=self.applicant).exists())

    def test_valid_personal_information_post_creates_the_profile(self):
        response = self.client.post(reverse('personal_info'), {
            'first_name': 'Test',
            'last_name': 'Applicant',
            'date_of_birth': '1995-01-01',
            'nationality': 'Filipino',
            'sex_male': 'on',
            'civil_single': 'on',
            'emp_unemployed': 'on',
        })

        self.assertRedirects(response, reverse('applicant-address'))
        profile = ApplicantProfile.objects.get(user=self.applicant)
        self.assertEqual(profile.first_name, 'Test')
        self.assertEqual(profile.sex, 'M')
        self.assertEqual(profile.civil_status, 'single')
        self.assertIsNone(profile.phone_number)
        self.assertIsNone(profile.education_level)

    def test_later_onboarding_step_redirects_without_creating_a_profile(self):
        response = self.client.get(reverse('applicant-address'))

        self.assertRedirects(response, reverse('personal_info'))
        self.assertFalse(ApplicantProfile.objects.filter(user=self.applicant).exists())

    def test_address_fields_are_required_on_the_address_step(self):
        profile = ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='M',
        )

        response = self.client.post(reverse('applicant-address'), {
            'house_street': 'Main Street',
            'region': 'Region VIII',
        })

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertIsNone(profile.phone_number)
        self.assertIsNone(profile.barangay)

    def test_sensitive_phone_update_moves_approved_applicant_to_reverification_pending(self):
        peso_admin = User.objects.create_user(
            username='phone-update-peso',
            email='phone-update-peso@example.com',
            password='test-password',
            role='peso',
        )
        other_admin = User.objects.create_superuser(
            username='phone-update-other-admin',
            email='phone-update-other-admin@example.com',
            password='test-password',
        )
        profile = ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            status='approved',
        )

        response = self.client.post(reverse('applicant-address'), {
            'house_street': 'New Street',
            'barangay': 'Poblacion',
            'municipality': 'Carigara',
            'province': 'Leyte',
            'region': 'Region VIII',
            'zip_code': '6529',
            'phone_number': '09987654321',
            'mobile_number_secondary': '',
            'landline_number': '',
            'email_address': '',
        })

        self.assertRedirects(response, reverse('applicant-education'))
        profile.refresh_from_db()
        self.assertEqual(profile.status, 'reverify_pending')
        self.client.force_login(peso_admin)
        admin_verification = self.client.get(
            reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': profile.uuid},
            )
        )
        self.assertEqual(
            admin_verification.context['applicant'].phone_number,
            '09987654321',
        )
        change_log = ProfileChangeLog.objects.get(applicant=profile)
        self.assertEqual(
            change_log.changes['phone_number']['old'],
            '09123456789',
        )
        self.assertEqual(
            change_log.changes['phone_number']['new'],
            '09987654321',
        )
        self.assertIsNone(change_log.reviewed_at)
        notification = Notification.objects.get(
            recipient=peso_admin,
            notification_type='RESUBMISSION',
        )
        admin_notification = Notification.objects.get(
            recipient=other_admin,
            notification_type='RESUBMISSION',
        )
        self.assertEqual(
            notification.title,
            'Applicant Profile Updated - Re-Verification Required',
        )
        self.assertEqual(
            notification.target_url,
            reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': profile.uuid},
            ),
        )
        self.client.force_login(peso_admin)
        admin_header = self.client.get(
            reverse('AdminSide:notifications_header_api'),
        )
        self.assertTrue(any(
            item['id'] == str(notification.id)
            for item in admin_header.json()['notifications']
        ))
        self.client.force_login(other_admin)
        admin_role_header = self.client.get(
            reverse('AdminSide:notifications_header_api'),
        )
        self.assertTrue(any(
            item['id'] == str(admin_notification.id)
            for item in admin_role_header.json()['notifications']
        ))

    def test_sensitive_account_name_update_moves_approved_applicant_to_reverification_pending(self):
        profile = ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            status='approved',
        )

        response = self.client.post(
            reverse('settings'),
            {'full_name': 'Updated Applicant'},
        )

        self.assertRedirects(response, reverse('settings'))
        profile.refresh_from_db()
        self.assertEqual(profile.status, 'reverify_pending')

    def test_sensitive_applicant_update_while_pending_notifies_admins(self):
        peso_admin = User.objects.create_user(
            username='pending-applicant-update-peso',
            email='pending-applicant-update-peso@example.com',
            password='test-password',
            role='peso',
        )
        profile = ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            phone_number='09123456789',
            barangay='Poblacion',
            municipality='Carigara',
            province='Leyte',
            status='pending',
        )

        response = self.client.post(reverse('applicant-address'), {
            'house_street': 'New Street',
            'barangay': 'Poblacion',
            'municipality': 'Carigara',
            'province': 'Leyte',
            'region': 'Region VIII',
            'zip_code': '6529',
            'phone_number': '09987654321',
            'mobile_number_secondary': '',
            'landline_number': '',
            'email_address': '',
        })

        self.assertRedirects(response, reverse('applicant-education'))
        profile.refresh_from_db()
        self.assertEqual(profile.status, 'pending')
        notification = Notification.objects.get(
            recipient=peso_admin,
            notification_type='RESUBMISSION',
        )
        self.assertEqual(
            notification.target_url,
            reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': profile.uuid},
            ),
        )

    def test_sensitive_username_update_moves_approved_applicant_to_reverification_pending(self):
        profile = ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            status='approved',
        )

        response = self.client.post(
            reverse('update-username'),
            {'username': 'updated-applicant'},
        )

        self.assertRedirects(response, reverse('my_profile'))
        profile.refresh_from_db()
        self.assertEqual(profile.status, 'reverify_pending')

    def test_pending_applicant_is_not_job_matched_or_allowed_to_apply(self):
        ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            status='reverify_pending',
        )
        employer_user = User.objects.create_user(
            username='pending-applicant-employer',
            email='pending-applicant-employer@example.com',
            password='test-password',
            role='employer',
        )
        employer = EmployerProfile.objects.create(
            user=employer_user,
            business_name='Verified Employer',
            verification_status='verified',
        )
        job = Jobs.objects.create(
            employer=employer,
            job_title='Test Position',
            job_description='Test job description',
            place_of_work='Carigara',
            salary=10000,
            job_posting_expiry='2099-01-01',
        )

        with patch('ApplicantSide.views.get_job_collection') as get_job_collection:
            dashboard = self.client.get(reverse('applicant-dashboard'))

        self.assertEqual(dashboard.status_code, 200)
        self.assertFalse(dashboard.context['matching_jobs'].exists())
        self.assertContains(dashboard, 'Pending Re-Verification')
        get_job_collection.assert_not_called()

        response = self.client.post(
            reverse('apply-for-job', kwargs={'pk': job.pk})
        )

        self.assertRedirects(response, reverse('job_details', kwargs={'pk': job.pk}))
        self.assertFalse(AppliedJobs.objects.filter(applicant__user=self.applicant).exists())

    def test_unverified_employer_jobs_are_not_available_to_applicants(self):
        ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Test',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            status='approved',
        )
        employer_user = User.objects.create_user(
            username='pending-employer',
            email='pending-employer@example.com',
            password='test-password',
            role='employer',
        )
        employer = EmployerProfile.objects.create(
            user=employer_user,
            business_name='Pending Employer',
            verification_status='pending',
        )
        job = Jobs.objects.create(
            employer=employer,
            job_title='Unverified Employer Job',
            job_description='Test job description',
            place_of_work='Carigara',
            salary=10000,
            job_posting_expiry='2099-01-01',
        )

        response = self.client.get(reverse('job_list'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['jobs'].filter(pk=job.pk).exists())
        detail_response = self.client.get(
            reverse('job_details', kwargs={'pk': job.pk})
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_my_profile_keeps_registration_details_visible(self):
        ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Registered',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
            phone_number='09123456789',
        )

        response = self.client.get(reverse('my_profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registered')
        self.assertContains(response, 'Applicant')
        self.assertContains(response, 'January 1, 1995')
        self.assertContains(response, self.applicant.email)

        personal_info_response = self.client.get(reverse('personal_info'))

        self.assertEqual(personal_info_response.status_code, 200)
        self.assertContains(personal_info_response, 'value="Registered"')
        self.assertContains(personal_info_response, 'value="Applicant"')
        self.assertContains(personal_info_response, 'value="1995-01-01"')


class ApplicantProofDocumentFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='supporting-document-applicant',
            email='supporting-document-applicant@example.com',
            password='test-password',
            role='applicant',
        )
        self.profile = ApplicantProfile.objects.create(
            user=self.user,
            first_name='Document',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
        )

    def make_education_form(self, uploaded_file=None):
        return ApplicantEducationForm(
            data={
                'school_status_yes': 'on',
                'highest_educational_attainment': 'college_grad',
                'school_university': 'Test University',
            },
            files={'education_proof_document': uploaded_file} if uploaded_file else {},
            instance=self.profile,
        )

    def test_education_change_accepts_a_valid_category_specific_pdf(self):
        self.profile.status = 'approved'
        uploaded_file = SimpleUploadedFile(
            'diploma.pdf',
            b'%PDF-1.7\nvalid test document',
            content_type='application/pdf',
        )
        form = self.make_education_form(uploaded_file)

        self.assertTrue(form.is_valid(), form.errors)

    def test_education_change_requires_a_valid_proof_upload_when_approved(self):
        self.profile.status = 'approved'
        missing_file_form = self.make_education_form()
        invalid_pdf_form = self.make_education_form(
            SimpleUploadedFile('proof.pdf', b'not a pdf'),
        )

        self.assertFalse(missing_file_form.is_valid())
        self.assertTrue(missing_file_form.non_field_errors())
        self.assertFalse(invalid_pdf_form.is_valid())
        self.assertIn('education_proof_document', invalid_pdf_form.errors)

    def test_final_document_form_has_no_generic_supporting_document_fields(self):
        form = ApplicantDocumentsForm(instance=self.profile)

        self.assertNotIn('supporting_doc', form.fields)
        self.assertNotIn('supporting_doc_type', form.fields)

    def test_final_document_page_does_not_render_generic_support_upload(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('applicant-documents'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload Applicant ID Picture')
        self.assertNotContains(response, 'Supporting Document')
        self.assertNotContains(response, 'supporting_doc')

class ApplicantNotificationTests(TestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            username='notification-applicant',
            email='notification-applicant@example.com',
            password='test-password',
            role='applicant',
        )
        self.profile = ApplicantProfile.objects.create(
            user=self.applicant,
            first_name='Notification',
            last_name='Applicant',
            date_of_birth='1995-01-01',
            sex='F',
        )

    def create_notification(self, notification_type, **kwargs):
        return Notification.objects.create(
            recipient=self.applicant,
            title='Test notification',
            message='Test notification message',
            notification_type=notification_type,
            **kwargs,
        )

    def test_applicant_inbox_and_header_only_include_supported_types(self):
        self.create_notification('APPLICATION_STATUS')
        self.create_notification(
            'VERIFICATION_REJECTED',
            reason='Please upload a clearer ID.',
        )
        self.create_notification('VERIFICATION_APPROVED')
        self.create_notification('APPEAL_REVERIFICATION')
        self.client.force_login(self.applicant)

        inbox_response = self.client.get(reverse('applicant-notifications'))
        header_response = self.client.get(reverse('applicant-notifications-header'))

        self.assertEqual(inbox_response.status_code, 200)
        self.assertEqual(len(inbox_response.context['notifications']), 3)
        self.assertContains(inbox_response, 'Please upload a clearer ID.')
        self.assertEqual(header_response.status_code, 200)
        self.assertEqual(header_response.json()['total_count'], 3)
        self.assertEqual(
            {item['notification_type'] for item in header_response.json()['notifications']},
            {'APPLICATION_STATUS', 'VERIFICATION_APPROVED', 'VERIFICATION_REJECTED'},
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_admin_approval_notification_is_visible_to_applicant(self):
        admin = User.objects.create_superuser(
            username='applicant-approval-notification-admin',
            email='applicant-approval-notification-admin@example.com',
            password='test-password',
        )
        self.profile.status = 'reverify_pending'
        self.profile.education_proof_document = (
            'applicant_docs/education_proofs/current-proof.pdf'
        )
        self.profile.save()
        ProfileChangeLog.objects.create(
            applicant=self.profile,
            changed_by=self.applicant,
            changes={
                'school_university': {
                    'label': 'School University',
                    'old': 'Old School',
                    'new': 'New School',
                },
            },
        )
        self.profile.education_proof_uploaded_at = timezone.now()
        self.profile.save(update_fields=['education_proof_uploaded_at'])
        admin_client = self.client_class()
        admin_client.force_login(admin)

        response = admin_client.post(
            reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': self.profile.uuid},
            ),
            {'action': 'verify'},
        )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(
            recipient=self.applicant,
            notification_type='VERIFICATION_APPROVED',
        )
        self.assertEqual(notification.sender, admin)
        self.assertEqual(notification.title, 'Applicant Account Verified')
        self.assertEqual(notification.target_url, reverse('my_profile'))

        self.client.force_login(self.applicant)
        header_response = self.client.get(reverse('applicant-notifications-header'))
        self.assertEqual(header_response.status_code, 200)
        self.assertEqual(header_response.json()['unread_count'], 1)
        self.assertEqual(
            header_response.json()['notifications'][0]['notification_type'],
            'VERIFICATION_APPROVED',
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_registry_approval_notifies_applicant(self):
        admin = User.objects.create_superuser(
            username='applicant-registry-notification-admin',
            email='applicant-registry-notification-admin@example.com',
            password='test-password',
        )
        admin_client = Client()
        admin_client.force_login(admin)

        response = admin_client.post(
            reverse('AdminSide:applicants_list'),
            {
                'applicant_uuid': str(self.profile.uuid),
                'status': 'approved',
            },
        )

        self.assertRedirects(response, reverse('AdminSide:applicants_list'))
        notification = Notification.objects.get(
            recipient=self.applicant,
            notification_type='VERIFICATION_APPROVED',
        )
        self.assertEqual(notification.sender, admin)

    def test_reading_notification_reduces_unread_count(self):
        notification = self.create_notification(
            'APPLICATION_STATUS',
            target_url=reverse('applied_jobs'),
        )
        self.client.force_login(self.applicant)

        response = self.client.post(
            reverse('applicant-notification-read', args=[notification.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 0)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        response = self.client.post(
            reverse('applicant-notification-read', args=[notification.id]),
        )
        self.assertRedirects(response, reverse('applied_jobs'))

    def test_admin_rejection_sends_applicant_a_reason_notification(self):
        admin = User.objects.create_superuser(
            username='applicant-rejection-admin',
            email='applicant-rejection-admin@example.com',
            password='test-password',
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': self.profile.uuid},
            ),
            {
                'action': 'reject',
                'reason': 'The uploaded identification document is unreadable.',
            },
        )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(
            recipient=self.applicant,
            notification_type='VERIFICATION_REJECTED',
        )
        self.assertEqual(
            notification.reason,
            'The uploaded identification document is unreadable.',
        )
        self.assertEqual(notification.sender, admin)
        self.assertEqual(notification.target_url, reverse('my_profile'))

    def test_applicant_reverification_appeal_notifies_admin_in_app(self):
        admin = User.objects.create_superuser(
            username='applicant-appeal-admin',
            email='applicant-appeal-admin@example.com',
            password='test-password',
        )
        self.profile.status = 'rejected'
        self.profile.save(update_fields=['status'])
        self.client.force_login(self.applicant)

        response = self.client.post(
            reverse('applicant-reverification-appeal'),
            {'reason': 'I uploaded the corrected verification documents.'},
        )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(
            recipient=admin,
            notification_type='APPEAL_REVERIFICATION',
        )
        self.assertEqual(notification.sender, self.applicant)
        self.assertEqual(
            notification.reason,
            'I uploaded the corrected verification documents.',
        )

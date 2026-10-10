from django.test import Client, TestCase, override_settings
from django.urls import reverse

from AdminSide.models import ApplicantProfile, Notification, User


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

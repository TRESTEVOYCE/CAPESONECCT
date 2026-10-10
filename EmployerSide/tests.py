from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from AdminSide.models import AppliedJobs, ApplicantProfile, EmployerProfile, Jobs, Notification, User
from AdminSide.signals import notify_admin_on_employer_registration
from AdminSide.utils import notify_admins


class EmployerNotificationTests(TestCase):
    def setUp(self):
        self.employer_user = User.objects.create_user(
            username='notification-employer',
            email='notification-employer@example.com',
            password='test-password',
            role='employer',
        )
        self.employer = EmployerProfile.objects.create(
            user=self.employer_user,
            business_name='Notification Employer Ltd',
        )
        self.applicant_user = User.objects.create_user(
            username='notification-applicant',
            email='notification-applicant@example.com',
            password='test-password',
            role='applicant',
        )
        self.applicant = ApplicantProfile.objects.create(
            user=self.applicant_user,
            first_name='Test',
            last_name='Applicant',
            date_of_birth=date(1995, 1, 1),
            sex='F',
        )

    def create_notification(self, notification_type, **kwargs):
        return Notification.objects.create(
            recipient=self.employer_user,
            title='Test notification',
            message='Test message',
            notification_type=notification_type,
            **kwargs,
        )

    def test_applying_to_employers_job_creates_notification(self):
        job = Jobs.objects.create(
            employer=self.employer,
            job_title='Test Job',
            job_description='A test role',
            place_of_work='Carigara',
            salary=10000,
            job_posting_expiry=timezone.localdate() + timedelta(days=30),
        )

        application = AppliedJobs.objects.create(
            employer=self.employer,
            applicant=self.applicant,
            applied_job=job,
        )

        notification = Notification.objects.get(recipient=self.employer_user)
        self.assertEqual(notification.notification_type, 'NEW_APPLICANT')
        self.assertIn('Test Applicant', notification.message)
        self.assertIn('/employer/applicants/', notification.target_url)

    def test_admin_registration_notifications_use_admin_side_routes(self):
        admin = User.objects.create_superuser(
            username='notification-route-admin',
            email='notification-route-admin@example.com',
            password='test-password',
        )

        notify_admin_on_employer_registration(
            sender=EmployerProfile,
            instance=self.employer,
            created=True,
        )
        employer_notification = Notification.objects.get(
            recipient=admin,
            notification_type='NEW_EMPLOYER',
        )
        self.assertEqual(
            employer_notification.target_url,
            reverse('AdminSide:employer_verification', kwargs={'uuid': self.employer.uuid}),
        )

        job = Jobs.objects.create(
            employer=self.employer,
            job_title='Test Job',
            job_description='A test role',
            place_of_work='Carigara',
            salary=10000,
            job_posting_expiry=timezone.localdate() + timedelta(days=30),
        )
        job_notification = Notification.objects.get(
            recipient=admin,
            notification_type='NEW_JOB_POST',
            target_url=reverse('AdminSide:job_detail', kwargs={'job_uuid': job.uuid}),
        )
        self.assertEqual(
            job_notification.target_url,
            reverse('AdminSide:job_detail', kwargs={'job_uuid': job.uuid}),
        )

    def test_legacy_employer_notification_url_redirects_to_verification_page(self):
        response = self.client.get(f'/admin/employers/{self.employer.uuid}/')

        self.assertRedirects(
            response,
            reverse('AdminSide:employer_verification', kwargs={'uuid': self.employer.uuid}),
            fetch_redirect_response=False,
        )

    def test_legacy_home_url_redirects_to_employer_dashboard(self):
        response = self.client.get('/home/')

        self.assertRedirects(
            response,
            reverse('employer-home'),
            fetch_redirect_response=False,
        )

    def test_header_returns_only_latest_five_supported_notifications(self):
        for _ in range(6):
            self.create_notification('NEW_APPLICANT')
        self.create_notification('VERIFICATION_REJECTED', reason='Missing registration document')
        self.create_notification('APPLICATION_STATUS')
        self.client.force_login(self.employer_user)

        response = self.client.get(reverse('employer-notifications-header'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_count'], 7)
        self.assertEqual(len(data['notifications']), 5)
        self.assertTrue(all(
            notification['notification_type'] in {'NEW_APPLICANT', 'VERIFICATION_REJECTED'}
            for notification in data['notifications']
        ))

    def test_mark_all_read_keeps_notifications_and_does_not_affect_other_types(self):
        self.create_notification('NEW_APPLICANT')
        self.create_notification('VERIFICATION_REJECTED', reason='Missing document')
        unrelated_notification = self.create_notification('APPLICATION_STATUS')
        self.client.force_login(self.employer_user)

        response = self.client.post(
            reverse('employer-notifications-read-all'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 0)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.employer_user,
                notification_type__in=('NEW_APPLICANT', 'VERIFICATION_REJECTED'),
            ).count(),
            2,
        )
        unrelated_notification.refresh_from_db()
        self.assertFalse(unrelated_notification.is_read)

    def test_inbox_displays_only_the_employer_notification_types(self):
        self.create_notification('NEW_APPLICANT')
        self.create_notification('VERIFICATION_REJECTED', reason='Missing document')
        self.create_notification('APPLICATION_STATUS')
        self.client.force_login(self.employer_user)

        response = self.client.get(reverse('employer-notifications'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 2)
        self.assertContains(response, 'Missing document')

    def test_opening_employer_notification_marks_it_read_and_updates_count(self):
        notification = self.create_notification(
            'VERIFICATION_APPROVED',
            target_url=reverse('company_profile_view'),
        )
        self.client.force_login(self.employer_user)

        header = self.client.get(reverse('employer-notifications-header'))
        read_url = header.json()['notifications'][0]['read_url']
        response = self.client.post(
            read_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 0)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        response = self.client.post(read_url)
        self.assertRedirects(response, reverse('company_profile_view'))

    def test_opening_admin_notification_marks_it_read_and_updates_count(self):
        admin = User.objects.create_superuser(
            username='notification-read-admin',
            email='notification-read-admin@example.com',
            password='test-password',
        )
        notification = Notification.objects.create(
            recipient=admin,
            title='Appeal for Reverification',
            message='Please review this appeal.',
            notification_type='APPEAL_REVERIFICATION',
            target_url=reverse(
                'AdminSide:employer_verification',
                kwargs={'uuid': self.employer.uuid},
            ),
        )
        self.client.force_login(admin)

        header = self.client.get(reverse('AdminSide:notifications_header_api'))
        read_url = header.json()['notifications'][0]['read_url']
        response = self.client.post(
            read_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 0)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        response = self.client.post(read_url)
        self.assertRedirects(response, notification.target_url)

    def test_admin_rejection_sends_employer_notification_with_reason(self):
        admin = User.objects.create_superuser(
            username='notification-admin',
            email='notification-admin@example.com',
            password='test-password',
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('AdminSide:employer_verification', kwargs={'uuid': self.employer.uuid}),
            {'action': 'reject', 'remarks': 'Business permit is expired.'},
        )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(recipient=self.employer_user)
        self.assertEqual(notification.notification_type, 'VERIFICATION_REJECTED')
        self.assertEqual(notification.reason, 'Business permit is expired.')
        self.assertEqual(notification.target_url, reverse('company_profile_view'))
        self.assertEqual(
            Notification.objects.filter(notification_type='VERIFICATION_REJECTED').count(),
            1,
        )
        self.assertEqual(notification.recipient, self.employer_user)

        self.client.force_login(admin)
        admin_header = self.client.get(reverse('AdminSide:notifications_header_api'))
        self.assertFalse(any(
            item['notification_type'] == 'VERIFICATION_REJECTED'
            for item in admin_header.json()['notifications']
        ))

        self.client.force_login(self.employer_user)
        employer_header = self.client.get(reverse('employer-notifications-header'))
        self.assertTrue(any(
            item['notification_type'] == 'VERIFICATION_REJECTED'
            for item in employer_header.json()['notifications']
        ))
        notification_response = self.client.get(notification.target_url)
        self.assertEqual(notification_response.status_code, 200)

    def test_admin_approval_sends_employer_notification_once(self):
        admin = User.objects.create_superuser(
            username='notification-approval-admin',
            email='notification-approval-admin@example.com',
            password='test-password',
        )
        self.client.force_login(admin)
        approval_url = reverse(
            'AdminSide:employer_verification',
            kwargs={'uuid': self.employer.uuid},
        )

        response = self.client.post(approval_url, {'action': 'approve'})

        self.assertEqual(response.status_code, 302)
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.verification_status, 'verified')
        notification = Notification.objects.get(
            recipient=self.employer_user,
            notification_type='VERIFICATION_APPROVED',
        )
        self.assertEqual(notification.title, 'Employer Account Verified')
        self.assertEqual(notification.target_url, reverse('company_profile_view'))

        self.client.post(approval_url, {'action': 'approve'})
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.employer_user,
                notification_type='VERIFICATION_APPROVED',
            ).count(),
            1,
        )

        self.client.force_login(self.employer_user)
        employer_header = self.client.get(reverse('employer-notifications-header'))
        self.assertTrue(any(
            item['notification_type'] == 'VERIFICATION_APPROVED'
            for item in employer_header.json()['notifications']
        ))
        employer_inbox = self.client.get(reverse('employer-notifications'))
        self.assertContains(employer_inbox, 'Employer Account Verified')

    def test_admin_cannot_reject_without_a_reason(self):
        admin = User.objects.create_superuser(
            username='notification-admin-no-reason',
            email='notification-admin-no-reason@example.com',
            password='test-password',
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('AdminSide:employer_verification', kwargs={'uuid': self.employer.uuid}),
            {'action': 'reject', 'remarks': '   '},
        )

        self.assertEqual(response.status_code, 302)
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.verification_status, 'pending')
        self.assertFalse(Notification.objects.filter(recipient=self.employer_user).exists())

    def test_reverification_appeal_is_delivered_to_admin_side_not_employer_inbox(self):
        admin = User.objects.create_superuser(
            username='notification-appeal-admin',
            email='notification-appeal-admin@example.com',
            password='test-password',
        )
        self.assertEqual(admin.role, 'admin')
        self.employer.verification_status = 'rejected'
        self.employer.save(update_fields=['verification_status'])
        self.client.force_login(self.employer_user)

        response = self.client.post(
            reverse('employer-reverification-appeal'),
            {'reason': 'Updated verification documents are ready for review.'},
        )

        self.assertRedirects(response, reverse('employer-home'))
        appeal = Notification.objects.get(
            recipient=admin,
            notification_type='APPEAL_REVERIFICATION',
        )
        self.assertEqual(
            appeal.target_url,
            reverse('AdminSide:employer_verification', kwargs={'uuid': self.employer.uuid}),
        )
        self.assertEqual(appeal.reason, 'Updated verification documents are ready for review.')
        self.assertFalse(Notification.objects.filter(
            recipient=self.employer_user,
            notification_type='APPEAL_REVERIFICATION',
        ).exists())

        self.client.force_login(admin)
        admin_header = self.client.get(reverse('AdminSide:notifications_header_api'))
        self.assertEqual(admin_header.status_code, 200)
        self.assertTrue(any(
            item['notification_type'] == 'APPEAL_REVERIFICATION'
            for item in admin_header.json()['notifications']
        ))
        admin_inbox = self.client.get(reverse('AdminSide:notifications_list'))
        self.assertContains(admin_inbox, 'Appeal for Reverification')

        self.client.force_login(self.employer_user)
        employer_header = self.client.get(reverse('employer-notifications-header'))
        self.assertEqual(employer_header.status_code, 200)
        self.assertTrue(all(
            item['notification_type'] in {'NEW_APPLICANT', 'VERIFICATION_REJECTED'}
            for item in employer_header.json()['notifications']
        ))
        self.assertFalse(Notification.objects.filter(
            recipient=self.employer_user,
            notification_type='APPEAL_REVERIFICATION',
        ).exists())

    def test_admin_notifications_are_not_sent_to_employer_superusers(self):
        self.employer_user.is_superuser = True
        self.employer_user.save(update_fields=['is_superuser'])

        notify_admins(
            title='Appeal for Reverification',
            message='Test appeal',
            notification_type='APPEAL_REVERIFICATION',
        )

        self.assertFalse(Notification.objects.filter(
            recipient=self.employer_user,
            notification_type='APPEAL_REVERIFICATION',
        ).exists())

# Create your tests here.

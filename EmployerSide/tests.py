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

    def test_sensitive_business_profile_update_moves_verified_employer_to_reverification_pending(self):
        self.employer.business_name = 'Notification Employer Ltd'
        self.employer.contact_person = 'Test Contact'
        self.employer.mobile_number = '09123456789'
        self.employer.verification_status = 'verified'
        self.employer.save()
        self.client.force_login(self.employer_user)

        response = self.client.post(
            reverse('employer-profile-create'),
            {
                'business_name': self.employer.business_name,
                'trade_name': '',
                'acronym': '',
                'office_type': 'main',
                'tin_number': '',
                'employer_type': 'direct_hire',
                'total_workforce': 'micro',
                'line_of_business': '',
                'street_address': '',
                'barangay': 'Poblacion',
                'municipality': 'Carigara',
                'province': 'Leyte',
                'owner_name': '',
                'designation': '',
                'contact_person': self.employer.contact_person,
                'contact_position': '',
                'telephone_number': '',
                'mobile_number': '09987654321',
                'email': '',
                'public_doc_type': '',
            },
        )

        self.assertRedirects(response, reverse('employer-home'))
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.mobile_number, '09987654321')
        self.assertEqual(self.employer.verification_status, 'reverify_pending')
        employer_dashboard = self.client.get(reverse('employer-home'))
        self.assertContains(employer_dashboard, 'Pending Re-Verification')
        job_creation_response = self.client.get(reverse('job_create'))
        self.assertEqual(job_creation_response.status_code, 403)

    def test_pending_applicant_is_hidden_from_employer_candidate_list(self):
        self.employer.verification_status = 'verified'
        self.employer.save(update_fields=['verification_status'])
        self.applicant.status = 'approved'
        self.applicant.save(update_fields=['status'])
        job = Jobs.objects.create(
            employer=self.employer,
            job_title='Candidate List Job',
            job_description='Test job description',
            place_of_work='Carigara',
            salary=10000,
            job_posting_expiry='2099-01-01',
        )
        AppliedJobs.objects.create(
            employer=self.employer,
            applicant=self.applicant,
            applied_job=job,
        )
        self.client.force_login(self.employer_user)

        approved_response = self.client.get(reverse('applicants-list'))
        self.assertEqual(len(approved_response.context['object_list']), 1)

        self.applicant.status = 'pending'
        self.applicant.save(update_fields=['status'])
        pending_response = self.client.get(reverse('applicants-list'))

        self.assertEqual(len(pending_response.context['object_list']), 0)
        detail_response = self.client.get(
            reverse('applicant-detail', kwargs={'pk': job.applied_applicants.get().pk})
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_employer_application_status_change_notifies_applicant_once(self):
        job = Jobs.objects.create(
            employer=self.employer,
            job_title='Status Test Job',
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

        application.status = 'for interview'
        application.save(update_fields=['status'])

        notification = Notification.objects.get(
            recipient=self.applicant_user,
            notification_type='APPLICATION_STATUS',
        )
        self.assertEqual(notification.sender, self.employer_user)
        self.assertIn('For Interview', notification.message)
        self.assertEqual(notification.target_url, reverse('applied_jobs'))

        application.is_hired = True
        application.save(update_fields=['is_hired'])
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.applicant_user,
                notification_type='APPLICATION_STATUS',
            ).count(),
            1,
        )

        self.client.force_login(self.applicant_user)
        header = self.client.get(reverse('applicant-notifications-header'))
        self.assertTrue(any(
            item['notification_type'] == 'APPLICATION_STATUS'
            for item in header.json()['notifications']
        ))

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

    def test_admin_notification_center_hides_employer_account_approval(self):
        admin = User.objects.create_superuser(
            username='notification-admin-approval-inbox',
            email='notification-admin-approval-inbox@example.com',
            password='test-password',
        )
        approval = Notification.objects.create(
            recipient=admin,
            title='Employer Account Verified',
            message='Your employer account has been verified.',
            notification_type='VERIFICATION_APPROVED',
        )
        self.client.force_login(admin)

        inbox = self.client.get(reverse('AdminSide:notifications_list'))
        header = self.client.get(reverse('AdminSide:notifications_header_api'))

        self.assertEqual(inbox.status_code, 200)
        self.assertNotContains(inbox, 'Employer Account Verified')
        self.assertEqual(header.status_code, 200)
        self.assertEqual(header.json()['total_count'], 0)
        self.assertEqual(header.json()['unread_count'], 0)
        self.assertEqual(header.json()['notifications'], [])
        self.assertTrue(Notification.objects.filter(pk=approval.pk).exists())

    def test_approval_notifies_preverified_employer_when_notice_is_missing(self):
        admin = User.objects.create_superuser(
            username='notification-preverified-admin',
            email='notification-preverified-admin@example.com',
            password='test-password',
        )
        self.employer.verification_status = 'verified'
        self.employer.save(update_fields=['verification_status'])
        self.client.force_login(admin)

        response = self.client.post(
            reverse(
                'AdminSide:employer_verification',
                kwargs={'uuid': self.employer.uuid},
            ),
            {'action': 'approve'},
        )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(
            recipient=self.employer_user,
            notification_type='VERIFICATION_APPROVED',
        )
        self.assertEqual(notification.title, 'Employer Account Verified')
        self.assertFalse(Notification.objects.filter(
            recipient=admin,
            notification_type='VERIFICATION_APPROVED',
        ).exists())

    def test_verified_employer_sidebar_shows_approved_status(self):
        self.employer.verification_status = 'verified'
        self.employer.save(update_fields=['verification_status'])
        self.client.force_login(self.employer_user)

        response = self.client.get(reverse('employer-notifications'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Account Approved')
        self.assertNotContains(response, 'Account Pending')

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

    def test_reverification_appeal_is_sent_to_mswd_admin_role(self):
        mswd_admin = User.objects.create_user(
            username='notification-mswd-admin',
            email='notification-mswd-admin@example.com',
            password='test-password',
            role='mswdo',
        )

        notifications = notify_admins(
            title='Appeal for Reverification',
            message='Test appeal',
            notification_type='APPEAL_REVERIFICATION',
        )

        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].recipient, mswd_admin)
        self.assertEqual(notifications[0].notification_type, 'APPEAL_REVERIFICATION')

    def test_employer_appeal_reaches_peso_admin_inbox(self):
        peso_admin = User.objects.create_user(
            username='notification-peso-admin',
            email='notification-peso-admin@example.com',
            password='test-password',
            role='peso',
        )
        self.employer.verification_status = 'rejected'
        self.employer.save(update_fields=['verification_status'])
        self.client.force_login(self.employer_user)

        response = self.client.post(
            reverse('employer-reverification-appeal'),
            {'reason': 'Updated verification documents are ready for review.'},
        )

        self.assertRedirects(response, reverse('employer-home'))
        appeal = Notification.objects.get(
            recipient=peso_admin,
            notification_type='APPEAL_REVERIFICATION',
        )
        self.assertEqual(appeal.reason, 'Updated verification documents are ready for review.')

        self.client.force_login(peso_admin)
        header = self.client.get(reverse('AdminSide:notifications_header_api'))
        inbox = self.client.get(reverse('AdminSide:notifications_list'))

        self.assertTrue(any(
            item['id'] == str(appeal.pk)
            for item in header.json()['notifications']
        ))
        self.assertContains(inbox, 'Appeal for Reverification')

    def test_employer_appeal_reaches_uppercase_peso_admin_role(self):
        peso_admin = User.objects.create_user(
            username='notification-uppercase-peso-admin',
            email='notification-uppercase-peso-admin@example.com',
            password='test-password',
            role='PESO',
        )
        self.employer.verification_status = 'rejected'
        self.employer.save(update_fields=['verification_status'])
        self.client.force_login(self.employer_user)

        self.client.post(
            reverse('employer-reverification-appeal'),
            {'reason': 'Updated verification documents are ready for review.'},
        )

        appeal = Notification.objects.get(
            recipient=peso_admin,
            notification_type='APPEAL_REVERIFICATION',
        )
        self.client.force_login(peso_admin)
        header = self.client.get(reverse('AdminSide:notifications_header_api'))
        inbox = self.client.get(reverse('AdminSide:notifications_list'))
        header_data = header.json()

        self.assertEqual(header.status_code, 200)
        self.assertEqual(header_data['unread_count'], 1)
        self.assertEqual(header_data['total_count'], 1)
        self.assertEqual(len(header_data['notifications']), 1)
        self.assertEqual(header_data['notifications'][0]['id'], str(appeal.pk))
        self.assertEqual(header_data['notifications'][0]['title'], 'Appeal for Reverification')
        self.assertEqual(
            header_data['notifications'][0]['notification_type'],
            'APPEAL_REVERIFICATION',
        )
        self.assertEqual(inbox.status_code, 200)
        self.assertContains(inbox, 'Appeal for Reverification')
        self.assertContains(inbox, 'id="notifBellBtn"')
        self.assertContains(
            inbox,
            reverse('AdminSide:notifications_header_api'),
        )
        self.assertEqual(
            inbox.context['notifications'][0],
            appeal,
        )

# Create your tests here.

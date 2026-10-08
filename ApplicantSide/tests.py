from django.test import Client, TestCase
from django.urls import reverse

from AdminSide.models import ApplicantProfile, User


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

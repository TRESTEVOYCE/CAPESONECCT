from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from AdminSide.models import ApplicantProfile, AppliedJobs, EmployerProfile, Jobs


DUMMY_APPLICANTS = [
    {
        'username': 'dummy_applicant_1',
        'email': 'applicant1@example.com',
        'first_name': 'Juan',
        'middle_name': 'D',
        'last_name': 'Cruz',
        'date_of_birth': '1998-01-15',
        'age': 27,
        'civil_status': 'single',
        'sex': 'Male',
        'contact_number': '09171234567',
        'barangay': 'Barangay 123',
        'municipality': 'Manila',
        'province': 'Metro Manila',
        'zip_code': '1000',
        'region': 'NCR',
        'phone_number': '09171234567',
        'resume': 'resumes/dummy_resume_1.pdf',
        'curriculum_vitae': 'curriculum_vitae/dummy_cv_1.pdf',
        'applicant_id_picture': 'applicant_id_pictures/dummy_id_1.jpg',
        'education_level': 'college',
        'status': 'approved',
    },
    {
        'username': 'dummy_applicant_2',
        'email': 'applicant2@example.com',
        'first_name': 'Maria',
        'middle_name': 'L',
        'last_name': 'Santos',
        'date_of_birth': '1996-06-22',
        'age': 29,
        'civil_status': 'married',
        'sex': 'Female',
        'contact_number': '09181234567',
        'barangay': 'Barangay 456',
        'municipality': 'Quezon City',
        'province': 'Metro Manila',
        'zip_code': '1100',
        'region': 'NCR',
        'phone_number': '09181234567',
        'resume': 'resumes/dummy_resume_2.pdf',
        'curriculum_vitae': 'curriculum_vitae/dummy_cv_2.pdf',
        'applicant_id_picture': 'applicant_id_pictures/dummy_id_2.jpg',
        'education_level': 'university',
        'status': 'pending',
    },
]

DUMMY_EMPLOYERS = [
    {
        'username': 'dummy_employer_1',
        'email': 'employer1@example.com',
        'company_name': 'MetroTech Solutions',
        'company_type': 'private',
        'business_permit': 'business_permits/permit_1.pdf',
        'phone_number': '09192223344',
        'company_address': '123 Main Street, Makati',
        'contact_person': 'Rina Dela Cruz',
        'verification_status': 'verified',
    },
    {
        'username': 'dummy_employer_2',
        'email': 'employer2@example.com',
        'company_name': 'City Health Services',
        'company_type': 'government',
        'business_permit': 'business_permits/permit_2.pdf',
        'phone_number': '09223334455',
        'company_address': '99 Rizal Avenue, Manila',
        'contact_person': 'Paul Mendoza',
        'verification_status': 'pending',
    },
]

DUMMY_JOBS = [
    {
        'job_title': 'Software Developer',
        'job_description': 'Develop and maintain internal web applications.',
        'job_requirements': 'Experience with Python and Django.',
        'job_location': 'Manila',
        'job_type': 'full_time',
        'vacancy': 2,
        'salary': '45000.00',
    },
    {
        'job_title': 'Customer Service Representative',
        'job_description': 'Handle inbound support requests and customer concerns.',
        'job_requirements': 'Good communication and customer handling skills.',
        'job_location': 'Cebu',
        'job_type': 'part_time',
        'vacancy': 5,
        'salary': '22000.00',
    },
]


class Command(BaseCommand):
    help = 'Create one dummy applicant and one dummy employer account for testing'

    def handle(self, *args, **options):
        User = get_user_model()

        applicant_profiles = []
        employer_profiles = []

        for applicant_data in DUMMY_APPLICANTS:
            user, created = User.objects.get_or_create(
                username=applicant_data['username'],
                defaults={
                    'email': applicant_data['email'],
                    'password': 'Test12345!',
                    'role': 'applicant',
                },
            )
            if created:
                user.set_password('Test12345!')
                user.save()

            profile, profile_created = ApplicantProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': applicant_data['first_name'],
                    'middle_name': applicant_data['middle_name'],
                    'last_name': applicant_data['last_name'],
                    'date_of_birth': applicant_data['date_of_birth'],
                    'age': applicant_data['age'],
                    'civil_status': applicant_data['civil_status'],
                    'sex': applicant_data['sex'],
                    'contact_number': applicant_data['contact_number'],
                    'barangay': applicant_data['barangay'],
                    'municipality': applicant_data['municipality'],
                    'province': applicant_data['province'],
                    'zip_code': applicant_data['zip_code'],
                    'region': applicant_data['region'],
                    'phone_number': applicant_data['phone_number'],
                    'resume': applicant_data['resume'],
                    'curriculum_vitae': applicant_data['curriculum_vitae'],
                    'applicant_id_picture': applicant_data['applicant_id_picture'],
                    'education_level': applicant_data['education_level'],
                    'status': applicant_data['status'],
                },
            )
            applicant_profiles.append(profile)

        for employer_data in DUMMY_EMPLOYERS:
            user, created = User.objects.get_or_create(
                username=employer_data['username'],
                defaults={
                    'email': employer_data['email'],
                    'password': 'Test12345!',
                    'role': 'employer',
                },
            )
            if created:
                user.set_password('Test12345!')
                user.save()

            profile, profile_created = EmployerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': employer_data['company_name'],
                    'company_type': employer_data['company_type'],
                    'business_permit': employer_data['business_permit'],
                    'email': employer_data['email'],
                    'phone_number': employer_data['phone_number'],
                    'company_address': employer_data['company_address'],
                    'contact_person': employer_data['contact_person'],
                    'verification_status': employer_data['verification_status'],
                },
            )
            employer_profiles.append(profile)

        for employer_profile in employer_profiles:
            for job_data in DUMMY_JOBS:
                job, created = Jobs.objects.get_or_create(
                    job_title=job_data['job_title'],
                    employer=employer_profile,
                    defaults={
                        'job_description': job_data['job_description'],
                        'job_requirements': job_data['job_requirements'],
                        'job_location': job_data['job_location'],
                        'job_type': job_data['job_type'],
                        'vacancy': job_data['vacancy'],
                        'salary': job_data['salary'],
                        'job_posting_expiry': timezone.make_aware(datetime(2030, 12, 31, 23, 59, 59)),
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created job posting: {job.job_title} for {employer_profile.company_name}'))

                applicant_profile = applicant_profiles[0]
                AppliedJobs.objects.get_or_create(
                    applicant=applicant_profile,
                    applied_job=job,
                    defaults={'status': 'pending'},
                )

        self.stdout.write(self.style.SUCCESS('Seeded dashboard test data successfully.'))

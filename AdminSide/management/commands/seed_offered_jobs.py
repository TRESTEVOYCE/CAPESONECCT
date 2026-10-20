import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker

from AdminSide.models import (
    EmployerProfile,
    Jobs,
    ApplicantProfile,
    OfferedJobs,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds test data for OfferedJobs linking Applicants, Job Vacancies, and Employers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=15,
            help="Number of referrals/offered jobs to generate.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        fake = Faker("en_PH")

        self.stdout.write(self.style.WARNING("Starting OfferedJobs (Referrals) seeding process..."))

        # -------------------------------------------------------------
        # 1. VERIFY OR CREATE DEPENDENT DATA
        # -------------------------------------------------------------
        employers = list(EmployerProfile.objects.all())
        if not employers:
            self.stdout.write(self.style.ERROR("No employers found. Generating a default employer..."))
            user, _ = User.objects.get_or_create(
                username="default_emp",
                defaults={"email": "hr@leytebuilders.ph", "role": "employer"}
            )
            emp = EmployerProfile.objects.create(
                user=user,
                business_name="Leyte Builders & Supply Corp.",
                trade_name="Leyte Builders",
                office_type="main",
                employer_type="direct_hire",
                barangay="Jugaban",
                municipality="Carigara",
                province="Leyte",
                contact_person="Maria Santos",
                mobile_number="09171234567",
                email="hr@leytebuilders.ph",
                verification_status="verified"
            )
            employers.append(emp)

        jobs = list(Jobs.objects.all())
        if not jobs:
            self.stdout.write(self.style.ERROR("No job vacancies found. Generating sample jobs..."))
            job_titles = ["Administrative Assistant", "IT Support Specialist", "Store Cashier", "Project Supervisor"]
            for title in job_titles:
                j = Jobs.objects.create(
                    employer=random.choice(employers),
                    job_title=title,
                    job_description="Responsible for daily operations and tasks.",
                    place_of_work="Carigara, Leyte",
                    salary=15000.00,
                    vacancy=3,
                    job_posting_expiry=timezone.now().date() + timedelta(days=30),
                    status="Active"
                )
                jobs.append(j)

        applicants = list(ApplicantProfile.objects.all())
        if not applicants:
            self.stdout.write(self.style.ERROR("No applicants found. Generating sample applicants..."))
            for i in range(10):
                f_name = fake.first_name()
                l_name = fake.last_name()
                user = User.objects.create(
                    username=f"applicant_ref_{i+1}",
                    email=f"{f_name.lower()}.{l_name.lower()}@gmail.com",
                    role="applicant",
                    first_name=f_name,
                    last_name=l_name
                )
                app = ApplicantProfile.objects.create(
                    user=user,
                    first_name=f_name,
                    last_name=l_name,
                    date_of_birth=fake.date_of_birth(minimum_age=20, maximum_age=35),
                    sex=random.choice(["M", "F"]),
                    civil_status="single",
                    phone_number=f"09{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
                    barangay="Baybay",
                    municipality="Carigara",
                    province="Leyte",
                    education_level="college",
                    status="approved"
                )
                applicants.append(app)

        # -------------------------------------------------------------
        # 2. SEED OFFERED JOBS / REFERRALS
        # -------------------------------------------------------------
        statuses = ["pending", "reviewed", "for interview", "hired", "rejected"]
        status_weights = [0.30, 0.25, 0.20, 0.15, 0.10]  # Weighted to give realistic distributions

        remarks_samples = {
            "pending": "Endorsed by PESO Manager. Pending employer initial review.",
            "reviewed": "Candidate portfolio and credentials reviewed by HR.",
            "for interview": "Scheduled for initial face-to-face interview on Friday.",
            "hired": "Successfully passed technical interview and signed job offer.",
            "rejected": "Position requirements do not align with current skill level."
        }

        officers = [
            "PESO Employment Officer - Carigara",
            "Labor Employment Officer II",
            "NSRP Desk Coordinator",
            "PESO Director - Leyte Office"
        ]

        created_count = 0
        for _ in range(count):
            selected_applicant = random.choice(applicants)
            selected_job = random.choice(jobs)
            selected_status = random.choices(statuses, weights=status_weights, k=1)[0]
            
            # Avoid duplicate referrals for the exact same applicant and job pair
            if OfferedJobs.objects.filter(applicant=selected_applicant, offered_job=selected_job).exists():
                continue

            offered = OfferedJobs.objects.create(
                applicant=selected_applicant,
                offered_job=selected_job,
                referred_by=random.choice(officers),
                status=selected_status,
                remarks=remarks_samples[selected_status]
            )
            
            # Backdate created date slightly for realistic audit history
            days_ago = random.randint(1, 45)
            OfferedJobs.objects.filter(id=offered.id).update(
                date_offered=timezone.now() - timedelta(days=days_ago)
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"✔ Successfully created {created_count} OfferedJobs (Referrals) with linked Employers and Vacancies!")
        )
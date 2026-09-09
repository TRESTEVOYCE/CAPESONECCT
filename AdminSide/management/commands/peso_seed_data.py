import io
import random
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from faker import Faker

from AdminSide.models import (
    EmployerProfile,
    Jobs,
    ApplicantSkills,
    ApplicantProfile,
    AppliedJobs,
    OfferedJobs,
    PESOActivities,
    AuditLog,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds test data matching DOLE NSRP Form 1 & 2 models for Employers, Jobs, Applicants, and Activities."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Base multiplier for generating applicants and jobs.",
        )

    def generate_dummy_id_image(self, applicant_name, applicant_id):
        """Generates a dummy Government / National ID card image using PIL."""
        width, height = 600, 380
        img = Image.new("RGB", (width, height), color=(245, 247, 250))
        draw = ImageDraw.Draw(img)

        # Draw card header banner
        draw.rectangle([0, 0, width, 70], fill=(17, 41, 84))
        draw.text((20, 20), "REPUBLIC OF THE PHILIPPINES", fill=(255, 255, 255))
        draw.text((20, 42), "NATIONAL SKILLS REGISTRATION PROGRAM - ID", fill=(220, 220, 220))

        # Draw photo placeholder box
        draw.rectangle([30, 90, 170, 260], fill=(210, 215, 225), outline=(100, 110, 120), width=2)
        draw.text((65, 165), "[ PHOTO ]", fill=(100, 110, 120))

        # Draw applicant details
        draw.text((190, 100), f"NAME: {applicant_name.upper()}", fill=(20, 20, 20))
        draw.text((190, 130), f"ID NO: {applicant_id}", fill=(20, 20, 20))
        draw.text((190, 160), "ISSUER: PESO CARIGARA, LEYTE", fill=(20, 20, 20))
        draw.text((190, 190), f"VERIFIED DATE: {timezone.now().strftime('%Y-%m-%d')}", fill=(20, 20, 20))

        # Draw footer bar
        draw.rectangle([0, 330, width, height], fill=(220, 225, 230))
        draw.text((20, 348), "FOR PESO OFFICIAL VERIFICATION USE ONLY", fill=(80, 80, 80))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return ContentFile(buffer.getvalue(), name=f"id_{applicant_id}.jpg")

    def handle(self, *args, **options):
        count = options["count"]
        fake = Faker("en_PH")

        self.stdout.write(self.style.WARNING("Starting NSRP-compliant PESO database seeding..."))

        # -------------------------------------------------------------
        # 1. SEED SKILLS
        # -------------------------------------------------------------
        skills_list = [
            "Customer Service", "Computer Literacy", "Data Entry", "MS Office",
            "SMAW Welding", "Driving (Professional)", "Bookkeeping", "Auto Mechanics",
            "Project Management", "Technical Support", "Carpentry", "Sales & Marketing",
            "Food Preparation", "Electrical Installation", "Graphic Design"
        ]
        created_skills = []
        for name in skills_list:
            skill, _ = ApplicantSkills.objects.get_or_create(skill_name=name)
            created_skills.append(skill)
        self.stdout.write(self.style.SUCCESS(f"✔ Ensured {len(created_skills)} Applicant Skills."))

        # -------------------------------------------------------------
        # 2. SEED ADMIN / PESO USERS
        # -------------------------------------------------------------
        admin_user, _ = User.objects.get_or_create(
            username="peso_admin",
            defaults={
                "email": "admin@carigara.gov.ph",
                "role": "admin",
                "first_name": "Maria",
                "last_name": "Andres",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.set_password("Password123!")
        admin_user.save()

        # -------------------------------------------------------------
        # 3. SEED EMPLOYERS (NSRP FORM 2 PAGE 1)
        # -------------------------------------------------------------
        employer_data = [
            {
                "business_name": "Carigara Hardware & Builders Corp.",
                "trade_name": "Carigara Hardware",
                "acronym": "CHBC",
                "office_type": "main",
                "employer_type": "direct_hire",
                "total_workforce": "small",
                "line_of_business": "Hardware & Construction Supplies",
            },
            {
                "business_name": "Leyte Agricultural Development Co-Op",
                "trade_name": "LeyteAgri Co-Op",
                "acronym": "LADCO",
                "office_type": "main",
                "employer_type": "direct_hire",
                "total_workforce": "medium",
                "line_of_business": "Agriculture and Farming Supplies",
            },
            {
                "business_name": "Eastern Visayas Tech Solutions Inc.",
                "trade_name": "EV Tech",
                "acronym": "EVTS",
                "office_type": "branch",
                "employer_type": "direct_hire",
                "total_workforce": "large",
                "line_of_business": "Information Technology Services",
            },
            {
                "business_name": "Municipal Government of Carigara",
                "trade_name": "LGU Carigara",
                "acronym": "LGU",
                "office_type": "main",
                "employer_type": "lgu",
                "total_workforce": "large",
                "line_of_business": "Public Administration / Government",
            },
            {
                "business_name": "Visayas Logistics Services Co.",
                "trade_name": "Visayas Logistics",
                "acronym": "VLS",
                "office_type": "branch",
                "employer_type": "local_agency",
                "total_workforce": "small",
                "line_of_business": "Transportation and Freight Storage",
            },
        ]

        created_employer_profiles = []
        for idx, emp in enumerate(employer_data):
            username = f"employer_{idx + 1}"
            email = f"contact@{username}.ph"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": "employer",
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                }
            )
            if created:
                user.set_password("Password123!")
                user.save()

            tin = f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(100, 999)}-000"

            emp_profile, _ = EmployerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "business_name": emp["business_name"],
                    "trade_name": emp["trade_name"],
                    "acronym": emp["acronym"],
                    "office_type": emp["office_type"],
                    "tin_number": tin,
                    "employer_type": emp["employer_type"],
                    "total_workforce": emp["total_workforce"],
                    "line_of_business": emp["line_of_business"],
                    "street_address": f"Real Street, Brgy. {fake.random_element(['Jugaban', 'Baybay', 'Ponong', 'Buntay'])}",
                    "barangay": fake.random_element(["Jugaban", "Baybay", "Ponong", "Buntay"]),
                    "municipality": "Carigara",
                    "province": "Leyte",
                    "owner_name": f"{fake.first_name()} {fake.last_name()}",
                    "contact_person": f"{fake.first_name()} {fake.last_name()}",
                    "contact_position": random.choice(["HR Manager", "General Manager", "Administrative Officer"]),
                    "telephone_number": f"(053) {random.randint(300, 899)}-{random.randint(1000, 9999)}",
                    "mobile_number": self.philippine_phone(),
                    "email": email,
                    "verification_status": "verified",
                }
            )
            created_employer_profiles.append(emp_profile)

        self.stdout.write(self.style.SUCCESS(f"✔ Seeded {len(created_employer_profiles)} NSRP Employer Profiles."))

        # -------------------------------------------------------------
        # 4. SEED VACANCIES / JOBS (NSRP FORM 2 PAGE 2)
        # -------------------------------------------------------------
        job_templates = [
            {
                "title": "Administrative Assistant",
                "nature": "permanent",
                "desc": "Handles office paperwork, record keeping, and client inquiries.",
                "exp": 12,
                "qual": "Good communication skills, proficient in MS Office suite.",
                "edu": "College",
                "strand": "BS Business Administration / Office Management",
                "lang": "English, Waray, Tagalog",
            },
            {
                "title": "IT Support Technician",
                "nature": "contractual",
                "desc": "Maintains municipal network infrastructure, desktop support, and hardware repair.",
                "exp": 24,
                "qual": "Knowledgeable in Cisco network devices and Windows/Linux server admin.",
                "edu": "College",
                "strand": "BS Information Technology / Computer Science",
                "cert": "NC II Computer Systems Servicing",
                "lang": "English, Waray",
            },
            {
                "title": "Store Cashier",
                "nature": "permanent",
                "desc": "Processes customer transactions, sales reports, and inventory monitoring.",
                "exp": 6,
                "qual": "Honest, detail-oriented with basic accounting capabilities.",
                "edu": "Senior High School",
                "strand": "Accountancy, Business and Management (ABM)",
                "lang": "Waray, Tagalog",
            },
            {
                "title": "SMAW Welder / Fabricator",
                "nature": "project_based",
                "desc": "Performs structural welding, metal fabrication, and site construction tasks.",
                "exp": 12,
                "qual": "Able to read fabrication blue prints and pass structural weld tests.",
                "edu": "Tech-Voc",
                "cert": "TESDA NC II SMAW Welding",
                "lang": "Waray",
            },
            {
                "title": "Agricultural Field Inspector",
                "nature": "permanent",
                "desc": "Monitors local farming cooperatives, crop yield reports, and soil health tests.",
                "exp": 12,
                "qual": "Fieldwork required. Knowledge of sustainable farming practices.",
                "edu": "College",
                "strand": "BS Agriculture / Agribusiness",
                "eligibility": "Civil Service Professional / Agriculturist License",
                "lang": "Waray, Tagalog",
            },
            {
                "title": "Graphic Design & Social Media Intern",
                "nature": "internship",
                "desc": "Creates visual assets, manages promotional materials and page content.",
                "exp": 0,
                "qual": "Proficient in Adobe Illustrator, Canva, and video editing tools.",
                "edu": "College",
                "strand": "BS Information Technology / Multimedia",
                "lang": "English, Waray",
            },
        ]

        created_jobs = []

        for emp in created_employer_profiles:
            selected_jobs = random.sample(job_templates, k=3)
            for j in selected_jobs:
                job = Jobs.objects.create(
                    job_title=j["title"],
                    job_description=j["desc"],
                    nature_of_work=j["nature"],
                    place_of_work=f"{emp.business_name}, {emp.street_address}, Carigara, Leyte",
                    salary=random.randint(450, 1000) * 26,
                    vacancy=random.randint(1, 8),
                    work_experience_months=j["exp"],
                    other_qualifications=j["qual"],
                    accepts_pwd=random.choice([True, False]),
                    pwd_disabilities="Visual, Hearing, Physical" if random.choice([True, False]) else None,
                    accepts_ofw=random.choice([True, False]),
                    educational_level=j["edu"],
                    course_or_strand=j.get("strand"),
                    required_license=j.get("license"),
                    required_eligibility=j.get("eligibility"),
                    required_certification=j.get("cert"),
                    languages_spoken=j["lang"],
                    employer=emp,
                    status=random.choice(["Active", "Active", "Pending", "Filled"]),
                    job_posting_expiry=timezone.now().date() + timedelta(days=random.randint(15, 60)),
                )
                created_jobs.append(job)

        self.stdout.write(self.style.SUCCESS(f"✔ Seeded {len(created_jobs)} NSRP Job Vacancies."))

        # -------------------------------------------------------------
        # 5. SEED APPLICANTS & PROFILES (NSRP FORM 1 UPDATED)
        # -------------------------------------------------------------
        unemployment_reasons = [
            "fresh_grad", "finished_contract", "resigned",
            "retired", "laid_off_local", "laid_off_abroad"
        ]
        created_applicant_profiles = []

        for i in range(count):
            sex = random.choice(["M", "F"])
            f_name = fake.first_name_male() if sex == "M" else fake.first_name_female()
            l_name = fake.last_name()
            username = f"applicant_{i+1}"
            email = f"{username}@gmail.com"

            # Step 1: Create User with required email field
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": "applicant",
                    "first_name": f_name,
                    "last_name": l_name,
                }
            )
            if created:
                user.set_password("Password123!")
                user.save()

            dob = fake.date_of_birth(minimum_age=18, maximum_age=45)
            emp_status = random.choice(["unemployed", "unemployed", "employed"])
            unemp_reason = random.choice(unemployment_reasons) if emp_status == "unemployed" else None

            # Step 2: Create ApplicantProfile
            app_profile = ApplicantProfile.objects.create(
                user=user,
                first_name=f_name,
                middle_name=fake.last_name(),
                last_name=l_name,
                date_of_birth=dob,
                sex=sex,
                civil_status=random.choice(["single", "married"]),
                phone_number=self.philippine_phone(),
                house_street=f"Block {random.randint(1,15)} Lot {random.randint(1,30)}",
                barangay=fake.random_element(["Jugaban", "Baybay", "Ponong", "Buntay", "Sawang", "Cogon"]),
                municipality="Carigara",
                province="Leyte",
                region="Eastern Visayas",
                zip_code="6529",
                
                # NSRP Form 1 Specific Fields
                employment_status=emp_status,
                unemployment_reason=unemp_reason,
                actively_looking=True,
                looking_duration=f"{random.randint(1, 12)} months",
                is_4ps_beneficiary=random.choice([True, False]),
                household_id_no=f"4PS-{random.randint(100000, 999999)}" if random.choice([True, False]) else None,
                is_ofw=random.choice([True, False]),
                expected_salary=random.randint(12000, 35000),
                
                education_level=random.choice(["high_school", "college", "vocational"]),
                school_name=f"{fake.city()} State University",
                course_program="BS Information Technology" if sex == "M" else "BS Business Administration",
                year_graduated="2023",
                status=random.choice(["approved", "pending"]),
            )

            # Step 3: Attach generated ID Image file
            formatted_name = f"{f_name} {l_name}"
            app_id_code = f"APP-2026-{i+1:04d}"
            id_file = self.generate_dummy_id_image(formatted_name, app_id_code)
            app_profile.applicant_id_picture.save(f"id_{app_id_code}.jpg", id_file, save=True)

            # Assign random skills & preferred jobs
            app_profile.skills.set(random.sample(created_skills, k=random.randint(2, 4)))
            app_profile.preferred_job.set(random.sample(created_jobs, k=random.randint(1, 3)))
            created_applicant_profiles.append(app_profile)

        self.stdout.write(self.style.SUCCESS(f"✔ Seeded {len(created_applicant_profiles)} Applicants with generated ID images."))

        # -------------------------------------------------------------
        # 6. SEED APPLIED JOBS & OFFERED JOBS
        # -------------------------------------------------------------
        for app in created_applicant_profiles:
            target_jobs = random.sample(created_jobs, k=2)
            for j in target_jobs:
                is_hired = random.choice([True, False, False])
                status = "hired" if is_hired else random.choice(["pending", "reviewed", "for interview"])

                AppliedJobs.objects.create(
                    applicant=app,
                    applied_job=j,
                    is_hired=is_hired,
                    status=status,
                )

            offered_job = random.choice(created_jobs)
            OfferedJobs.objects.create(
                applicant=app,
                offered_job=offered_job,
                referred_by="PESO Officer - Carigara",
                status=random.choice(["pending", "for interview", "hired"]),
                remarks="Matches candidate profile, educational attainment, and skill assessments."
            )

        self.stdout.write(self.style.SUCCESS("✔ Seeded Applied & Offered Jobs."))

        # -------------------------------------------------------------
        # 7. SEED ACTIVITIES & AUDIT LOGS
        # -------------------------------------------------------------
        activities = [
            ("Carigara NSRP Job Fair 2026", "Municipal-wide local and overseas job matching event.", 350),
            ("Pre-Employment Seminar for Local Applicants", "Orientation on DOLE & NSRP employment requirements.", 80),
            ("PESO Special Recruitment Activity (SRA)", "Direct hiring session with accredited NSRP establishments.", 120),
        ]

        for name, desc, participants in activities:
            PESOActivities.objects.create(
                activity_name=name,
                activity_description=desc,
                number_of_participants=participants,
                activity_date=timezone.now().date() + timedelta(days=random.randint(5, 30)),
                activity_time="09:00:00",
                activity_location="Carigara Municipal Gym, Leyte",
                organizer="PESO Carigara",
                added_by=admin_user,
            )

        AuditLog.objects.create(
            user=admin_user, 
            action="Executed updated seed_peso_data script with NSRP Form 1 & 2 model compliance."
        )

        self.stdout.write(self.style.SUCCESS("✔ Seeded PESO Activities & Audit Logs."))
        self.stdout.write(self.style.SUCCESS("🎉 Database Seeding Complete!"))

    def philippine_phone(self):
        return f"09{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
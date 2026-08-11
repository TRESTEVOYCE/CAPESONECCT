import random
import uuid
from io import BytesIO
from urllib.request import Request, urlopen
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from AdminSide.models import (
    User,
    EmployerProfile,
    Jobs,
    ApplicantSkills,
    ApplicantProfile,
    AppliedJobs,
    OfferedJobs,
)


class Command(BaseCommand):

    help = "Generate sample applicants, employers, jobs, applications, and offers."

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            help="Number of applicants and employers to create.",
        )

        parser.add_argument(
            "--with-images",
            action="store_true",
            help="Download DiceBear avatars for generated users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        count = options["count"]
        with_images = options["with_images"]

        if count <= 0:
            self.stdout.write(
                self.style.ERROR(
                    "Count must be greater than 0."
                )
            )
            return

        fake = Faker("en_PH")

        self.stdout.write(
            self.style.WARNING(
                f"Creating {count:,} applicants and {count:,} employers..."
            )
        )

        # ---------------------------------------------------------
        # Create skills
        # ---------------------------------------------------------

        skills = self.create_skills()

        # ---------------------------------------------------------
        # Create applicants
        # ---------------------------------------------------------

        applicants = self.create_applicants(
            fake,
            count,
            skills,
            with_images,
        )

        # ---------------------------------------------------------
        # Create employers
        # ---------------------------------------------------------

        employers = self.create_employers(
            fake,
            count,
            with_images,
        )

        # ---------------------------------------------------------
        # Create jobs
        # ---------------------------------------------------------

        jobs = self.create_jobs(
            fake,
            employers,
            count,
        )

        # ---------------------------------------------------------
        # Assign preferred jobs
        # ---------------------------------------------------------

        self.assign_preferred_jobs(
            applicants,
            jobs,
        )

        # ---------------------------------------------------------
        # Create applications
        # ---------------------------------------------------------

        applications = self.create_applications(
            applicants,
            jobs,
            count,
        )

        # ---------------------------------------------------------
        # Create offers
        # ---------------------------------------------------------

        self.create_offers(
            applications,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Sample data successfully created."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Applicants : {len(applicants):,}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Employers  : {len(employers):,}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Jobs       : {len(jobs):,}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Applications: {AppliedJobs.objects.count():,}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Offers     : {OfferedJobs.objects.count():,}"
            )
        )

    # =========================================================
    # SKILLS
    # =========================================================

    def create_skills(self):

        skill_names = [
            "Python",
            "Django",
            "Django REST Framework",
            "JavaScript",
            "React",
            "HTML",
            "CSS",
            "Tailwind CSS",
            "Java",
            "C++",
            "C#",
            "PHP",
            "Laravel",
            "Node.js",
            "SQL",
            "MySQL",
            "PostgreSQL",
            "MongoDB",
            "Git",
            "GitHub",
            "Docker",
            "Linux",
            "Networking",
            "CCNA",
            "Cybersecurity",
            "Network Administration",
            "Technical Support",
            "Computer Hardware",
            "Microsoft Office",
            "Excel",
            "Word",
            "PowerPoint",
            "Accounting",
            "Bookkeeping",
            "Customer Service",
            "Communication",
            "Sales",
            "Marketing",
            "Graphic Design",
            "Video Editing",
            "Data Entry",
            "Project Management",
            "Human Resources",
            "Teaching",
            "Research",
            "Food Preparation",
            "Hospitality",
            "Driving",
            "Electrical Installation",
            "Welding",
        ]

        skills = []

        for name in skill_names:

            skill, created = ApplicantSkills.objects.get_or_create(
                skill_name=name
            )

            skills.append(skill)

        self.stdout.write(
            f"  Skills: {len(skills):,}"
        )

        return skills

    # =========================================================
    # APPLICANTS
    # =========================================================

    def create_applicants(
        self,
        fake,
        count,
        skills,
        with_images,
    ):

        applicants = []

        education_levels = [
            "elementary",
            "high_school",
            "college",
            "university",
            "vocational",
            "other",
        ]

        for _ in range(count):

            sex = random.choice(["M", "F"])

            first_name = (
                fake.first_name_male()
                if sex == "M"
                else fake.first_name_female()
            )

            middle_name = fake.first_name()
            last_name = fake.last_name()

            username = self.unique_username(
                first_name,
                last_name,
            )

            email = (
                f"{username}"
                f"@example.com"
            )

            user = User.objects.create_user(
                username=username,
                email=email,
                password="Password123!",
                role="applicant",
                is_active=True,
            )

            if with_images:
                self.add_avatar(
                    user,
                    seed=str(user.uuid),
                    style="personas",
                )

            applicant = ApplicantProfile.objects.create(
                user=user,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                date_of_birth=fake.date_of_birth(
                    minimum_age=18,
                    maximum_age=60,
                ),
                sex=sex,
                civil_status=random.choice([
                    "single",
                    "married",
                    "divorced",
                    "widowed",
                ]),
                phone_number=self.philippine_phone(),
                barangay=random.choice([
                    "Abucay",
                    "Bagacay",
                    "Buntay",
                    "Can-abay",
                    "Cangumbang",
                    "Cogon",
                    "Downtown",
                    "Guindapunan",
                    "Libertad",
                    "Palanog",
                    "San Jose",
                    "San Roque",
                    "Santa Cruz",
                    "Santo Niño",
                ]),
                municipality=random.choice([
                    "Tacloban City",
                    "Palo",
                    "Tanauan",
                    "Basey",
                    "Marabut",
                    "Tolosa",
                    "Dulag",
                    "Alangalang",
                    "Babatngon",
                    "Jaro",
                ]),
                province="Leyte",
                region="Eastern Visayas",
                zip_code=random.choice([
                    "6500",
                    "6501",
                    "6502",
                    "6503",
                    "6504",
                    "6505",
                ]),
                education_level=random.choice(
                    education_levels
                ),
                status="pending",
            )

            # Give each applicant 2-6 skills
            applicant.skills.set(
                random.sample(
                    skills,
                    k=random.randint(
                        2,
                        min(6, len(skills)),
                    ),
                )
            )

            applicants.append(applicant)

        self.stdout.write(
            f"  Applicants: {len(applicants):,}"
        )

        return applicants

    # =========================================================
    # EMPLOYERS
    # =========================================================

    def create_employers(
        self,
        fake,
        count,
        with_images,
    ):

        employers = []

        company_names = [
            "Eastern Visayas Technology Solutions",
            "Leyte Business Solutions",
            "Tacloban Digital Services",
            "Visayas Software Development",
            "Eastern Visayas Trading Corporation",
            "Leyte Manufacturing Corporation",
            "Tacloban Hospitality Group",
            "Eastern Visayas Healthcare Services",
            "Visayas Logistics Corporation",
            "Leyte Construction Services",
            "Eastern Visayas Financial Services",
            "Tacloban Retail Group",
            "Visayas Agricultural Corporation",
            "Leyte Telecommunications",
            "Eastern Visayas Consulting Group",
        ]

        for _ in range(count):

            company_name = (
                f"{random.choice(company_names)} "
                f"{random.randint(100, 999)}"
            )

            username = (
                "employer_"
                f"{uuid.uuid4().hex[:8]}"
            )

            email = (
                f"{username}"
                "@example.com"
            )

            user = User.objects.create_user(
                username=username,
                email=email,
                password="Password123!",
                role="employer",
                is_active=True,
            )

            if with_images:
                self.add_avatar(
                    user,
                    seed=str(user.uuid),
                    style="personas",
                )

            employer = EmployerProfile.objects.create(
                user=user,
                company_name=company_name,
                company_type=random.choice([
                    "private",
                    "government",
                    "non_profit",
                    "other",
                ]),
                business_permit=self.fake_business_permit(),
                email=fake.unique.company_email(),
                phone_number=self.philippine_phone(),
                company_address=(
                    f"{random.randint(1, 999)} "
                    f"{fake.street_name()}, "
                    f"Tacloban City, Leyte"
                ),
                contact_person=fake.name(),
                verification_status=random.choice([
                    "pending",
                    "verified",
                    "verified",
                    "verified",
                    "rejected",
                ]),
            )

            employers.append(employer)

        self.stdout.write(
            f"  Employers: {len(employers):,}"
        )

        return employers

    # =========================================================
    # JOBS
    # =========================================================

    def create_jobs(
        self,
        fake,
        employers,
        count,
    ):

        jobs = []

        job_titles = [
            "Software Developer",
            "Web Developer",
            "Backend Developer",
            "Frontend Developer",
            "Full Stack Developer",
            "IT Support Specialist",
            "Network Administrator",
            "Cybersecurity Analyst",
            "Data Entry Specialist",
            "Administrative Assistant",
            "Accountant",
            "Bookkeeper",
            "Customer Service Representative",
            "Sales Representative",
            "Marketing Assistant",
            "Graphic Designer",
            "Video Editor",
            "HR Assistant",
            "Project Coordinator",
            "Electrical Technician",
        ]

        job_descriptions = [
            "We are looking for a motivated professional to join our team.",
            "The successful candidate will work with our team on daily operations and projects.",
            "This position requires someone who is organized, responsible, and willing to learn.",
            "The candidate will support the company's daily activities and assigned projects.",
        ]

        requirements = [
            "Good communication skills",
            "Ability to work with a team",
            "Computer literate",
            "Strong problem-solving skills",
            "Willing to learn",
            "Relevant educational background",
        ]

        sectors = [
            "BPO / IT",
            "Finance",
            "Administrative",
            "Hospitality",
            "Wholesale & Retail",
            "Logistics",
            "Manufacturing",
            "Construction",
            "Healthcare",
            "Education",
            "Public Sector",
            "Agriculture",
        ]

        for _ in range(count):

            employer = random.choice(employers)

            title = random.choice(job_titles)

            job = Jobs.objects.create(
                job_title=title,
                job_description=random.choice(
                    job_descriptions
                ),
                job_requirements="\n".join(
                    random.sample(
                        requirements,
                        k=random.randint(3, 6),
                    )
                ),
                job_location=random.choice([
                    "Tacloban City",
                    "Palo, Leyte",
                    "Tanauan, Leyte",
                    "Ormoc City",
                    "Baybay City",
                    "Cebu City",
                    "Manila",
                    "Remote",
                ]),
                job_type=random.choice([
                    "full_time",
                    "part_time",
                    "contract",
                    "internship",
                ]),
                vacancy=random.randint(1, 15),
                salary=random.randint(
                    12000,
                    60000,
                ),
                employer=employer,
                status=random.choice([
                    "Active",
                    "Active",
                    "Active",
                    "Pending",
                    "Filled",
                    "Closed",
                ]),
                job_posting_expiry=timezone.make_aware(
                fake.date_time_between(
                    start_date="+30d",
                    end_date="+180d",
                )
),
            )

            jobs.append(job)

        self.stdout.write(
            f"  Jobs: {len(jobs):,}"
        )

        return jobs

    # =========================================================
    # PREFERRED JOBS
    # =========================================================

    def assign_preferred_jobs(
        self,
        applicants,
        jobs,
    ):

        if not jobs:
            return

        for applicant in applicants:

            preferred = random.sample(
                jobs,
                k=random.randint(
                    1,
                    min(5, len(jobs)),
                ),
            )

            applicant.preferred_job.set(
                preferred
            )

        self.stdout.write(
            "  Preferred jobs assigned."
        )

    # =========================================================
    # APPLICATIONS
    # =========================================================

    def create_applications(
        self,
        applicants,
        jobs,
        count,
    ):

        applications = []

        # Not every applicant needs to apply to every job.
        for applicant in applicants:

            number_of_applications = random.randint(
                0,
                min(5, len(jobs)),
            )

            selected_jobs = random.sample(
                jobs,
                k=number_of_applications,
            )

            for job in selected_jobs:

                application = AppliedJobs.objects.create(
                    applicant=applicant,
                    applied_job=job,
                    is_hired=False,
                    status=random.choice([
                        "pending",
                        "reviewed",
                        "for interview",
                        "hired",
                        "rejected",
                    ]),
                )

                applications.append(
                    application
                )

        self.stdout.write(
            f"  Applications: {len(applications):,}"
        )

        return applications

    # =========================================================
    # OFFERS
    # =========================================================

    def create_offers(
        self,
        applications,
    ):

        offers = []

        # Only a percentage of applications receive offers.
        for application in applications:

            if application.status not in [
                "for interview",
                "hired",
            ]:
                continue

            if random.random() > 0.25:
                continue

            offer = OfferedJobs.objects.create(
                applicant=application.applicant,
                offered_job=application.applied_job,
                referred_by=random.choice([
                    "PESO",
                    "MSWDO",
                    "Employer",
                    "Job Fair",
                    "Online Application",
                    None,
                ]),
                status=random.choice([
                    "pending",
                    "reviewed",
                    "for interview",
                    "hired",
                ]),
                remarks=random.choice([
                    None,
                    "Candidate recommended for interview.",
                    "Employer requested additional documents.",
                    "Candidate qualified for the position.",
                ]),
            )

            offers.append(offer)

        self.stdout.write(
            f"  Offers: {len(offers):,}"
        )

        return offers

    # =========================================================
    # UTILITIES
    # =========================================================

    def unique_username(
        self,
        first_name,
        last_name,
    ):

        base = (
            f"{first_name.lower()}"
            f".{last_name.lower()}"
        )

        username = base

        while User.objects.filter(
            username=username
        ).exists():

            username = (
                f"{base}"
                f"{random.randint(1000, 9999)}"
            )

        return username

    def philippine_phone(self):

        return (
            "09"
            f"{random.randint(10, 99)}"
            f"{random.randint(1000000, 9999999)}"
        )

    def fake_business_permit(self):

        return ContentFile(
            b"Sample business permit for development data.",
            name=f"business_permit_{uuid.uuid4().hex}.txt",
        )

    # =========================================================
    # DICEBEAR AVATAR
    # =========================================================

    def add_avatar(
        self,
        user,
        seed,
        style="personas",
    ):

        try:

            url = (
                f"https://api.dicebear.com/10.x/"
                f"{style}/png"
                f"?seed={seed}&size=256"
            )

            request = Request(
                url,
                headers={
                    "User-Agent": "Django Development Seeder"
                },
            )

            with urlopen(
                request,
                timeout=10,
            ) as response:

                image_data = response.read()

            user.profile_picture.save(
                f"{user.username}.png",
                ContentFile(image_data),
                save=True,
            )

        except Exception as exc:

            self.stdout.write(
                self.style.WARNING(
                    f"Could not download avatar for "
                    f"{user.username}: {exc}"
                )
            )
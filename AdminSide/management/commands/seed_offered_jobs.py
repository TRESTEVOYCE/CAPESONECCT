"""
Seed demo employers, jobs, and applicants for CAPESCONNECT job-matching tests.

Install this file at:
    <your_app>/management/commands/seed_demo_data.py

Run:
    python manage.py seed_demo_data

Optional:
    python manage.py seed_demo_data --password "YourDemoPassword"
    python manage.py seed_demo_data --skip-matching
    python manage.py seed_demo_data --matching-module your_app.utils.job_matching
"""

import os
from datetime import date, timedelta
from decimal import Decimal
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


EMPLOYERS = [
    {
        "username": "demo_employer1",
        "email": "demo_employer1@example.com",
        "business_name": "Carigara Tech Solutions",
        "line_of_business": "Information Technology and Software Services",
        "barangay": "San Roque",
        "municipality": "Carigara",
        "province": "Leyte",
        "contact_person": "Demo Employer One",
        "mobile_number": "09170000001",
    },
    {
        "username": "demo_employer2",
        "email": "demo_employer2@example.com",
        "business_name": "Leyte Builders and Fabrication",
        "line_of_business": "Construction and Metal Fabrication",
        "barangay": "Barugohay Central",
        "municipality": "Carigara",
        "province": "Leyte",
        "contact_person": "Demo Employer Two",
        "mobile_number": "09170000002",
    },
    {
        "username": "demo_employer3",
        "email": "demo_employer3@example.com",
        "business_name": "Carigara Business Services",
        "line_of_business": "Accounting and Administrative Services",
        "barangay": "Ponong",
        "municipality": "Carigara",
        "province": "Leyte",
        "contact_person": "Demo Employer Three",
        "mobile_number": "09170000003",
    },
]


JOBS = [
    {
        "employer": "demo_employer1",
        "job_title": "Junior Python Developer",
        "job_description": (
            "Develop and maintain web applications using Python and Django. "
            "Work with SQL databases, troubleshoot application issues, write "
            "clean code, and collaborate with a development team."
        ),
        "nature_of_work": "permanent",
        "salary": Decimal("22000.00"),
        "vacancy": 2,
        "work_experience_months": 0,
        "educational_level": "college",
        "course_or_strand": "Information Technology, Computer Science, or related course",
        "other_qualifications": "Python, Django, SQL, database fundamentals, and computer skills.",
        "custom_skills": ["Python", "Django", "SQL", "Web Development", "Computer Skills"],
        "skill_problem_solving": True,
        "skill_team_work": True,
    },
    {
        "employer": "demo_employer1",
        "job_title": "IT Support Technician",
        "job_description": (
            "Provide first-level technical support, install and configure "
            "computer equipment, troubleshoot hardware and software, and assist "
            "users with basic network and office technology issues."
        ),
        "nature_of_work": "contractual",
        "salary": Decimal("16000.00"),
        "vacancy": 2,
        "work_experience_months": 0,
        "educational_level": "vocational",
        "course_or_strand": "Computer Systems Servicing or Information Technology",
        "other_qualifications": "Computer troubleshooting, hardware, software installation, and customer support.",
        "custom_skills": [
            "Computer Troubleshooting",
            "Hardware",
            "Technical Support",
            "Customer Support",
        ],
        "skill_problem_solving": True,
    },
    {
        "employer": "demo_employer2",
        "job_title": "Welder",
        "job_description": (
            "Perform metal welding and fabrication tasks, read basic shop "
            "drawings, inspect finished welds, and follow workplace safety "
            "procedures. Applicants with welding training or NC certification "
            "are preferred."
        ),
        "nature_of_work": "project_based",
        "salary": Decimal("650.00"),
        "vacancy": 3,
        "work_experience_months": 0,
        "educational_level": "vocational",
        "course_or_strand": "Welding or Shielded Metal Arc Welding",
        "required_certification": "TESDA Welding NC II preferred",
        "other_qualifications": "Welding, metal fabrication, measuring, and occupational safety.",
        "custom_skills": ["Welding", "Metal Fabrication", "Measurement"],
        "skill_welding": True,
        "skill_team_work": True,
        "skill_work_ethics": True,
    },
    {
        "employer": "demo_employer2",
        "job_title": "Carpenter",
        "job_description": (
            "Measure, cut, assemble, and install wooden structures and fixtures. "
            "Use hand and power tools safely and coordinate with construction "
            "workers on project deadlines."
        ),
        "nature_of_work": "project_based",
        "salary": Decimal("600.00"),
        "vacancy": 2,
        "work_experience_months": 0,
        "educational_level": "vocational",
        "course_or_strand": "Carpentry or Construction",
        "other_qualifications": "Carpentry, construction measurement, hand tools, and teamwork.",
        "custom_skills": ["Carpentry", "Construction", "Measurement"],
        "skill_carpentry": True,
        "skill_masonry": True,
        "skill_team_work": True,
    },
    {
        "employer": "demo_employer3",
        "job_title": "Accounting Assistant",
        "job_description": (
            "Assist with bookkeeping, encode financial transactions, organize "
            "receipts and invoices, prepare basic financial summaries, and "
            "maintain accurate accounting records."
        ),
        "nature_of_work": "permanent",
        "salary": Decimal("18000.00"),
        "vacancy": 1,
        "work_experience_months": 0,
        "educational_level": "college",
        "course_or_strand": "Accountancy, Accounting Technology, or Business Administration",
        "other_qualifications": "Bookkeeping, spreadsheets, attention to detail, and basic accounting.",
        "custom_skills": ["Bookkeeping", "Accounting", "Spreadsheets"],
        "skill_math_functional": True,
    },
    {
        "employer": "demo_employer3",
        "job_title": "Administrative Assistant",
        "job_description": (
            "Provide clerical and administrative support, handle records and "
            "correspondence, assist clients, answer inquiries, and coordinate "
            "daily office tasks."
        ),
        "nature_of_work": "permanent",
        "salary": Decimal("17000.00"),
        "vacancy": 1,
        "work_experience_months": 0,
        "educational_level": "college",
        "course_or_strand": "Business Administration or any related course",
        "other_qualifications": "Customer service, computer literacy, communication, and office administration.",
        "custom_skills": [
            "Customer Service",
            "Office Administration",
            "Communication",
            "Computer Literacy",
        ],
        "skill_english_functional": True,
    },
]


APPLICANTS = [
    {
        "username": "demo_applicant1",
        "email": "demo_applicant1@example.com",
        "first_name": "Alex",
        "last_name": "Developer",
        "sex": "M",
        "date_of_birth": date(2000, 5, 15),
        "education_level": "college",
        "school_name": "Eastern Visayas State University",
        "course_program": "Bachelor of Science in Information Technology",
        "year_graduated": "2024",
        "skills": ["Python", "Django", "SQL", "Web Development", "Computer Troubleshooting"],
        "preferred_titles": ["Junior Python Developer", "IT Support Technician"],
        "other_skills": "Programming, database management, web development",
        "skill_computer": True,
        "skill_problem_solving": True,
        "skill_critical_thinking": True,
    },
    {
        "username": "demo_applicant2",
        "email": "demo_applicant2@example.com",
        "first_name": "Jordan",
        "last_name": "Builder",
        "sex": "M",
        "date_of_birth": date(1998, 8, 20),
        "education_level": "vocational",
        "school_name": "TESDA Accredited Training Center",
        "course_program": "Welding and Fabrication",
        "year_graduated": "2023",
        "skills": ["Welding", "Metal Fabrication", "Carpentry", "Construction", "Measurement"],
        "preferred_titles": ["Welder", "Carpenter"],
        "other_skills": "Hand tools, construction safety, metal works",
        "skill_welding": True,
        "skill_carpentry": True,
        "skill_team_work": True,
    },
    {
        "username": "demo_applicant3",
        "email": "demo_applicant3@example.com",
        "first_name": "Taylor",
        "last_name": "Bookkeeper",
        "sex": "F",
        "date_of_birth": date(2001, 2, 10),
        "education_level": "college",
        "school_name": "University of the Philippines Visayas",
        "course_program": "Bachelor of Science in Business Administration",
        "year_graduated": "2024",
        "skills": ["Bookkeeping", "Accounting", "Spreadsheets", "Customer Service", "Office Administration"],
        "preferred_titles": ["Accounting Assistant", "Administrative Assistant"],
        "other_skills": "Financial records, office work, client assistance",
        "skill_bookkeeping": True,
        "skill_computer": True,
        "skill_customer_service": True,
        "skill_math_functional": True,
    },
]


class Command(BaseCommand):
    help = "Create demo employers, active job posts, approved applicants, and test job recommendations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=os.environ.get("DEMO_SEED_PASSWORD", "DemoPass123!"),
            help="Password assigned only to newly created demo users.",
        )
        parser.add_argument(
            "--skip-matching",
            action="store_true",
            help="Create database records but skip ChromaDB indexing and recommendation tests.",
        )
        parser.add_argument(
            "--matching-module",
            default=None,
            help=(
                "Python module containing upsert_job_vector and query_matching_jobs. "
                "Example: your_app.utils.job_matching"
            ),
        )

    def handle(self, *args, **options):
        password = options["password"]
        if not password:
            raise CommandError("A non-empty --password is required.")

        app_label = __package__.split(".")[0]
        try:
            User = apps.get_model(settings.AUTH_USER_MODEL)
            EmployerProfile = apps.get_model(app_label, "EmployerProfile")
            Jobs = apps.get_model(app_label, "Jobs")
            JobSkills = apps.get_model(app_label, "JobSkills")
            ApplicantProfile = apps.get_model(app_label, "ApplicantProfile")
            ApplicantSkills = apps.get_model(app_label, "ApplicantSkills")
        except LookupError as exc:
            raise CommandError(
                f"Could not load the expected models from app '{app_label}'. "
                "Place this command inside your Django app's management/commands folder."
            ) from exc

        employer_by_username = {}
        applicant_by_username = {}
        jobs_by_title = {}

        with transaction.atomic():
            for data in EMPLOYERS:
                user, created = User.objects.get_or_create(
                    email=data["email"],
                    defaults={
                        "username": data["username"],
                        "role": "employer",
                        "is_active": True,
                        "email_verified": True,
                    },
                )
                if created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Created employer login: {user.username}"))
                else:
                    # Only update demo-owned accounts; never reset an existing password.
                    changed = []
                    if user.role != "employer":
                        user.role = "employer"
                        changed.append("role")
                    if not user.is_active:
                        user.is_active = True
                        changed.append("is_active")
                    if not user.email_verified:
                        user.email_verified = True
                        changed.append("email_verified")
                    if changed:
                        user.save(update_fields=changed)

                profile, _ = EmployerProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "business_name": data["business_name"],
                        "line_of_business": data["line_of_business"],
                        "barangay": data["barangay"],
                        "municipality": data["municipality"],
                        "province": data["province"],
                        "contact_person": data["contact_person"],
                        "mobile_number": data["mobile_number"],
                        "email": data["email"],
                        "employer_type": "direct_hire",
                        "total_workforce": "small",
                        "verification_status": "verified",
                    },
                )
                employer_by_username[data["username"]] = profile

            for data in JOBS:
                employer = employer_by_username[data["employer"]]
                defaults = {
                    key: value
                    for key, value in data.items()
                    if key not in {"employer", "custom_skills"}
                }
                defaults.update({
                    "employer": employer,
                    "place_of_work": f"{employer.municipality}, {employer.province}",
                    "status": "Active",
                    "job_posting_expiry": timezone.localdate() + timedelta(days=90),
                    "accepts_pwd": True,
                    "accepts_ofw": False,
                    "languages_spoken": "English, Filipino",
                })
                job, _ = Jobs.objects.update_or_create(
                    employer=employer,
                    job_title=data["job_title"],
                    defaults=defaults,
                )
                for skill in data["custom_skills"]:
                    JobSkills.objects.get_or_create(job=job, skill_name=skill)
                jobs_by_title[data["job_title"]] = job

            for data in APPLICANTS:
                user, created = User.objects.get_or_create(
                    email=data["email"],
                    defaults={
                        "username": data["username"],
                        "role": "applicant",
                        "is_active": True,
                        "email_verified": True,
                        "first_name": data["first_name"],
                        "last_name": data["last_name"],
                    },
                )
                if created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Created applicant login: {user.username}"))
                else:
                    changed = []
                    if user.role != "applicant":
                        user.role = "applicant"
                        changed.append("role")
                    if not user.is_active:
                        user.is_active = True
                        changed.append("is_active")
                    if not user.email_verified:
                        user.email_verified = True
                        changed.append("email_verified")
                    if changed:
                        user.save(update_fields=changed)

                profile_defaults = {
                    key: value
                    for key, value in data.items()
                    if key not in {
                        "username", "email", "skills", "preferred_titles"
                    }
                }
                profile_defaults.update({
                    "user": user,
                    "civil_status": "single",
                    "phone_number": "09170000010",
                    "barangay": "San Roque",
                    "municipality": "Carigara",
                    "province": "Leyte",
                    "region": "Eastern Visayas",
                    "employment_status": "unemployed",
                    "unemployment_reason": "fresh_grad",
                    "actively_looking": True,
                    "expected_salary": Decimal("18000.00"),
                    "status": "approved",
                    "email_address": data["email"],
                    "nationality": "Filipino",
                    "willing_to_work_immediately": True,
                })
                profile, _ = ApplicantProfile.objects.update_or_create(
                    user=user,
                    defaults=profile_defaults,
                )

                skill_objects = []
                for skill_name in data["skills"]:
                    skill, _ = ApplicantSkills.objects.get_or_create(
                        skill_name=skill_name
                    )
                    skill_objects.append(skill)
                profile.skills.set(skill_objects)

                preferred_jobs = [
                    jobs_by_title[title]
                    for title in data["preferred_titles"]
                    if title in jobs_by_title
                ]
                profile.preferred_job.set(preferred_jobs)
                applicant_by_username[data["username"]] = profile

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Database seeded: {len(EMPLOYERS)} employers, {len(JOBS)} jobs, "
            f"{len(APPLICANTS)} approved applicants."
        ))
        self.stdout.write("Demo account password applies only to newly created users.")
        self.stdout.write("Demo logins:")
        for item in EMPLOYERS + APPLICANTS:
            self.stdout.write(f"  {item['username']} / {item['email']}")

        if options["skip_matching"]:
            self.stdout.write(self.style.WARNING(
                "Skipped ChromaDB indexing and recommendation tests."
            ))
            return

        matching_module = options["matching_module"]
        candidates = (
            [matching_module] if matching_module else [
                f"{app_label}.job_matching",
                f"{app_label}.utils.job_matching",
                f"{app_label}.utils",
            ]
        )

        matching = None
        import_errors = []
        for module_path in candidates:
            try:
                module = import_module(module_path)
                if hasattr(module, "upsert_job_vector") and hasattr(module, "query_matching_jobs"):
                    matching = module
                    break
                import_errors.append(f"{module_path}: matching functions not found")
            except ImportError as exc:
                import_errors.append(f"{module_path}: {exc}")

        if matching is None:
            self.stdout.write(self.style.WARNING(
                "Database records were created, but ChromaDB matching was skipped. "
                "Could not locate upsert_job_vector/query_matching_jobs."
            ))
            self.stdout.write(
                "Rerun with --matching-module your_app.path.to.the_module"
            )
            for error in import_errors:
                self.stdout.write(f"  - {error}")
            return

        # Index only jobs that are currently active and belong to verified employers.
        active_verified_jobs = Jobs.objects.filter(
            status="Active",
            employer__verification_status="verified",
        ).select_related("employer").prefetch_related("custom_skills")

        indexed = 0
        for job in active_verified_jobs:
            matching.upsert_job_vector(job)
            indexed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Indexed {indexed} active jobs from verified employers in ChromaDB."
        ))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("APPLICANT RECOMMENDATION TEST"))
        for username, applicant in applicant_by_username.items():
            result = matching.query_matching_jobs(applicant, total_results=10)
            ids = result.get("ids", [])
            distances = result.get("distances", [])
            metadata = result.get("metadatas", [])

            self.stdout.write(f"\n{username} ({applicant.first_name} {applicant.last_name})")
            if not ids:
                self.stdout.write(self.style.WARNING(
                    "  No recommendations returned. Check ChromaDB collection and embeddings."
                ))
                continue

            for index, job_id in enumerate(ids):
                distance = distances[index] if index < len(distances) else None
                meta = metadata[index] if index < len(metadata) else {}
                title = meta.get("title", "Unknown job")
                self.stdout.write(
                    f"  - {title} | Chroma distance: {distance} | Job UUID: {job_id}"
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed and recommendation test completed."))

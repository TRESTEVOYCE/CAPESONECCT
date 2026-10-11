
import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from AdminSide.models import (
    User,
    SpecialProgramForEmploymentOfStudents,
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    CareerGuidanceBeneficiary,
    PESOActivities,
)


FIRST_NAMES = [
    "Juan", "Maria", "Jose", "Ana", "Mark", "Angel",
    "Carlo", "Sofia", "Miguel", "Grace", "Paolo",
    "Angela", "Rafael", "Nicole", "Daniel", "Andrea",
    "Christian", "Patricia", "Joshua", "Camille",
]

LAST_NAMES = [
    "Santos", "Reyes", "Cruz", "Garcia", "Mendoza",
    "Ramos", "Flores", "Castillo", "Dela Cruz", "Bautista",
    "Villanueva", "Aquino", "Gonzales", "Fernandez",
    "Rivera", "Torres", "Navarro", "Perez",
]

MIDDLE_NAMES = [
    "Lopez", "Garcia", "Reyes", "Dizon", "Ramos",
    "Santiago", "Morales", "Aquino", "Rivera",
]

BARANGAYS = [
    "Poblacion", "San Isidro", "San Roque", "Santa Cruz",
    "San Miguel", "San Antonio", "Bagong Silang",
    "Maligaya", " Mabini", "Del Pilar",
]

MUNICIPALITIES = [
    "Cebu City", "Talisay City", "Minglanilla",
    "Naga City", "Carcar City", "Consolacion",
    "Liloan", "Compostela", "Cordova",
]

PROVINCE = "Cebu"
REGION = "Central Visayas"

SCHOOLS = [
    "Cebu National High School",
    "University of Cebu",
    "Cebu Technological University",
    "University of the Visayas",
    "Southwestern University PHINMA",
    "Cebu Institute of Technology - University",
]

COLLEGE_PROGRAMS = [
    "Information Technology",
    "Computer Science",
    "Business Administration",
    "Education",
    "Accountancy",
    "Hospitality Management",
    "Criminology",
    "Engineering",
]

AGENCIES = [
    "City Government Office",
    "Municipal Planning Office",
    "Public Employment Service Office",
    "Municipal Agriculture Office",
    "Community Development Office",
]

ACTIVITIES = [
    (
        "Career Guidance Seminar",
        "Career planning and employment preparation seminar.",
    ),
    (
        "Labor Market Information Orientation",
        "Orientation on current labor market trends and opportunities.",
    ),
    (
        "Job Readiness Workshop",
        "Workshop covering resumes, interviews, and workplace readiness.",
    ),
    (
        "Employment Coaching Session",
        "Career coaching and employment counseling for participants.",
    ),
    (
        "Pre-Employment Seminar",
        "Seminar on workplace expectations and pre-employment requirements.",
    ),
]


def random_date(start, end):
    """Return a random date between start and end, inclusive."""
    days = (end - start).days
    return start + timedelta(days=random.randint(0, max(days, 0)))


def random_phone():
    return f"09{random.randint(100000000, 999999999)}"


def random_address():
    return {
        "barangay": random.choice(BARANGAYS).strip(),
        "municipality": random.choice(MUNICIPALITIES),
        "province": PROVINCE,
        "region": REGION,
        "zip_code": str(random.choice([6000, 6014, 6035, 6037, 6045])),
    }


class Command(BaseCommand):
    help = "Seed development data for beneficiary programs and PESO activities."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of records to create for each beneficiary program.",
        )
        parser.add_argument(
            "--activities",
            type=int,
            default=10,
            help="Number of PESO activities to create.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Optional random seed for reproducible data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        activity_count = options["activities"]

        if count < 0 or activity_count < 0:
            self.stderr.write(
                self.style.ERROR("Counts must be zero or greater.")
            )
            return

        if options["seed"] is not None:
            random.seed(options["seed"])

        today = timezone.localdate()
        start_range = today - timedelta(days=730)
        end_range = today + timedelta(days=365)

        created = {}

        def beneficiary_data():
            start_date = random_date(start_range, today)
            end_date = start_date + timedelta(
                days=random.randint(10, 180)
            )
            address = random_address()

            return {
                "first_name": random.choice(FIRST_NAMES),
                "middle_name": random.choice(MIDDLE_NAMES),
                "last_name": random.choice(LAST_NAMES),
                "sex": random.choice(["M", "F"]),
                "date_of_birth": random_date(
                    date(1985, 1, 1),
                    date(2008, 12, 31),
                ),
                "phone_number": random_phone(),
                **address,
                "daily_salary": Decimal(
                    str(random.randrange(40000, 80001) / 100)
                ).quantize(Decimal("0.01")),
                "start_date": start_date,
                "end_date": end_date,
                "is_done": end_date < today,
            }

        # SPES beneficiaries
        for _ in range(count):
            SpecialProgramForEmploymentOfStudents.objects.create(
                **beneficiary_data(),
                education_level=random.choice([
                    "elementary",
                    "juniors_hs",
                    "senior_hs",
                    "college",
                    "tech_voc",
                ]),
                is_out_of_school_youth=random.choice([True, False]),
                has_graduated=random.choice([True, False]),
                has_nc_certification=random.choice([True, False]),
                is_absorbed_by_employer=random.choice([True, False]),
                school_name=random.choice(SCHOOLS),
                college_program=random.choice(COLLEGE_PROGRAMS),
            )

        created["SPES"] = count

        # Government Internship Program beneficiaries
        for _ in range(count):
            GovernmentInternshipProgram.objects.create(
                **beneficiary_data(),
                education_level=random.choice([
                    "als",
                    "juniors_hs",
                    "senior_hs",
                    "tech_voc",
                    "college",
                ]),
                has_nc_certification=random.choice([True, False]),
                is_absorbed_by_agency=random.choice([True, False]),
            )

        created["GIP"] = count

        # TUPAD beneficiaries
        for _ in range(count):
            TupadBeneficiary.objects.create(
                **beneficiary_data(),
                project_type=random.choice(["short", "long"]),
                project_name=random.choice([
                    "Community Cleanup",
                    "Drainage Maintenance",
                    "Roadside Clearing",
                    "Public Facility Maintenance",
                    "Community Gardening",
                ]),
            )

        created["TUPAD"] = count

        # DILP beneficiaries
        for _ in range(count):
            DisplacedInformalLaborProgram.objects.create(
                **beneficiary_data(),
                project_category=random.choice([
                    "individual", "group"
                ]),
                project_classification=random.choice([
                    "formation",
                    "enhancement",
                    "restoration",
                ]),
            )

        created["DILP"] = count

        # Career Guidance beneficiaries
        for _ in range(count):
            CareerGuidanceBeneficiary.objects.create(
                **beneficiary_data(),
                participant_category=random.choice([
                    "juniors_hs",
                    "senior_hs",
                    "college",
                    "tech_voc",
                    "osy",
                    "jobseeker",
                ]),
                activity_type=random.choice([
                    "orientation",
                    "coaching",
                    "lmi_briefing",
                    "pre_employment",
                ]),
                school_or_institution=random.choice(SCHOOLS),
                preferred_curriculum_exit=random.choice([
                    "higher_ed",
                    "employment",
                    "entrepreneurship",
                    "skills_dev",
                    "undecided",
                ]),
                conducted_date=random_date(start_range, today),
                has_received_lmi_materials=random.choice([True, False]),
            )

        created["Career Guidance"] = count

        # PESO activities require an existing User foreign key.
        users = list(User.objects.all())

        if users:
            for _ in range(activity_count):
                activity_name, description = random.choice(ACTIVITIES)
                activity_date = random_date(start_range, end_range)

                PESOActivities.objects.create(
                    activity_name=activity_name,
                    activity_description=description,
                    number_of_participants=random.randint(10, 250),
                    activity_date=activity_date,
                    activity_time=time(
                        hour=random.randint(8, 16),
                        minute=random.choice([0, 15, 30, 45]),
                    ),
                    activity_location=(
                        f"{random.choice(BARANGAYS)}, "
                        f"{random.choice(MUNICIPALITIES)}, Cebu"
                    ),
                    organizer=random.choice(AGENCIES),
                    added_by=random.choice(users),
                )

            created["PESO Activities"] = activity_count
        else:
            created["PESO Activities"] = 0
            self.stdout.write(
                self.style.WARNING(
                    "No User records found. PESO activities were skipped "
                    "because added_by requires an existing user."
                )
            )

        self.stdout.write(self.style.SUCCESS(
            "Development seed data created successfully:"
        ))

        for label, amount in created.items():
            self.stdout.write(f"  {label}: {amount}")

        self.stdout.write(
            f"  Total created: {sum(created.values())}"
        )

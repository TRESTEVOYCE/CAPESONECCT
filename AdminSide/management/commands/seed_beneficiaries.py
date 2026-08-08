import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from AdminSide.models import (
    SpecialProgramForEmploymentOfStudents,
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    CareerGuidanceBeneficiary,
)


class Command(BaseCommand):
    help = "Generate sample beneficiary data for all programs."

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            help="Number of beneficiaries to create per program.",
        )

    def handle(self, *args, **options):
        count = options["count"]

        if count <= 0:
            self.stdout.write(
                self.style.ERROR("Count must be greater than 0.")
            )
            return

        fake = Faker("en_PH")

        self.stdout.write(
            self.style.WARNING(
                f"Creating {count} records for each of 5 programs..."
            )
        )

        self.create_spes(fake, count)
        self.create_gip(fake, count)
        self.create_tupad(fake, count)
        self.create_dilp(fake, count)
        self.create_career_guidance(fake, count)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {count * 5:,} beneficiaries."
            )
        )

    # ---------------------------------------------------------
    # Common beneficiary data
    # ---------------------------------------------------------

    def common_data(self, fake):
        sex = random.choice(["M", "F"])

        first_name = (
            fake.first_name_male()
            if sex == "M"
            else fake.first_name_female()
        )

        middle_name = fake.first_name()
        last_name = fake.last_name()

        dob = fake.date_of_birth(
            minimum_age=10,
            maximum_age=65,
        )

        start_date = fake.date_between(
            start_date="-2y",
            end_date="today",
        )

        duration = random.randint(10, 90)
        end_date = start_date + timedelta(days=duration)

        return {
            "uuid": uuid.uuid4(),
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "sex": sex,
            "date_of_birth": dob,
            "phone_number": self.philippine_phone(),
            "barangay": fake.random_element([
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
            "municipality": fake.random_element([
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
            "province": "Leyte",
            "region": "Eastern Visayas",
            "zip_code": random.choice([
                "6500",
                "6501",
                "6502",
                "6503",
                "6504",
                "6505",
            ]),
            "daily_salary": random.randint(400, 1000),
            "start_date": start_date,
            "end_date": end_date,
            "is_done": end_date < timezone.localdate(),
        }

    def philippine_phone(self):
        return f"09{random.randint(10, 99)}{random.randint(1000000, 9999999)}"

    # ---------------------------------------------------------
    # SPES
    # ---------------------------------------------------------

    def create_spes(self, fake, count):
        education_levels = [
            "elementary",
            "juniors_hs",
            "senior_hs",
            "college",
            "tech_voc",
        ]

        records = []

        for _ in range(count):
            data = self.common_data(fake)

            education = random.choice(education_levels)

            records.append(
                SpecialProgramForEmploymentOfStudents(
                    **data,
                    education_level=education,
                    is_out_of_school_youth=random.choice([
                        True, False
                    ]),
                    has_graduated=random.choice([
                        True, False
                    ]),
                    has_nc_certification=random.choice([
                        True, False
                    ]),
                    is_absorbed_by_employer=random.choice([
                        True, False
                    ]),
                    school_name=random.choice([
                        "Eastern Visayas State University",
                        "Leyte National High School",
                        "Tacloban City National High School",
                        "University of the Philippines Visayas Tacloban",
                        "ACLC College Tacloban",
                        "AMA Computer College Tacloban",
                        "TESDA Regional Training Center",
                    ]),
                    college_program=(
                        random.choice([
                            "BS Information Technology",
                            "BS Computer Science",
                            "BS Business Administration",
                            "BS Education",
                            "BS Accountancy",
                            "BS Hospitality Management",
                        ])
                        if education == "college"
                        else None
                    ),
                )
            )

        SpecialProgramForEmploymentOfStudents.objects.bulk_create(
            records,
            batch_size=1000,
        )

        self.stdout.write(
            f"  SPES: {count:,} records"
        )

    # ---------------------------------------------------------
    # GIP
    # ---------------------------------------------------------

    def create_gip(self, fake, count):
        education_levels = [
            "als",
            "juniors_hs",
            "senior_hs",
            "tech_voc",
            "college",
        ]

        records = []

        for _ in range(count):
            data = self.common_data(fake)

            records.append(
                GovernmentInternshipProgram(
                    **data,
                    education_level=random.choice(
                        education_levels
                    ),
                    has_nc_certification=random.choice([
                        True, False
                    ]),
                    is_absorbed_by_agency=random.choice([
                        True, False
                    ]),
                )
            )

        GovernmentInternshipProgram.objects.bulk_create(
            records,
            batch_size=1000,
        )

        self.stdout.write(
            f"  GIP: {count:,} records"
        )

    # ---------------------------------------------------------
    # TUPAD
    # ---------------------------------------------------------

    def create_tupad(self, fake, count):
        records = []

        projects = [
            "Road Cleaning and Maintenance",
            "Community Beautification",
            "Drainage Cleaning",
            "Public Facility Maintenance",
            "Coastal Clean-up",
            "Barangay Road Maintenance",
            "Tree Planting",
            "Community Clean-up",
        ]

        for _ in range(count):
            data = self.common_data(fake)

            project_type = random.choice([
                "short",
                "long",
            ])

            records.append(
                TupadBeneficiary(
                    **data,
                    project_type=project_type,
                    project_name=random.choice(projects),
                )
            )

        TupadBeneficiary.objects.bulk_create(
            records,
            batch_size=1000,
        )

        self.stdout.write(
            f"  TUPAD: {count:,} records"
        )

    # ---------------------------------------------------------
    # DILP
    # ---------------------------------------------------------

    def create_dilp(self, fake, count):
        records = []

        for _ in range(count):
            data = self.common_data(fake)

            records.append(
                DisplacedInformalLaborProgram(
                    **data,
                    project_category=random.choice([
                        "individual",
                        "group",
                    ]),
                    project_classification=random.choice([
                        "formation",
                        "enhancement",
                        "restoration",
                    ]),
                )
            )

        DisplacedInformalLaborProgram.objects.bulk_create(
            records,
            batch_size=1000,
        )

        self.stdout.write(
            f"  DILP: {count:,} records"
        )

    # ---------------------------------------------------------
    # Career Guidance
    # ---------------------------------------------------------

    def create_career_guidance(self, fake, count):
        records = []

        participant_types = [
            "juniors_hs",
            "senior_hs",
            "college",
            "tech_voc",
            "osy",
            "jobseeker",
        ]

        activity_types = [
            "orientation",
            "coaching",
            "lmi_briefing",
            "pre_employment",
        ]

        curriculum_exits = [
            "higher_ed",
            "employment",
            "entrepreneurship",
            "skills_dev",
            "undecided",
        ]

        institutions = [
            "Eastern Visayas State University",
            "Leyte National High School",
            "Tacloban City National High School",
            "University of the Philippines Visayas Tacloban",
            "TESDA Regional Training Center",
            "ACLC College Tacloban",
            "AMA Computer College Tacloban",
        ]

        for _ in range(count):
            data = self.common_data(fake)

            participant_type = random.choice(
                participant_types
            )

            conducted_date = fake.date_between(
                start_date="-2y",
                end_date="today",
            )

            records.append(
                CareerGuidanceBeneficiary(
                    **data,
                    participant_category=participant_type,
                    activity_type=random.choice(
                        activity_types
                    ),
                    school_or_institution=(
                        random.choice(institutions)
                        if participant_type != "jobseeker"
                        else None
                    ),
                    preferred_curriculum_exit=random.choice(
                        curriculum_exits
                    ),
                    conducted_date=conducted_date,
                    has_received_lmi_materials=random.choice([
                        True,
                        True,
                        True,
                        False,
                    ]),
                )
            )

        CareerGuidanceBeneficiary.objects.bulk_create(
            records,
            batch_size=1000,
        )

        self.stdout.write(
            f"  Career Guidance: {count:,} records"
        )
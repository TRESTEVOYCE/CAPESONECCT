import random
import uuid
from datetime import timedelta

from faker import Faker
from django.core.management.base import BaseCommand

from AdminSide.models import (
    User,
    SpecialProgramForEmploymentOfStudents,
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    CareerGuidanceBeneficiary,
    PESOActivities,
    AuditLog,
)


class Command(BaseCommand):
    help = "Generate fake data for PESO beneficiary and activity models."

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            help="Number of fake records to create for each model.",
        )

    def handle(self, *args, **options):

        count = options["count"]

        fake = Faker("en_PH")

        self.stdout.write(
            self.style.WARNING(
                f"Creating {count} fake records for each model..."
            )
        )

        # =========================================================
        # USERS
        # =========================================================

        users = list(User.objects.all())

        if not users:
            user = User.objects.create_user(
                username="fake_peso_admin",
                email="fakepeso@example.com",
                password="password123",
                role="peso",
            )

            users.append(user)

            self.stdout.write(
                self.style.WARNING(
                    "No users found. Created fake_peso_admin."
                )
            )

        # =========================================================
        # PHILIPPINE LOCATION DATA
        # =========================================================

        locations = [
            {
                "barangay": "San Antonio",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Abucay",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Anibong",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Bagacay",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Can-abay",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Palanog",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "San Jose",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Sagkahan",
                "municipality": "Tacloban City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6500",
            },
            {
                "barangay": "Bagong Lipunan",
                "municipality": "Calbayog City",
                "province": "Samar",
                "region": "Region VIII",
                "zip_code": "6710",
            },
            {
                "barangay": "Central",
                "municipality": "Calbayog City",
                "province": "Samar",
                "region": "Region VIII",
                "zip_code": "6710",
            },
            {
                "barangay": "Cag-olango",
                "municipality": "Ormoc City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6541",
            },
            {
                "barangay": "Linao",
                "municipality": "Ormoc City",
                "province": "Leyte",
                "region": "Region VIII",
                "zip_code": "6541",
            },
            {
                "barangay": "Airport",
                "municipality": "Cebu City",
                "province": "Cebu",
                "region": "Region VII",
                "zip_code": "6000",
            },
            {
                "barangay": "Lahug",
                "municipality": "Cebu City",
                "province": "Cebu",
                "region": "Region VII",
                "zip_code": "6000",
            },
            {
                "barangay": "Guadalupe",
                "municipality": "Cebu City",
                "province": "Cebu",
                "region": "Region VII",
                "zip_code": "6000",
            },
            {
                "barangay": "Poblacion",
                "municipality": "Makati City",
                "province": "Metro Manila",
                "region": "NCR",
                "zip_code": "1200",
            },
            {
                "barangay": "Bel-Air",
                "municipality": "Makati City",
                "province": "Metro Manila",
                "region": "NCR",
                "zip_code": "1209",
            },
            {
                "barangay": "San Lorenzo",
                "municipality": "Makati City",
                "province": "Metro Manila",
                "region": "NCR",
                "zip_code": "1223",
            },
        ]

        # =========================================================
        # COMMON BENEFICIARY DATA
        # =========================================================

        def generate_phone_number():
            """
            Generates a Philippine-style mobile number.

            Example:
            09171234567
            """

            prefixes = [
                "0905",
                "0906",
                "0907",
                "0908",
                "0909",
                "0910",
                "0912",
                "0915",
                "0916",
                "0917",
                "0918",
                "0919",
                "0920",
                "0921",
                "0922",
                "0923",
                "0924",
                "0925",
                "0926",
                "0927",
                "0928",
                "0929",
                "0930",
                "0935",
                "0936",
                "0937",
                "0938",
                "0939",
                "0945",
                "0950",
                "0951",
                "0953",
                "0954",
                "0955",
                "0956",
                "0960",
                "0961",
                "0965",
                "0966",
                "0967",
                "0968",
                "0970",
                "0975",
                "0977",
                "0978",
                "0979",
                "0981",
                "0985",
                "0989",
                "0991",
                "0992",
                "0993",
                "0994",
                "0995",
                "0996",
                "0997",
            ]

            prefix = random.choice(prefixes)

            return prefix + "".join(
                str(random.randint(0, 9))
                for _ in range(7)
            )

        def beneficiary_data():

            sex = random.choice(["M", "F"])

            if sex == "M":
                first_name = fake.first_name_male()
            else:
                first_name = fake.first_name_female()

            location = random.choice(locations)

            date_of_birth = fake.date_of_birth(
                minimum_age=18,
                maximum_age=60,
            )

            start_date = fake.date_between(
                start_date="-1y",
                end_date="today",
            )

            duration = random.randint(10, 90)

            end_date = start_date + timedelta(
                days=duration
            )

            return {
                "uuid": uuid.uuid4(),

                "first_name": first_name,

                "middle_name": fake.first_name(),

                "last_name": fake.last_name(),

                "sex": sex,

                "date_of_birth": date_of_birth,

                "phone_number": generate_phone_number(),

                "barangay": location["barangay"],

                "municipality": location["municipality"],

                "province": location["province"],

                "region": location["region"],

                "zip_code": location["zip_code"],

                "daily_salary": random.randint(
                    400,
                    800,
                ),

                "start_date": start_date,

                "end_date": end_date,

                "is_done": random.choice([
                    True,
                    False,
                ]),
            }

        # =========================================================
        # SPES
        # =========================================================

        spes_records = []

        for _ in range(count):

            data = beneficiary_data()

            education = random.choice([
                "elementary",
                "juniors_hs",
                "senior_hs",
                "college",
                "tech_voc",
            ])

            record = (
                SpecialProgramForEmploymentOfStudents.objects.create(
                    **data,

                    education_level=education,

                    is_out_of_school_youth=random.choice([
                        True,
                        False,
                    ]),

                    has_graduated=random.choice([
                        True,
                        False,
                    ]),

                    has_nc_certification=random.choice([
                        True,
                        False,
                    ]),

                    is_absorbed_by_employer=random.choice([
                        True,
                        False,
                    ]),

                    school_name=(
                        fake.company()
                        if education in [
                            "juniors_hs",
                            "senior_hs",
                            "college",
                            "tech_voc",
                        ]
                        else None
                    ),

                    college_program=(
                        random.choice([
                            "Bachelor of Science in Information Technology",
                            "Bachelor of Science in Computer Science",
                            "Bachelor of Science in Business Administration",
                            "Bachelor of Science in Education",
                            "Bachelor of Science in Agriculture",
                            "Bachelor of Science in Nursing",
                        ])
                        if education == "college"
                        else None
                    ),
                )
            )

            spes_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(spes_records)} SPES beneficiaries."
            )
        )

        # =========================================================
        # GIP
        # =========================================================

        gip_records = []

        for _ in range(count):

            data = beneficiary_data()

            education = random.choice([
                "als",
                "juniors_hs",
                "senior_hs",
                "tech_voc",
                "college",
            ])

            record = GovernmentInternshipProgram.objects.create(
                **data,

                education_level=education,

                has_nc_certification=random.choice([
                    True,
                    False,
                ]),

                is_absorbed_by_agency=random.choice([
                    True,
                    False,
                ]),
            )

            gip_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(gip_records)} GIP beneficiaries."
            )
        )

        # =========================================================
        # TUPAD
        # =========================================================

        tupad_records = []

        tupad_projects = [
            "Community Cleanup",
            "Road Maintenance",
            "Drainage Improvement",
            "Barangay Beautification",
            "Public Facility Maintenance",
            "Environmental Cleanup",
            "Canal Cleaning",
            "Public Market Cleanup",
            "Tree Planting",
            "Coastal Cleanup",
        ]

        for _ in range(count):

            data = beneficiary_data()

            project_type = random.choice([
                "short",
                "long",
            ])

            record = TupadBeneficiary.objects.create(
                **data,

                project_type=project_type,

                project_name=random.choice(
                    tupad_projects
                ),
            )

            tupad_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(tupad_records)} TUPAD beneficiaries."
            )
        )

        # =========================================================
        # DILP
        # =========================================================

        dilp_records = []

        for _ in range(count):

            data = beneficiary_data()

            record = DisplacedInformalLaborProgram.objects.create(
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

            dilp_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(dilp_records)} DILP beneficiaries."
            )
        )

        # =========================================================
        # CAREER GUIDANCE
        # =========================================================

        career_records = []

        for _ in range(count):

            data = beneficiary_data()

            participant_category = random.choice([
                "juniors_hs",
                "senior_hs",
                "college",
                "tech_voc",
                "osy",
                "jobseeker",
            ])

            school_or_institution = None

            if participant_category in [
                "juniors_hs",
                "senior_hs",
                "college",
                "tech_voc",
            ]:
                school_or_institution = random.choice([
                    "Eastern Visayas State University",
                    "Leyte National High School",
                    "Tacloban National Agricultural College",
                    "University of the Philippines Visayas",
                    "Visayas State University",
                    "Leyte Normal University",
                    "TESDA Training Center",
                ])

            record = CareerGuidanceBeneficiary.objects.create(
                **data,

                participant_category=participant_category,

                activity_type=random.choice([
                    "orientation",
                    "coaching",
                    "lmi_briefing",
                    "pre_employment",
                ]),

                school_or_institution=school_or_institution,

                preferred_curriculum_exit=random.choice([
                    "higher_ed",
                    "employment",
                    "entrepreneurship",
                    "skills_dev",
                    "undecided",
                ]),

                conducted_date=fake.date_between(
                    start_date="-1y",
                    end_date="today",
                ),

                has_received_lmi_materials=random.choice([
                    True,
                    False,
                ]),
            )

            career_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(career_records)} Career Guidance beneficiaries."
            )
        )

        # =========================================================
        # PESO ACTIVITIES
        # =========================================================

        activity_records = []

        activity_names = [
            "Job Fair",
            "Career Guidance Seminar",
            "Employment Coaching",
            "Livelihood Orientation",
            "Job Matching Activity",
            "Labor Market Information Seminar",
            "Pre-Employment Seminar",
            "Skills Training",
            "Career Advocacy Program",
            "Local Recruitment Activity",
            "Career Expo",
        ]

        organizers = [
            "PESO Office",
            "DOLE",
            "Local Government Unit",
            "Barangay Council",
            "Public Employment Service Office",
            "TESDA",
            "Local Government Unit - PESO",
        ]

        activity_locations = [
            "PESO Office",
            "Municipal Hall",
            "Barangay Hall",
            "City Hall",
            "Community Center",
            "Public School",
            "Covered Court",
            "Convention Center",
            "Training Center",
        ]

        for _ in range(count):

            activity_date = fake.date_between(
                start_date="-1y",
                end_date="+6m",
            )

            record = PESOActivities.objects.create(
                uuid=uuid.uuid4(),

                activity_name=random.choice(
                    activity_names
                ),

                activity_description=fake.paragraph(
                    nb_sentences=3
                ),

                number_of_participants=random.randint(
                    10,
                    500,
                ),

                activity_date=activity_date,

                activity_time=fake.time_object(),

                activity_location=random.choice(
                    activity_locations
                ),

                organizer=random.choice(
                    organizers
                ),

                added_by=random.choice(
                    users
                ),
            )

            activity_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(activity_records)} PESO activities."
            )
        )

        # =========================================================
        # AUDIT LOGS
        # =========================================================

        audit_records = []

        actions = [
            "Created beneficiary record",
            "Updated beneficiary information",
            "Viewed beneficiary record",
            "Created PESO activity",
            "Updated PESO activity",
            "Generated beneficiary report",
            "Exported beneficiary data",
            "Viewed dashboard",
            "Logged in",
            "Logged out",
            "Viewed beneficiary list",
            "Searched beneficiary records",
        ]

        for _ in range(count):

            record = AuditLog.objects.create(
                uuid=uuid.uuid4(),

                user=random.choice(users),

                action=random.choice(actions),
            )

            audit_records.append(record)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(audit_records)} audit logs."
            )
        )

        # =========================================================
        # SUMMARY
        # =========================================================

        total_records = count * 7

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "=========================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Fake data generation completed successfully!"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Records created: {total_records}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "=========================================="
            )
        )
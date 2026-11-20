
from .config import chroma_client, get_embedding_function


# ============================================================
# SKILL FIELD DEFINITIONS
# ============================================================

SKILL_FIELDS = {
    # 21st Century / Functional Skills
    "skill_innovation": "Innovation",
    "skill_team_work": "Teamwork",
    "skill_multitasking": "Multitasking",
    "skill_work_ethics": "Work Ethics",
    "skill_self_motivation": "Self Motivation",
    "skill_creative_problem_solving": "Creative Problem Solving",
    "skill_problem_solving": "Problem Solving",
    "skill_critical_thinking": "Critical Thinking",
    "skill_decision_making": "Decision Making",
    "skill_stress_tolerance": "Stress Tolerance",
    "skill_planning_organizing": "Planning and Organizing",
    "skill_social_perceptiveness": "Social Perceptiveness",
    "skill_english_functional": "Functional English",
    "skill_english_comprehension": "English Comprehension",
    "skill_math_functional": "Functional Mathematics",

    # Technical Skills
    "skill_carpentry": "Carpentry",
    "skill_masonry": "Masonry",
    "skill_welding": "Welding",
    "skill_auto_mechanic": "Automotive Mechanic",
    "skill_plumbing": "Plumbing",
    "skill_driving": "Driving",
    "skill_gardening": "Gardening",
    "skill_tailoring": "Tailoring",
    "skill_photography": "Photography",
    "skill_hairdressing": "Hairdressing",
    "skill_cooking": "Cooking",
    "skill_baking": "Baking",
}


APPLICANT_EXTRA_SKILLS = {
    "skill_computer": "Computer Skills",
    "skill_customer_service": "Customer Service",
    "skill_bookkeeping": "Bookkeeping",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_text(value):
    """
    Converts values into safe, searchable text.
    """
    if value is None:
        return ""

    return str(value).strip()


def get_selected_boolean_skills(instance, fields):
    """
    Gets selected Boolean skill fields from a model instance.
    """

    selected = []

    for field_name, label in fields.items():
        if getattr(instance, field_name, False):
            selected.append(label)

    return selected


def get_applicant_default_skills(applicant):
    """
    Gets the applicant's selected default and additional skills.
    """

    skills = get_selected_boolean_skills(
        applicant,
        SKILL_FIELDS
    )

    skills.extend(
        get_selected_boolean_skills(
            applicant,
            APPLICANT_EXTRA_SKILLS
        )
    )

    return skills


def get_job_default_skills(job):
    """
    Gets the employer's selected Boolean skill requirements.
    """

    return get_selected_boolean_skills(
        job,
        SKILL_FIELDS
    )


def get_applicant_custom_skills(applicant):
    """
    Gets applicant custom skills from ApplicantSkills.
    """

    return [
        clean_text(skill)
        for skill in applicant.skills.values_list(
            "skill_name",
            flat=True
        )
        if clean_text(skill)
    ]


def get_job_custom_skills(job):
    """
    Gets employer-defined skills from JobSkills.
    """

    return [
        clean_text(skill)
        for skill in job.custom_skills.values_list(
            "skill_name",
            flat=True
        )
        if clean_text(skill)
    ]


def get_applicant_skills(applicant):
    """
    Combines applicant Boolean skills and custom skills.
    """

    skills = (
        get_applicant_default_skills(applicant)
        + get_applicant_custom_skills(applicant)
    )

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(skills))


def get_job_required_skills(job):
    """
    Combines job Boolean skill requirements and custom skills.
    """

    skills = (
        get_job_default_skills(job)
        + get_job_custom_skills(job)
    )

    return list(dict.fromkeys(skills))


# ============================================================
# CHROMADB COLLECTION
# ============================================================

def get_job_collection():
    """
    Gets or creates the ChromaDB collection used for job matching.
    """

    return chroma_client.get_or_create_collection(
        name="job_postings",
        embedding_function=get_embedding_function()
    )


# ============================================================
# APPLICANT EDUCATION
# ============================================================

def get_applicant_education(applicant):
    """
    Gets the applicant's education information.

    Uses both the education_level field and the detailed
    education Boolean fields.
    """

    education_labels = {
        "edu_no_formal": "No Formal Education",
        "edu_elem_level": "Elementary Level",
        "edu_elem_grad": "Elementary Graduate",
        "edu_hs_level": "High School Level",
        "edu_hs_grad": "High School Graduate",
        "edu_college_level": "College Level",
        "edu_college_grad": "College Graduate",
        "edu_tech_voc": "Technical Vocational",
        "edu_post_grad": "Postgraduate",
    }

    selected_education = []

    for field_name, label in education_labels.items():
        if getattr(applicant, field_name, False):
            selected_education.append(label)

    education_level = clean_text(
        getattr(applicant, "education_level", "")
    )

    school = clean_text(
        getattr(applicant, "school_name", "")
    )

    school_university = clean_text(
        getattr(applicant, "school_university", "")
    )

    course = clean_text(
        getattr(applicant, "course_program", "")
    )

    year_graduated = clean_text(
        getattr(applicant, "year_graduated", "")
    )

    year_attended = clean_text(
        getattr(applicant, "year_graduated_attended", "")
    )

    awards = []

    for field in ["award_1", "award_2", "award_3"]:
        award = clean_text(getattr(applicant, field, ""))

        if award:
            awards.append(award)

    return {
        "education_level": education_level,
        "selected_education": selected_education,
        "school": school or school_university,
        "course": course,
        "year": year_graduated or year_attended,
        "awards": awards,
    }


# ============================================================
# APPLICANT TRAINING
# ============================================================

def get_applicant_training_text(applicant):
    """
    Gets the applicant's training records.
    """

    training_records = []

    for training in applicant.trainings.all():

        details = [
            clean_text(training.training_title),
            clean_text(training.training_institution),
            (
                f"{training.training_hours} hours"
                if training.training_hours is not None
                else ""
            ),
            clean_text(training.training_date),
        ]

        details = [item for item in details if item]

        if details:
            training_records.append(" - ".join(details))

    return training_records


# ============================================================
# APPLICANT WORK EXPERIENCE
# ============================================================

def get_applicant_work_experience_text(applicant):
    """
    Gets the applicant's work experience records.

    Dates are retained as text because the model stores them
    as free-text values.
    """

    work_records = []

    for experience in applicant.work_experiences.all():

        details = [
            clean_text(experience.position),
            clean_text(experience.company),
            clean_text(experience.address),
            clean_text(experience.dates),
            clean_text(experience.status),
        ]

        details = [item for item in details if item]

        if details:
            work_records.append(" - ".join(details))

    return work_records


# ============================================================
# JOB DOCUMENT BUILDER
# ============================================================

def build_job_text(job):
    """
    Converts a Jobs instance into searchable text.

    Includes:
    - Job details
    - Education requirements
    - Experience requirements
    - Required skills
    - Custom skills
    - Employer information
    """

    required_skills = get_job_required_skills(job)

    employer = job.employer

    return f"""
JOB POSTING

Job Title:
{clean_text(job.job_title)}

Job Description:
{clean_text(job.job_description)}

Nature of Work:
{clean_text(job.get_nature_of_work_display())}

Place of Work:
{clean_text(job.place_of_work)}

Salary:
{clean_text(job.salary)}

Number of Vacancies:
{clean_text(job.vacancy)}

EDUCATIONAL REQUIREMENTS

Educational Level:
{clean_text(job.educational_level)}

Course or Strand:
{clean_text(job.course_or_strand)}

Required License:
{clean_text(job.required_license)}

Required Eligibility:
{clean_text(job.required_eligibility)}

Required Certification:
{clean_text(job.required_certification)}

WORK EXPERIENCE

Required Experience:
{clean_text(job.work_experience_months)} months

Other Qualifications:
{clean_text(job.other_qualifications)}

REQUIRED SKILLS

{", ".join(required_skills)}

LANGUAGE REQUIREMENTS

Languages Spoken:
{clean_text(job.languages_spoken)}

SPECIAL EMPLOYMENT CONDITIONS

Accepts Persons with Disabilities:
{"Yes" if job.accepts_pwd else "No"}

PWD Disabilities Accepted:
{clean_text(job.pwd_disabilities)}

Accepts OFW:
{"Yes" if job.accepts_ofw else "No"}

EMPLOYER INFORMATION

Business Name:
{clean_text(employer.business_name)}

Industry:
{clean_text(employer.line_of_business)}

Municipality:
{clean_text(employer.municipality)}

Province:
{clean_text(employer.province)}
"""


# ============================================================
# APPLICANT DOCUMENT BUILDER
# ============================================================

def build_applicant_profile_text(applicant):
    """
    Converts an ApplicantProfile instance into searchable text.

    Includes:
    - Applicant skills
    - Education
    - Training
    - Work experience
    - Preferred jobs
    - Employment preferences
    - Location
    """

    skills = get_applicant_skills(applicant)

    education = get_applicant_education(applicant)

    trainings = get_applicant_training_text(applicant)

    work_experience = get_applicant_work_experience_text(
        applicant
    )

    preferred_jobs = [
        clean_text(title)
        for title in applicant.preferred_job.values_list(
            "job_title",
            flat=True
        )
        if clean_text(title)
    ]

    preferred_occupations = [
        clean_text(getattr(applicant, field, ""))
        for field in [
            "pref_occupation_1",
            "pref_occupation_2",
            "pref_occupation_3",
        ]
        if clean_text(getattr(applicant, field, ""))
    ]

    employment_status = (
        applicant.get_employment_status_display()
        if hasattr(applicant, "get_employment_status_display")
        else clean_text(applicant.employment_status)
    )

    return f"""
APPLICANT PROFILE

Employment Status:
{employment_status}

Actively Looking for Work:
{"Yes" if applicant.actively_looking else "No"}

Expected Salary:
{clean_text(applicant.expected_salary)}

EDUCATIONAL BACKGROUND

Education Level:
{education["education_level"]}

Detailed Educational Attainment:
{", ".join(education["selected_education"])}

School:
{education["school"]}

Course or Program:
{education["course"]}

Year Graduated or Attended:
{education["year"]}

Awards and Achievements:
{", ".join(education["awards"])}

SKILLS

{", ".join(skills)}

TRAINING AND CERTIFICATIONS

{"; ".join(trainings)}

WORK EXPERIENCE

{"; ".join(work_experience)}

JOB PREFERENCES

Preferred Occupations:
{", ".join(preferred_occupations)}

Preferred Jobs:
{", ".join(preferred_jobs)}

Local Employment Preference:
{"Yes" if applicant.pref_local else "No"}

Overseas Employment Preference:
{"Yes" if applicant.pref_overseas else "No"}

Preferred Local Location:
{clean_text(applicant.pref_location_local)}

Preferred Overseas Location:
{clean_text(applicant.pref_location_overseas)}

LOCATION

Municipality:
{clean_text(applicant.municipality)}

Province:
{clean_text(applicant.province)}

OTHER INFORMATION

OFW:
{"Yes" if applicant.is_ofw else "No"}

4Ps Beneficiary:
{"Yes" if applicant.is_4ps_beneficiary else "No"}
"""


# ============================================================
# UPSERT JOB VECTOR
# ============================================================

def upsert_job_vector(job):
    """
    Creates or updates a job embedding in ChromaDB.

    Call this whenever a job is created or updated.
    """

    collection = get_job_collection()

    document = build_job_text(job)

    employer = job.employer

    collection.upsert(
        ids=[str(job.uuid)],
        documents=[document],
        metadatas=[{
            "job_uuid": str(job.uuid),
            "title": clean_text(job.job_title),
            "status": clean_text(job.status),
            "nature_of_work": clean_text(job.nature_of_work),
            "salary": float(job.salary or 0),
            "employer": clean_text(employer.business_name),
            "municipality": clean_text(employer.municipality),
            "province": clean_text(employer.province),
            "accepts_pwd": bool(job.accepts_pwd),
            "accepts_ofw": bool(job.accepts_ofw),
        }]
    )


# ============================================================
# DELETE JOB VECTOR
# ============================================================

def delete_job_vector(job_uuid):
    """
    Removes a job embedding from ChromaDB.
    """

    collection = get_job_collection()

    collection.delete(
        ids=[str(job_uuid)]
    )


# ============================================================
# QUERY MATCHING JOBS
# ============================================================

def query_matching_jobs(applicant, total_results=10):
    """
    Finds semantically similar jobs using the applicant profile.

    This function performs ChromaDB retrieval only.
    Final skill scoring and ranking can be handled separately
    by JobMatchingEngine.job_matching.
    """

    collection = get_job_collection()

    if total_results <= 0:
        return {
            "ids": [],
            "distances": [],
            "metadatas": [],
            "documents": [],
        }

    collection_count = collection.count()

    if collection_count == 0:
        return {
            "ids": [],
            "distances": [],
            "metadatas": [],
            "documents": [],
        }

    profile_text = build_applicant_profile_text(applicant)

    results = collection.query(
        query_texts=[profile_text],
        n_results=min(total_results, collection_count),
        include=[
            "distances",
            "metadatas",
            "documents",
        ],
    )

    return {
        "ids": results.get("ids", [[]])[0],
        "distances": results.get("distances", [[]])[0],
        "metadatas": results.get("metadatas", [[]])[0],
        "documents": results.get("documents", [[]])[0],
    }

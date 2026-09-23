from .config import chroma_client, embedding_function


def get_job_collection():
    """
    Gets or creates the ChromaDB collection used for job matching.
    """
    return chroma_client.get_or_create_collection(
        name="job_postings",
        embedding_function=embedding_function
    )


def build_job_text(job):
    """
    Converts a Jobs instance into searchable text.
    """

    return f"""
    Job Title:
    {job.job_title}

    Job Description:
    {job.job_description}

    Nature of Work:
    {job.get_nature_of_work_display()}

    Place of Work:
    {job.place_of_work}

    Salary:
    {job.salary}

    Vacancies:
    {job.vacancy}

    Educational Level:
    {job.educational_level or ""}

    Course or Strand:
    {job.course_or_strand or ""}

    Required License:
    {job.required_license or ""}

    Required Eligibility:
    {job.required_eligibility or ""}

    Required Certification:
    {job.required_certification or ""}

    Languages Spoken:
    {job.languages_spoken or ""}

    Experience Required:
    {job.work_experience_months} months

    Other Qualifications:
    {job.other_qualifications or ""}

    Accepts PWD:
    {"Yes" if job.accepts_pwd else "No"}

    PWD Disabilities:
    {job.pwd_disabilities or ""}

    Accepts OFW:
    {"Yes" if job.accepts_ofw else "No"}

    Employer:
    {job.employer.business_name}

    Industry:
    {job.employer.line_of_business or ""}

    Municipality:
    {job.employer.municipality}

    Province:
    {job.employer.province}
    """


def upsert_job_vector(job):
    """
    Creates or updates a job embedding in ChromaDB.
    """

    collection = get_job_collection()

    document = build_job_text(job)

    collection.upsert(
        ids=[str(job.uuid)],
        documents=[document],
        metadatas=[{
            "job_uuid": str(job.uuid),
            "title": job.job_title,
            "status": job.status,
            "nature_of_work": job.nature_of_work,
            "salary": float(job.salary),
            "employer": job.employer.business_name,
            "municipality": job.employer.municipality,
            "province": job.employer.province,
            "accepts_pwd": job.accepts_pwd,
            "accepts_ofw": job.accepts_ofw,
        }]
    )


def delete_job_vector(job_uuid):
    """
    Removes a job embedding from ChromaDB.
    """

    collection = get_job_collection()

    collection.delete(
        ids=[str(job_uuid)]
    )


def build_applicant_profile_text(applicant):
    """
    Converts an ApplicantProfile instance into searchable text.
    """

    skills = ", ".join(
        applicant.skills.values_list(
            "skill_name",
            flat=True
        )
    )

    preferred_jobs = ", ".join(
        applicant.preferred_job.values_list(
            "job_title",
            flat=True
        )
    )

    return f"""
    Applicant Profile

    Education Level:
    {applicant.get_education_level_display()}

    School:
    {applicant.school_name or ""}

    Course / Program:
    {applicant.course_program or ""}

    Year Graduated:
    {applicant.year_graduated or ""}

    Employment Status:
    {applicant.get_employment_status_display()}

    Actively Looking For Work:
    {"Yes" if applicant.actively_looking else "No"}

    Expected Salary:
    {applicant.expected_salary}

    Skills:
    {skills}

    Preferred Jobs:
    {preferred_jobs}

    Municipality:
    {applicant.municipality}

    Province:
    {applicant.province}

    OFW:
    {"Yes" if applicant.is_ofw else "No"}

    4Ps Beneficiary:
    {"Yes" if applicant.is_4ps_beneficiary else "No"}
    """


def query_matching_jobs(applicant, total_results=10):
    """
    Finds jobs matching an applicant profile.
    """

    collection = get_job_collection()

    profile_text = build_applicant_profile_text(applicant)

    results = collection.query(
        query_texts=[profile_text],
        n_results=total_results
    )

    ids = (
        results.get("ids", [[]])[0]
        if results.get("ids")
        else []
    )

    distances = (
        results.get("distances", [[]])[0]
        if results.get("distances")
        else []
    )

    metadatas = (
        results.get("metadatas", [[]])[0]
        if results.get("metadatas")
        else []
    )

    documents = (
        results.get("documents", [[]])[0]
        if results.get("documents")
        else []
    )

    return {
        "ids": ids,
        "distances": distances,
        "metadatas": metadatas,
        "documents": documents,
    }
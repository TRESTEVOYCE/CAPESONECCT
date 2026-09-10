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
    Converts a Jobs model instance into searchable text.
    """
    return f"""
    Job Title: {job.job_title}

    Description:
    {job.job_description}

    Nature of Work:
    {job.nature_of_work}

    Educational Level:
    {job.educational_level or ''}

    Course or Strand:
    {job.course_or_strand or ''}

    Required License:
    {job.required_license or ''}

    Required Eligibility:
    {job.required_eligibility or ''}

    Required Certification:
    {job.required_certification or ''}

    Languages Spoken:
    {job.languages_spoken or ''}

    Experience Required:
    {job.work_experience_months} months

    Other Qualifications:
    {job.other_qualifications or ''}
    """


def upsert_job_vector(job):
    """
    Creates or updates a job embedding in ChromaDB.
    """
    collection = get_job_collection()
    document = build_job_text(job)

    # Using job.uuid ensures consistency with your Jobs model layout
    collection.upsert(
        ids=[str(job.uuid)],
        documents=[document],
        metadatas=[{
            "job_uuid": str(job.uuid),
            "title": job.job_title,
            "nature_of_work": job.nature_of_work,
            "status": job.status,
        }]
    )


def delete_job_vector(job_uuid):
    """
    Removes a job from ChromaDB.
    """
    collection = get_job_collection()
    collection.delete(
        ids=[str(job_uuid)]
    )


# JobMatchingEngine/database.py

def build_applicant_profile_text(applicant):
    """
    Converts an ApplicantProfile instance into searchable text.
    """
    # Pull skill names from the Many-to-Many field mapping
    skills = ", ".join(applicant.skills.values_list("skill_name", flat=True))
    
    # Extract preferred job titles from the relationship
    preferred_jobs = ", ".join(applicant.preferred_job.values_list("job_title", flat=True))

    return f"""
    Education Level:
    {applicant.get_education_level_display()}

    Skills:
    {skills}

    Preferred Job Types or Targets:
    {preferred_jobs}
    """


def query_matching_jobs(applicant, total_results=5):
    """
    Finds jobs matching an applicant profile.
    """
    collection = get_job_collection()
    profile_text = build_applicant_profile_text(applicant)

    results = collection.query(
        query_texts=[profile_text],
        n_results=total_results
    )

    # ChromaDB queries return arrays nested inside an parent array: e.g., [['id1', 'id2']]
    # Extracting the 0th array strips out that layer safely
    ids = results.get("ids", [[]])[0] if results.get("ids") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    documents = results.get("documents", [[]])[0] if results.get("documents") else []

    return {
        "ids": ids,
        "distances": distances,
        "metadatas": metadatas,
        "documents": documents,
    }

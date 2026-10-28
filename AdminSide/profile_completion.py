# AdminSide/profile_completion.py


def is_filled(value):
    """Return True if a field contains meaningful information."""
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def calculate_profile_strength(profile):
    sections = []

    # 1. Personal Information
    personal_fields = [
        profile.first_name,
        profile.last_name,
        profile.date_of_birth,
        profile.sex,
        profile.civil_status,
        profile.nationality,
        profile.place_of_birth,
    ]

    sections.append({
        "name": "Personal Information",
        "fields": personal_fields,
    })

    # 2. Address and Contact Information
    contact_fields = [
        profile.phone_number,
        profile.house_street,
        profile.barangay,
        profile.municipality,
        profile.province,
        profile.region,
    ]

    sections.append({
        "name": "Address and Contact",
        "fields": contact_fields,
    })

    # 3. Education
    education_fields = [
        profile.school_university,
        profile.course_program,
        profile.year_graduated_attended,
    ]

    education_completed = any([
        profile.edu_no_formal,
        profile.edu_elem_level,
        profile.edu_elem_grad,
        profile.edu_hs_level,
        profile.edu_hs_grad,
        profile.edu_college_level,
        profile.edu_college_grad,
        profile.edu_tech_voc,
        profile.edu_post_grad,
    ])

    education_fields.append(education_completed)

    sections.append({
        "name": "Education",
        "fields": education_fields,
    })

    # 4. Preferred Jobs
    preference_fields = [
        profile.pref_salary,
        profile.pref_occupation_1,
    ]

    preference_fields.append(
        profile.pref_local or profile.pref_overseas
    )

    # Require a location only for the selected preference type.
    if profile.pref_local:
        preference_fields.append(profile.pref_location_local)

    if profile.pref_overseas:
        preference_fields.append(profile.pref_location_overseas)

    sections.append({
        "name": "Job Preferences",
        "fields": preference_fields,
    })

    # 5. Skills
    has_skills = (
        profile.skills.exists()
        or is_filled(profile.other_skills)
        or any([
            profile.skill_computer,
            profile.skill_driving,
            profile.skill_customer_service,
            profile.skill_bookkeeping,
            profile.skill_carpentry,
            profile.skill_welding,
        ])
    )

    sections.append({
        "name": "Skills",
        "fields": [has_skills],
    })

    # 6. Documents
    # Count this section only after the applicant uploads at least
    # one document, so applicants without documents aren't penalized.
    document_fields = [
        profile.resume_file,
        profile.applicant_id_picture_front,
        profile.applicant_id_picture_back,
        profile.supporting_doc,
    ]

    if any(is_filled(field) for field in document_fields):
        sections.append({
            "name": "Documents",
            "fields": document_fields,
        })

    # 7. Training
    # Training is optional. Count it only if the applicant starts
    # entering training information.
    training_fields = [
        profile.training_title_1,
        profile.training_hours_1,
        profile.training_institution_1,
        profile.training_date_1,
        profile.training_title_2,
        profile.training_hours_2,
        profile.training_institution_2,
        profile.training_date_2,
    ]

    if any(is_filled(field) for field in training_fields):
        sections.append({
            "name": "Training",
            "fields": training_fields,
        })

    # 8. Work Experience
    # Applicants with no work experience aren't penalized.
    work_experiences = profile.work_experiences.all()

    if work_experiences.exists():
        completed_experiences = 0

        for experience in work_experiences:
            fields = [
                experience.company,
                experience.position,
            ]

            if all(is_filled(field) for field in fields):
                completed_experiences += 1

        sections.append({
            "name": "Work Experience",
            "fields": [
                completed_experiences == work_experiences.count()
            ],
        })

    # Calculate each section's completion percentage.
    section_percentages = []

    for section in sections:
        fields = section["fields"]

        if not fields:
            continue

        completed = sum(
            1 for field in fields if is_filled(field)
        )

        section_percentages.append(
            (completed / len(fields)) * 100
        )

    if not section_percentages:
        return 0

    # Give each included section equal weight.
    profile_strength = round(
        sum(section_percentages) / len(section_percentages)
    )

    return max(0, min(100, profile_strength))
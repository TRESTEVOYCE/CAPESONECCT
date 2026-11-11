
def is_filled(value):
    """Return True if a field contains meaningful information."""
    if value is None:
        return False

    if isinstance(value, bool):
        return value

    # Handles FileField and ImageField values.
    if hasattr(value, 'name'):
        return bool(value.name)

    if isinstance(value, str):
        return bool(value.strip())

    # Zero is considered a valid numeric value.
    return True


def calculate_profile_strength(profile):
    sections = []

    # 1. Personal Information
    personal_fields = [
        profile.first_name,
        profile.middle_name,
        profile.last_name,
        profile.suffix,
        profile.date_of_birth,
        profile.place_of_birth,
        profile.nationality,
        profile.sex,
        profile.civil_status,
        profile.weight,
        profile.height,
    ]

    sections.append({
        "name": "Personal Information",
        "fields": personal_fields,
    })

    # 2. Address and Contact Information
    contact_fields = [
        profile.house_street,
        profile.barangay,
        profile.municipality,
        profile.province,
        profile.region,
        profile.zip_code,
        profile.phone_number,
        profile.email_address,
    ]

    sections.append({
        "name": "Address and Contact",
        "fields": contact_fields,
    })

    # 3. Education
    education_attainment = any([
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

    education_fields = [
        profile.school_status_yes or profile.school_status_no,
        education_attainment,
        profile.school_university,
        profile.course_program,
        profile.year_graduated_attended,
        profile.award_1,
        profile.award_2,
        profile.award_3,
        profile.education_proof_document,
    ]

    sections.append({
        "name": "Education",
        "fields": education_fields,
    })

    # 4. Preferred Jobs
    preference_fields = [
        profile.pref_salary,
        profile.pref_occupation_1,
        profile.pref_occupation_2,
        profile.pref_occupation_3,
        profile.pref_local or profile.pref_overseas,
    ]

    # Require the relevant location only when the preference is selected.
    if profile.pref_local:
        preference_fields.extend([
            profile.pref_location_local,
        ])

    if profile.pref_overseas:
        preference_fields.extend([
            profile.pref_location_overseas,
        ])

    sections.append({
        "name": "Job Preferences",
        "fields": preference_fields,
    })

    # 5. Skills
    # These are the checkbox fields from ApplicantSkillsForm.
    skill_fields = [
        profile.skill_innovation,
        profile.skill_team_work,
        profile.skill_multitasking,
        profile.skill_work_ethics,
        profile.skill_self_motivation,
        profile.skill_creative_problem_solving,
        profile.skill_problem_solving,
        profile.skill_critical_thinking,
        profile.skill_decision_making,
        profile.skill_stress_tolerance,
        profile.skill_planning_organizing,
        profile.skill_social_perceptiveness,
        profile.skill_english_functional,
        profile.skill_english_comprehension,
        profile.skill_math_functional,
        profile.skill_carpentry,
        profile.skill_masonry,
        profile.skill_welding,
        profile.skill_auto_mechanic,
        profile.skill_plumbing,
        profile.skill_driving,
        profile.skill_gardening,
        profile.skill_tailoring,
        profile.skill_photography,
        profile.skill_hairdressing,
        profile.skill_cooking,
        profile.skill_baking,
        profile.other_skills,
    ]

    # Include additional skills saved through the ApplicantSkills model.
    has_additional_skills = profile.skills.exists()

    skill_fields.append(has_additional_skills)

    sections.append({
        "name": "Skills",
        "fields": skill_fields,
    })

    # 6. Required Documents
    # Supporting document and professional license are optional,
    # so they are intentionally excluded.
    document_fields = [
        profile.valid_id_type,
        profile.applicant_id_picture_front,
        profile.applicant_id_picture_back,
        profile.certification_agree,
        profile.resume_file,
    ]

    sections.append({
        "name": "Documents",
        "fields": document_fields,
    })

    # Training and Work Experience are optional.
    # They are intentionally excluded from profile completion.

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

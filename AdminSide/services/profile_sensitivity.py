from dataclasses import dataclass

from AdminSide.models import (
    ApplicantProfile,
    ApplicantSkills,
    ApplicantWorkExperience,
    EmployerProfile,
    User,
)


NON_SENSITIVE_PROFILE_FIELDS = {
    ApplicantProfile: frozenset({
        'email_address',
        'house_street',
        'barangay',
        'zip_code',
        'certification_agree',
        'pref_local',
        'pref_overseas',
        'pref_occupation_1',
        'pref_occupation_2',
        'pref_occupation_3',
        'pref_location_local',
        'pref_location_overseas',
        'pref_salary',
    }),
    ApplicantSkills: frozenset(),
    ApplicantWorkExperience: frozenset(),
    EmployerProfile: frozenset({
        'contact_person',
        'contact_position',
        'email',
    }),
    User: frozenset({
        'profile_picture',
    }),
}


@dataclass(frozen=True)
class ProfileChangeClassification:
    sensitive_fields: frozenset[str]
    non_sensitive_fields: frozenset[str]

    @property
    def requires_reverification(self):
        return bool(self.sensitive_fields)


def classify_profile_changes(profile_or_model, changed_fields):
    """Classify changed fields; only explicitly allowlisted fields are non-sensitive."""
    model = (
        profile_or_model
        if isinstance(profile_or_model, type)
        else type(profile_or_model)
    )
    model = model._meta.concrete_model

    try:
        non_sensitive_fields = NON_SENSITIVE_PROFILE_FIELDS[model]
    except KeyError as exc:
        raise ValueError(
            f'No profile sensitivity rules are defined for {model.__name__}.'
        ) from exc

    changed_fields = frozenset(changed_fields)
    non_sensitive_changes = changed_fields & non_sensitive_fields
    sensitive_changes = changed_fields - non_sensitive_fields

    return ProfileChangeClassification(
        sensitive_fields=sensitive_changes,
        non_sensitive_fields=non_sensitive_changes,
    )


def mark_profile_for_reverification(profile, changed_fields, change_model=None):
    """Move an approved profile to the re-verification queue after sensitive edits."""
    classification = classify_profile_changes(
        change_model or profile,
        changed_fields,
    )
    if not classification.requires_reverification:
        return False

    if isinstance(profile, ApplicantProfile):
        if profile.status != 'approved':
            return False
        profile.status = 'reverify_pending'
        status_field = 'status'
    elif isinstance(profile, EmployerProfile):
        if profile.verification_status != 'verified':
            return False
        profile.verification_status = 'reverify_pending'
        status_field = 'verification_status'
    else:
        raise ValueError(
            f'Re-verification is not supported for {type(profile).__name__}.'
        )

    profile.save(update_fields=[status_field, 'updated_at'])
    return True

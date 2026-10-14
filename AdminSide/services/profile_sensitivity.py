from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.files import FileField
from django.utils import timezone

from AdminSide.models import (
    ApplicantProfile,
    ApplicantSkills,
    ApplicantWorkExperience,
    EmployerProfile,
    ProfileChangeLog,
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
        'email',
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


def _display_value(value):
    if value is None:
        return ''
    if hasattr(value, 'name'):
        return value.name or ''
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, (int, float, Decimal)):
        return format(Decimal(str(value)).normalize(), 'f')
    return str(value)


def capture_profile_changes(instance, many_to_many_values=None):
    """Capture persisted old values and the instance's current values before saving."""
    if instance.pk is None:
        return {}

    model = instance._meta.concrete_model
    old_instance = model._default_manager.get(pk=instance.pk)
    changes = {}
    for field in model._meta.concrete_fields:
        if field.primary_key or field.name in {
            'created_at',
            'updated_at',
            'supporting_doc_uploaded_at',
        }:
            continue
        old_value = _display_value(field.value_from_object(old_instance))
        new_value = _display_value(field.value_from_object(instance))
        if old_value != new_value:
            changes[field.name] = {
                'label': str(field.verbose_name).title(),
                'old': old_value,
                'new': new_value,
            }

    for field_name, new_values in (many_to_many_values or {}).items():
        field = model._meta.get_field(field_name)
        old_values = [
            str(value)
            for value in getattr(old_instance, field_name).all()
        ]
        new_values = [_display_value(value) for value in new_values]
        if old_values != new_values:
            changes[field_name] = {
                'label': str(field.verbose_name).title(),
                'old': old_values,
                'new': new_values,
            }
    return changes


def capture_related_profile_changes(label, old_values, new_values):
    old_values = list(old_values)
    new_values = list(new_values)
    if old_values == new_values:
        return {}
    return {
        label: {
            'label': label.replace('_', ' ').title(),
            'old': old_values,
            'new': new_values,
        }
    }


def record_profile_changes(profile, actor, changes, change_model=None):
    if not changes:
        return None
    classification = classify_profile_changes(
        change_model or profile,
        changes.keys(),
    )
    if not classification.requires_reverification:
        return None

    if isinstance(profile, ApplicantProfile):
        if profile.status == 'approved':
            ProfileChangeLog.objects.filter(applicant=profile).delete()
    elif isinstance(profile, EmployerProfile):
        if profile.verification_status == 'verified':
            ProfileChangeLog.objects.filter(employer=profile).delete()
    else:
        raise ValueError(
            f'Profile change logs are not supported for {type(profile).__name__}.'
        )

    if isinstance(profile, ApplicantProfile):
        return ProfileChangeLog.objects.create(
            applicant=profile,
            changed_by=actor,
            changes=changes,
        )
    if isinstance(profile, EmployerProfile):
        return ProfileChangeLog.objects.create(
            employer=profile,
            changed_by=actor,
            changes=changes,
        )
    return None


def clear_profile_changes(profile):
    if isinstance(profile, ApplicantProfile):
        ProfileChangeLog.objects.filter(applicant=profile).delete()
    elif isinstance(profile, EmployerProfile):
        ProfileChangeLog.objects.filter(employer=profile).delete()
    else:
        raise ValueError(
            f'Profile change logs are not supported for {type(profile).__name__}.'
        )


def profile_change_audit_rows(profile):
    if isinstance(profile, ApplicantProfile):
        change_logs = ProfileChangeLog.objects.filter(
            applicant=profile,
            reviewed_at__isnull=True,
        )
    elif isinstance(profile, EmployerProfile):
        change_logs = ProfileChangeLog.objects.filter(
            employer=profile,
            reviewed_at__isnull=True,
        )
    else:
        raise ValueError(
            f'Profile change logs are not supported for {type(profile).__name__}.'
        )
    change_logs = change_logs.order_by('created_at', 'pk')
    rows = []
    for change_log in change_logs:
        for field_name, change in change_log.changes.items():
            field = None
            try:
                field = profile._meta.get_field(field_name)
            except FieldDoesNotExist:
                pass

            old_value = change.get('old')
            new_value = change.get('new')
            old_url = None
            new_url = None
            if isinstance(field, FileField):
                if old_value:
                    old_url = field.storage.url(old_value)
                if new_value:
                    new_url = field.storage.url(new_value)

            rows.append({
                'field': change.get('label', field_name),
                'old_value': ', '.join(map(str, old_value)) if isinstance(old_value, list) else old_value,
                'new_value': ', '.join(map(str, new_value)) if isinstance(new_value, list) else new_value,
                'old_url': old_url,
                'new_url': new_url,
                'changed_at': change_log.created_at,
            })
    return rows


EDUCATION_PROOF_FIELDS = frozenset({
    'school_status_yes',
    'school_status_no',
    'edu_no_formal',
    'edu_elem_level',
    'edu_elem_grad',
    'edu_hs_level',
    'edu_hs_grad',
    'edu_college_level',
    'edu_college_grad',
    'edu_tech_voc',
    'edu_post_grad',
    'school_university',
    'course_program',
    'year_graduated_attended',
    'award_1',
    'award_2',
    'award_3',
})

TRAINING_PROOF_FIELDS = frozenset({
    'training_title_1',
    'training_hours_1',
    'training_institution_1',
    'training_date_1',
    'training_title_2',
    'training_hours_2',
    'training_institution_2',
    'training_date_2',
})

SKILLS_PROOF_FIELDS = frozenset({
    'skill_computer',
    'skill_driving',
    'skill_customer_service',
    'skill_bookkeeping',
    'skill_carpentry',
    'skill_welding',
    'other_skills',
    'skills',
})


def has_current_supporting_document(applicant):
    change_logs = list(
        ProfileChangeLog.objects.filter(
            applicant=applicant,
            reviewed_at__isnull=True,
        ).order_by('created_at', 'pk')
    )
    if not change_logs:
        return False

    changes_by_field = {}
    for log in change_logs:
        for field_name in log.changes:
            changes_by_field.setdefault(field_name, log.created_at)
            changes_by_field[field_name] = max(
                changes_by_field[field_name],
                log.created_at,
            )

    if set(changes_by_field).intersection(EDUCATION_PROOF_FIELDS):
        changed_at = max(
            changes_by_field[field_name]
            for field_name in EDUCATION_PROOF_FIELDS
            if field_name in changes_by_field
        )
        if not (
            applicant.education_proof_document
            and applicant.education_proof_uploaded_at
            and applicant.education_proof_uploaded_at >= changed_at
        ):
            return False

    if set(changes_by_field).intersection(TRAINING_PROOF_FIELDS):
        changed_at = max(
            changes_by_field[field_name]
            for field_name in TRAINING_PROOF_FIELDS
            if field_name in changes_by_field
        )
        technical_proof_is_current = (
            applicant.technical_certification_document
            and applicant.technical_certification_uploaded_at
            and applicant.technical_certification_uploaded_at >= changed_at
        )
        license_proof_is_current = (
            applicant.professional_license_document
            and applicant.professional_license_uploaded_at
            and applicant.professional_license_uploaded_at >= changed_at
        )
        if not (technical_proof_is_current or license_proof_is_current):
            return False

    if set(changes_by_field).intersection(SKILLS_PROOF_FIELDS):
        changed_at = max(
            changes_by_field[field_name]
            for field_name in SKILLS_PROOF_FIELDS
            if field_name in changes_by_field
        )
        if not (
            applicant.technical_certification_document
            and applicant.technical_certification_uploaded_at
            and applicant.technical_certification_uploaded_at >= changed_at
        ):
            return False

    if 'work_experiences' in changes_by_field:
        changed_at = changes_by_field['work_experiences']
        if not applicant.work_experiences.filter(
            proof_document__isnull=False,
            proof_document_uploaded_at__gte=changed_at,
        ).exclude(proof_document='').exists():
            return False

    return True

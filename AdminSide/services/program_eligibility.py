from dataclasses import dataclass

from django.db.models import Q
from django.utils import timezone

from AdminSide.models import (
    ApplicantProfile,
    DisplacedInformalLaborProgram,
    GovernmentInternshipProgram,
    SpecialProgramForEmploymentOfStudents,
    TupadBeneficiary,
)


FINANCIAL_PROGRAMS = {
    'spes': SpecialProgramForEmploymentOfStudents,
    'tupad': TupadBeneficiary,
    'dilp': DisplacedInformalLaborProgram,
    'gip': GovernmentInternshipProgram,
}


@dataclass(frozen=True)
class ProgramEligibilityResult:
    blocked_reasons: tuple[str, ...]
    review_flags: tuple[str, ...]
    notices: tuple[str, ...]


def _identity_filter(first_name, middle_name, last_name, date_of_birth, sex):
    identity_filter = Q(
        first_name__iexact=first_name.strip(),
        last_name__iexact=last_name.strip(),
        date_of_birth=date_of_birth,
        sex=sex,
    )
    normalized_middle_name = (middle_name or '').strip()
    if normalized_middle_name:
        identity_filter &= Q(middle_name__iexact=normalized_middle_name)
    else:
        identity_filter &= (
            Q(middle_name__isnull=True) | Q(middle_name__exact='')
        )
    return identity_filter


def _candidate_identity_filter(candidate):
    return _identity_filter(
        candidate.first_name,
        candidate.middle_name,
        candidate.last_name,
        candidate.date_of_birth,
        candidate.sex,
    )


def _probable_identity_filter(candidate):
    base_filter = Q(
        first_name__iexact=candidate.first_name.strip(),
        last_name__iexact=candidate.last_name.strip(),
        date_of_birth=candidate.date_of_birth,
        sex=candidate.sex,
    )
    middle_name = (candidate.middle_name or '').strip()
    if middle_name:
        return base_filter & (
            Q(middle_name__isnull=True) | Q(middle_name__exact='')
        )
    return base_filter


def _overlapping_dates_filter(candidate):
    if not candidate.start_date or not candidate.end_date:
        return Q(pk__in=[])
    return Q(
        start_date__lte=candidate.end_date,
        end_date__gte=candidate.start_date,
    )


def _profile_household_identities(candidate):
    identities = {
        (
            candidate.first_name.strip().casefold(),
            (candidate.middle_name or '').strip().casefold(),
            candidate.last_name.strip().casefold(),
            candidate.date_of_birth,
            candidate.sex,
        )
    }
    matching_profiles = ApplicantProfile.objects.filter(
        first_name__iexact=candidate.first_name.strip(),
        last_name__iexact=candidate.last_name.strip(),
        date_of_birth=candidate.date_of_birth,
        sex=candidate.sex,
    )

    for profile in matching_profiles:
        identities.add((
            profile.first_name.strip().casefold(),
            (profile.middle_name or '').strip().casefold(),
            profile.last_name.strip().casefold(),
            profile.date_of_birth,
            profile.sex,
        ))

        household_filter = Q()
        if profile.household_id_no:
            household_filter |= Q(household_id_no=profile.household_id_no)

        address_fields = ('house_street', 'barangay', 'municipality', 'province')
        if all(getattr(profile, field) for field in address_fields):
            address_filter = Q()
            for field in address_fields:
                address_filter &= Q(**{
                    f'{field}__iexact': getattr(profile, field).strip()
                })
            household_filter |= address_filter

        if household_filter:
            for member in ApplicantProfile.objects.filter(household_filter):
                identities.add((
                    member.first_name.strip().casefold(),
                    (member.middle_name or '').strip().casefold(),
                    member.last_name.strip().casefold(),
                    member.date_of_birth,
                    member.sex,
                ))

    return identities


def _identities_filter(identities):
    identity_filter = Q(pk__in=[])
    for first_name, middle_name, last_name, date_of_birth, sex in identities:
        identity_filter |= _identity_filter(
            first_name,
            middle_name,
            last_name,
            date_of_birth,
            sex,
        )
    return identity_filter


def check_program_eligibility(
    program_key,
    candidate,
    *,
    emergency_override=False,
    verified_group_project=False,
):
    """Cross-check a new beneficiary enrollment against existing program registries."""
    blocked_reasons = []
    review_flags = []
    if program_key not in FINANCIAL_PROGRAMS:
        return ProgramEligibilityResult((), (), ())

    candidate_filter = _candidate_identity_filter(candidate)
    probable_filter = _probable_identity_filter(candidate) & ~candidate_filter
    date_overlap = _overlapping_dates_filter(candidate)

    for matched_program, model in FINANCIAL_PROGRAMS.items():
        if model.objects.filter(candidate_filter).filter(
            Q(is_done=False) | date_overlap
        ).exists():
            if matched_program == program_key:
                blocked_reasons.append(
                    f"The applicant already has a duplicate {matched_program.upper()} "
                    "record that is active or has overlapping contract dates."
                )
            else:
                blocked_reasons.append(
                    f"The applicant has an active or overlapping {matched_program.upper()} "
                    "record. Complete that placement before enrolling in another wage or "
                    "financial program."
                )

        if model.objects.filter(probable_filter).filter(
            Q(is_done=False) | date_overlap
        ).exists():
            review_flags.append(
                f"PESO review required: probable identity match in {matched_program.upper()} "
                "because one record has a blank middle name. Confirm the identity before approval."
            )

    if program_key == 'gip' and GovernmentInternshipProgram.objects.filter(
        candidate_filter,
    ).exists():
        blocked_reasons.append(
            "The applicant has a previous GIP record. GIP is limited to one lifetime availment."
        )

    if program_key == 'gip':
        completed_spes_records = SpecialProgramForEmploymentOfStudents.objects.filter(
            candidate_filter,
            is_done=True,
        )
        if completed_spes_records.exists():
            review_flags.append(
                "PESO review required: verify whether the completed SPES placement was with an "
                "LGU or government agency. The registry does not record the placement agency type."
            )
            if completed_spes_records.filter(has_graduated=False).exists():
                review_flags.append(
                    "PESO review required: verify the applicant's graduation status before "
                    "endorsing the SPES graduate to GIP."
                )

    if program_key == 'tupad':
        current_year = timezone.localdate().year
        tupad_records = TupadBeneficiary.objects.filter(start_date__year=current_year)

        exact_repeat = tupad_records.filter(candidate_filter).exists()
        if exact_repeat:
            if emergency_override:
                review_flags.append(
                    "Emergency TUPAD override selected: verify the calamity/emergency "
                    "authorization for this enrollment."
                )
            else:
                blocked_reasons.append(
                    f"The applicant already has a TUPAD record starting in {current_year}. "
                    "A calamity/emergency override is required to proceed."
                )

        contact_match = Q()
        candidate_phone = (candidate.phone_number or '').strip()
        if candidate_phone:
            contact_match |= Q(phone_number__iexact=candidate_phone)
        if candidate.last_name.strip() and candidate.barangay.strip() and candidate.municipality.strip():
            contact_match |= Q(
                last_name__iexact=candidate.last_name.strip(),
                barangay__iexact=candidate.barangay.strip(),
                municipality__iexact=candidate.municipality.strip(),
            )
        contact_match = tupad_records.filter(contact_match).exclude(candidate_filter)
        if contact_match.exists():
            review_flags.append(
                "PESO review required: a current-year TUPAD record shares the applicant's "
                "phone number or surname and barangay/municipality. Confirm whether this is "
                "the same person or a separate household member."
            )

        household_filter = _identities_filter(_profile_household_identities(candidate))
        household_repeat = tupad_records.filter(household_filter).exclude(candidate_filter).exists()
        if household_repeat:
            if emergency_override:
                review_flags.append(
                    "Emergency TUPAD household override selected: verify the calamity/emergency "
                    "authorization for this enrollment."
                )
            else:
                blocked_reasons.append(
                    "A registered household member has a TUPAD record starting in "
                    f"{current_year}. A calamity/emergency override is required to proceed."
                )

    if program_key == 'dilp':
        completed_individual_grant = DisplacedInformalLaborProgram.objects.filter(
            candidate_filter,
            is_done=True,
            project_category='individual',
        ).exists()
        if completed_individual_grant:
            if candidate.project_category == 'individual':
                blocked_reasons.append(
                    "The applicant has a completed individual DILP record. Repeat individual "
                    "grants are restricted; only a qualifying group/association project may proceed."
                )
            elif candidate.project_category == 'group':
                if not verified_group_project:
                    blocked_reasons.append(
                        "The applicant has a completed individual DILP record. Confirm that "
                        "the new group/association project has been verified before proceeding."
                    )
                else:
                    review_flags.append(
                        "The group/association verification was confirmed for this submission. "
                        "Check the supporting documents; verification is not stored in the registry."
                    )

    return ProgramEligibilityResult(
        tuple(dict.fromkeys(blocked_reasons)),
        tuple(dict.fromkeys(review_flags)),
        (),
    )

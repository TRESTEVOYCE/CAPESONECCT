from django.db.models import Count, Q

from .models import (
    ApplicantProfile,
    AppliedJobs,
    EmployerProfile,
    Jobs,
    SpecialProgramForEmploymentOfStudents,
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    CareerGuidanceBeneficiary,
    PESOActivities,
)


def generate_complete_peso_matrix(target_year, target_month):
    """
    Compiles stats from the current beneficiary and activity models into the report matrix.
    """
    jobs = Jobs.objects.filter(created_at__year=target_year, created_at__month=target_month)
    vacancies_posted = jobs.count()

    employers_registered = EmployerProfile.objects.filter(created_at__year=target_year, created_at__month=target_month).count()
    applicants_registered = ApplicantProfile.objects.filter(created_at__year=target_year, created_at__month=target_month).count()
    applicants_registered_female = ApplicantProfile.objects.filter(
        created_at__year=target_year,
        created_at__month=target_month,
        sex='F',
    ).count()

    placed_private = AppliedJobs.objects.filter(
        application_date__year=target_year,
        application_date__month=target_month,
        status='hired',
    ).count()
    placed_private_female = AppliedJobs.objects.filter(
        application_date__year=target_year,
        application_date__month=target_month,
        status='hired',
        applicant__sex='F',
    ).count()

    fairs_count = PESOActivities.objects.filter(created_at__year=target_year, created_at__month=target_month).count()

    spes_qs = SpecialProgramForEmploymentOfStudents.objects.filter(created_at__year=target_year, created_at__month=target_month)
    gip_qs = GovernmentInternshipProgram.objects.filter(created_at__year=target_year, created_at__month=target_month)
    tupad_qs = TupadBeneficiary.objects.filter(created_at__year=target_year, created_at__month=target_month)
    dilp_qs = DisplacedInformalLaborProgram.objects.filter(created_at__year=target_year, created_at__month=target_month)

    spes_elementary = spes_qs.filter(education_level='elementary').count()
    spes_jhs = spes_qs.filter(education_level='juniors_hs').count()
    spes_shs = spes_qs.filter(education_level='senior_hs').count()
    spes_college = spes_qs.filter(education_level='college').count()
    spes_tech_voc = spes_qs.filter(education_level='tech_voc').count()
    spes_osy = spes_qs.filter(is_out_of_school_youth=True).count()
    spes_graduates = spes_qs.filter(has_graduated=True).count()
    spes_nc = spes_qs.filter(has_nc_certification=True).count()
    spes_absorbed = spes_qs.filter(is_absorbed_by_employer=True).count()

    gip_total = gip_qs.count()
    gip_female = gip_qs.filter(sex='F').count()
    gip_graduates_nc = gip_qs.filter(has_nc_certification=True).count()
    gip_absorbed = gip_qs.filter(is_absorbed_by_agency=True).count()

    lmi_youth = ApplicantProfile.objects.filter(created_at__year=target_year, created_at__month=target_month).count()
    lmi_youth_female = ApplicantProfile.objects.filter(created_at__year=target_year, created_at__month=target_month, sex='F').count()

    tupad_total = tupad_qs.count()
    tupad_short = tupad_qs.filter(project_type='short').count()
    tupad_long = tupad_qs.filter(project_type='long').count()

    dilp_total = dilp_qs.count()
    dilp_individual = dilp_qs.filter(project_category='individual').count()
    dilp_group = dilp_qs.filter(project_category='group').count()

    child_labor_total = 0

    pop_projected = 56746
    poor_pop = 16627
    working_pop = 18158
    labor_force = 10949
    employed_persons = 10106
    unemployed_persons = 843
    underemployed_persons = 1890

    lfpr = (labor_force / working_pop) * 100 if working_pop else 0
    employment_rate = (employed_persons / labor_force) * 100 if labor_force else 0
    unemployment_rate = (unemployed_persons / labor_force) * 100 if labor_force else 0
    underemployment_rate = (underemployed_persons / employed_persons) * 100 if employed_persons else 0

    return {
        'vacancies_posted': vacancies_posted,
        'vacancies_posted_total': vacancies_posted,
        'employers_registered': employers_registered,
        'applicants_registered': applicants_registered,
        'applicants_registered_female': applicants_registered_female,
        'placed_private': placed_private,
        'placed_private_female': placed_private_female,
        'hired_private_total': placed_private,
        'hired_private_female': placed_private_female,
        'fairs_conducted': fairs_count,
        'jobs_fairs_conducted': fairs_count,
        'hots_total': placed_private,
        'spes_elementary': spes_elementary,
        'spes_elem': spes_elementary,
        'spes_jhs': spes_jhs,
        'spes_shs': spes_shs,
        'spes_college': spes_college,
        'spes_tech_voc': spes_tech_voc,
        'spes_osy': spes_osy,
        'spes_graduates': spes_graduates,
        'spes_nc': spes_nc,
        'spes_absorbed': spes_absorbed,
        'gip_total': gip_total,
        'gip_female': gip_female,
        'gip_graduates_nc': gip_graduates_nc,
        'gip_absorbed': gip_absorbed,
        'lmi_youth_total': lmi_youth,
        'lmi_youth_female': lmi_youth_female,
        'tupad_total': tupad_total,
        'tupad_short': tupad_short,
        'tupad_long': tupad_long,
        'dilp_total_workers': dilp_total,
        'individual_assistance_total': dilp_individual,
        'group_assistance_total': dilp_group,
        'child_labor_total': child_labor_total,
        'pop_projected': pop_projected,
        'poor_pop': poor_pop,
        'working_pop': working_pop,
        'labor_force': labor_force,
        'employed_persons': employed_persons,
        'unemployed_persons': unemployed_persons,
        'underemployed_persons': underemployed_persons,
        'lfpr': f"{lfpr:.1f}%",
        'employment_rate': f"{employment_rate:.1f}%",
        'unemployment_rate': f"{unemployment_rate:.1f}%",
        'underemployment_rate': f"{underemployment_rate:.1f}%",
    }
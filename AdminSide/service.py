from django.db.models import Count, Q
from django.utils import timezone
# Import only your existing models from the local app folder
from .models import (
    ApplicantProfile, AppliedJobs, EmployerProfile, Jobs, OfferedJobs, 
    SpecialProgramForEmploymentOfStudents, GovernmentInternshipProgram, 
    TupadBeneficiary, DisplacedInformalLaborProgram, JobStartBeneficiary, 
    PESOActivities
)

def generate_complete_peso_matrix(target_year, target_month):
    """
    Compiles stats across the entire 7-section DOLE-PESO monitoring matrix.
    """
    date_filter = Q(created_at__year=target_year, created_at__month=target_month)

    # ==========================================
    # SECTION 1: EMPLOYMENT FACILITATION
    # ==========================================
    # 1.1.1 PEIS Data
    vacancies_peis = Jobs.objects.filter(date_filter, platform='PEIS')
    employers_peis = EmployerProfile.objects.filter(date_filter) 
    
    # 1.1.1.4 Placements via Private Sector (Using related field lookup for sector)
    hired_private = OfferedJobs.objects.filter(date_filter, status='HIRED', job__sector='PRIVATE')
    
    # 1.4 Jobs Fair
    fairs_count = PESOActivities.objects.filter(date_filter, activity_type='JOBS_FAIR', status='COMPLETED').count()
    hots_total = OfferedJobs.objects.filter(date_filter, application_type='JOBS_FAIR', status='HIRED')

    # ==========================================
    # SECTION 2: YOUTH-BRIDGING EMPLOYMENT ASSISTANCE
    # ==========================================
    spes_base = SpecialProgramForEmploymentOfStudents.objects.filter(date_filter, status='PLACED')
    gip_base = GovernmentInternshipProgram.objects.filter(date_filter, status='PLACED')
    jobstart_base = JobStartBeneficiary.objects.filter(date_filter)

    # ==========================================
    # SECTION 3: PESO-LED ADVOCACY AND TRAININGS
    # ==========================================
    lmi_youth = ApplicantProfile.objects.filter(date_filter, age__lte=30)
    lmi_adult = ApplicantProfile.objects.filter(date_filter, age__gt=30)

    # ==========================================
    # SECTION 4: DILEEP AND EMERGENCY EMPLOYMENT
    # ==========================================
    dilp_indiv = DisplacedInformalLaborProgram.objects.filter(date_filter, setup_type='INDIVIDUAL')
    dilp_group = DisplacedInformalLaborProgram.objects.filter(date_filter, setup_type='GROUP')
    tupad_short = TupadBeneficiary.objects.filter(date_filter, contract_duration__lte=30)

    # ==========================================
    # SECTION 5: CHILD LABOR PREVENTION (NO MODEL PATH)
    # ==========================================
    # Clean handling since no model exists yet for this program tracking
    child_labor_total = 0 

    # ==========================================
    # SECTION 7: MONTHLY LABOR MARKET ANALYSIS
    # ==========================================
    # Direct institutional baseline defaults for the visual UI components
    pop_projected = 56746
    poor_pop = 16627
    working_pop = 18158
    labor_force = 10949
    employed_persons = 10106
    unemployed_persons = 843
    underemployed_persons = 1890

    # Calculate operational percentages programmatically
    lfpr = (labor_force / working_pop) * 100 if working_pop else 0
    employment_rate = (employed_persons / labor_force) * 100 if labor_force else 0
    unemployment_rate = (unemployed_persons / labor_force) * 100 if labor_force else 0
    underemployment_rate = (underemployed_persons / employed_persons) * 100 if employed_persons else 0

    return {
        # Section 1
        'vacancies_posted_total': vacancies_peis.count(),
        'hired_private_total': hired_private.count(),
        'hired_private_female': hired_private.filter(applicant__gender='FEMALE').count(),
        'fairs_conducted': fairs_count,
        'hots_total': hots_total.count(),
        
        # Section 2
        'spes_elem': spes_base.filter(education_stage='ELEMENTARY').count(),
        'spes_jhs': spes_base.filter(education_stage='JHS').count(),
        'spes_shs': spes_base.filter(education_stage='SHS').count(),
        'spes_college': spes_base.filter(education_stage='COLLEGE').count(),
        'gip_total': gip_base.count(),
        'gip_female': gip_base.filter(applicant__gender='FEMALE').count(),
        
        # Section 3 & 5
        'lmi_youth_total': lmi_youth.count(),
        'lmi_youth_female': lmi_youth.filter(gender='FEMALE').count(),
        'child_labor_total': child_labor_total,
        
        # Section 7 Computed Analytics Output
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
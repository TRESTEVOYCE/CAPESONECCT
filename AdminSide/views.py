import calendar
import json
from datetime import datetime, timedelta
from django.db.models import Count, Q, OuterRef, Subquery
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, TemplateView, ListView
from .service import generate_complete_peso_matrix
from .models import (
    ApplicantProfile, 
    AppliedJobs, 
    EmployerProfile, 
    Jobs, 
    OfferedJobs, 
    SpecialProgramForEmploymentOfStudents, 
    GovernmentInternshipProgram, 
    TupadBeneficiary, 
    DisplacedInformalLaborProgram, 
    CareerGuidanceBeneficiary
)
from .forms import (
    SpecialProgramForEmploymentOfStudentsForm,
    GovernmentInternshipProgramForm,
    CareerGuidanceBeneficiaryForm,
    TupadBeneficiaryForm,
    DisplacedInformalLaborProgramForm,
    JobVacancyForm
)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Custom mixin to ensure the user is both authenticated and a superuser."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Unauthorized access. Superuser credentials required.")
        return redirect('AdminSide:admin_login')

class AdminLoginView(View):
    """Class-Based View handling administrator authentication."""
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect('AdminSide:dashboard')
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username_str = request.POST.get('username')
        password_str = request.POST.get('password')

        user = authenticate(request, username=username_str, password=password_str)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('AdminSide:dashboard')
        
        messages.error(request, "Invalid administrator credentials! Please Try Again.")
        return render(request, self.template_name)

class AdminLogoutView(View):
    """Class-Based View handling administrator logout."""
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('AdminSide:admin_login')

PROGRAM_CONFIG = {
    'spes': {
        'name': 'Special Program for Employment of Students (SPES)',
        'form_class': SpecialProgramForEmploymentOfStudentsForm,
        'model': SpecialProgramForEmploymentOfStudents,
        'badge_color': 'bg-purple-100 text-purple-700',
    },
    'gip': {
        'name': 'Government Internship Program (GIP)',
        'form_class': GovernmentInternshipProgramForm,
        'model': GovernmentInternshipProgram,
        'badge_color': 'bg-blue-100 text-blue-700',
    },
    'career_guidance': {
        'name': 'Career Guidance & Employment Coaching Program',
        'form_class': CareerGuidanceBeneficiaryForm,
        'model': CareerGuidanceBeneficiary,
        'badge_color': 'bg-indigo-100 text-indigo-700',
    },
    'tupad': {
        'name': 'TUPAD Emergency Employment Program',
        'form_class': TupadBeneficiaryForm,
        'model': TupadBeneficiary,
        'badge_color': 'bg-amber-100 text-amber-700',
    },
    'dilp': {
        'name': 'DOLE Integrated Livelihood Program (DILP)',
        'form_class': DisplacedInformalLaborProgramForm,
        'model': DisplacedInformalLaborProgram,
        'badge_color': 'bg-emerald-100 text-emerald-700',
    },
}

class DashboardView(SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        # Fallback to parent context initialization
        context = super().get_context_data(**kwargs)

        # Counter Metrics
        applicant_count = ApplicantProfile.objects.count()
        employer_count = EmployerProfile.objects.count()
        active_job_count = Jobs.objects.count()
        referral_count = AppliedJobs.objects.count()
        placement_count = AppliedJobs.objects.filter(status='hired').count()
        pending_approval_count = (
            ApplicantProfile.objects.filter(status='pending').count()
            + EmployerProfile.objects.filter(verification_status='pending').count()
        )

        # Tables Slices
        recent_applications = (
            AppliedJobs.objects.select_related(
                'applicant', 'applied_job', 'applicant__user', 
                'applied_job__employer', 'applied_job__employer__user'
            )
            .order_by('-application_date')[:5]
        )

        pending_approvals = list(
            ApplicantProfile.objects.filter(status='pending').select_related('user')[:3]
        ) + list(
            EmployerProfile.objects.filter(verification_status='pending').select_related('user')[:3]
        )

        # Line Chart Metrics Generation
        chart_labels = []
        referred_data = []
        hired_data = []
        near_hire_data = []

        today = timezone.localdate()
        for offset in range(5, -1, -1):
            month_index = (today.month - 1 - offset) % 12
            year = today.year + ((today.month - 1 - offset) // 12)
            month = month_index + 1
            start = timezone.make_aware(datetime(year, month, 1))
            
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            end = timezone.make_aware(datetime(next_year, next_month, 1))

            monthly_applications = AppliedJobs.objects.filter(application_date__gte=start, application_date__lt=end)
            chart_labels.append(calendar.month_abbr[month])
            referred_data.append(monthly_applications.count())
            hired_data.append(monthly_applications.filter(status='hired').count())
            near_hire_data.append(monthly_applications.filter(status__in=['reviewed', 'for interview']).count())

        # Doughnut/Pie Chart Metrics Generation
        job_type_counts = Jobs.objects.values('nature_of_work').annotate(count=Count('id'))
        job_type_lookup = {item['nature_of_work']: item['count'] for item in job_type_counts}
        sector_items = []
        colors = ['#1d3d75', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#94a3b8']
        
        for code, label in Jobs.NATURE_OF_WORK_CHOICES:
            count = job_type_lookup.get(code, 0)
            sector_items.append({
                'label': label, 
                'value': count, 
                'color': colors[len(sector_items)] if len(sector_items) < len(colors) else colors[-1]
            })

        # Inject calculations directly into view context
        context.update({
            'applicant_count': applicant_count,
            'employer_count': employer_count,
            'active_job_count': active_job_count,
            'referral_count': referral_count,
            'placement_count': placement_count,
            'pending_approval_count': pending_approval_count,
            'recent_applications': recent_applications,
            'pending_approvals': pending_approvals,
            'chart_labels': json.dumps(chart_labels),
            'chart_referred': json.dumps(referred_data),
            'chart_hired': json.dumps(hired_data),
            'chart_near_hire': json.dumps(near_hire_data),
            'sector_items': sector_items,
            'sector_data': json.dumps([item['value'] for item in sector_items]),
        })
        return context

class JobPostingsListView(View):
    template_name = 'job_posting.html'

    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '').strip()
        sector_filter = request.GET.get('sector', '').strip()
        status_filter = request.GET.get('status', '').strip()

        jobs = Jobs.objects.all().select_related('employer').order_by('-created_at')

        # Trigger self-contained model check for each record
        for job in jobs:
            job.check_and_close()

        if search_query:
            query_filter = Q(job_title__icontains=search_query) | Q(employer__business_name__icontains=search_query)
            cleaned_id = search_query.replace('JP-', '').replace('jp-', '').strip()
            if cleaned_id.isdigit():
                query_filter |= Q(id=int(cleaned_id))
            jobs = jobs.filter(query_filter)

        if sector_filter and sector_filter != "All":
            jobs = jobs.filter(sector=sector_filter)
        if status_filter and status_filter != "All":
            jobs = jobs.filter(status=status_filter)

        context = {
            'jobs': jobs,
            'form': JobVacancyForm(),
            'total_active': Jobs.objects.filter(status='Active').count(),
            'total_pending': Jobs.objects.filter(status='Pending').count(),
            'total_results': jobs.count(),
            'search_query': search_query,
            'selected_sector': sector_filter,
            'selected_status': status_filter,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = JobVacancyForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            if not job.status:
                job.status = 'Active'
            job.save()
            messages.success(request, f"Job vacancy '{job.job_title}' created successfully!")
            
            # Post/Redirect/Get pattern prevents double submission on browser refresh
            return redirect('AdminSide:job_postings_list')

        # Re-render list with invalid form errors inside the modal
        jobs = Jobs.objects.all().select_related('employer').order_by('-created_at')
        context = {
            'jobs': jobs,
            'form': form,
            'total_active': Jobs.objects.filter(status='Active').count(),
            'total_pending': Jobs.objects.filter(status='Pending').count(),
            'total_results': jobs.count(),
            'show_modal': True,
        }
        return render(request, self.template_name, context)

class JobPostingDetailView(View):
    template_name = 'job_posting_detail.html'

    def get(self, request, job_uuid, *args, **kwargs):
        # Fetch job record and verify status on loading
        job = get_object_or_404(Jobs.objects.select_related('employer'), uuid=job_uuid)
        job.check_and_close()

        context = {
            'job': job,
        }
        return render(request, self.template_name, context)
    
class ApplicantListView(ListView):
    model = ApplicantProfile
    template_name = 'applicant_list.html'
    context_object_name = 'applicants'

    def get_queryset(self):
        # 1. Capture user inputs from searchbars and dropdown select controls
        self.search_query = self.request.GET.get('search', '').strip()
        self.status_filter = self.request.GET.get('status', 'All').strip()
        self.gender_filter = self.request.GET.get('gender', 'All').strip()

        # 2. Optimize DB relational fetching
        queryset = ApplicantProfile.objects.select_related('user').prefetch_related('skills', 'preferred_job')

        # 3. Handle live keyword filtering (Name, Education, or Sequential Padded ID numbers)
        if self.search_query:
            # Strip "AP-" prefix if typed into searchbar to find raw sequence integers
            clean_search = self.search_query.lower().replace('ap-', '')
            id_query = Q()
            if clean_search.isdigit():
                id_query = Q(applicant_sequence=int(clean_search))

            queryset = queryset.filter(
                Q(first_name__icontains=self.search_query) |
                Q(last_name__icontains=self.search_query) |
                Q(education_level__icontains=self.search_query) |
                id_query
            )

        # 4. Handle state filter parameters
        if self.status_filter != 'All':
            queryset = queryset.filter(status=self.status_filter.lower())

        # 5. Handle gender filter parameters
        if self.gender_filter != 'All':
            queryset = queryset.filter(sex=self.gender_filter)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate summary banner numbers using aggregate rules matching your UI layout
        kpi_stats = ApplicantProfile.objects.aggregate(
            total=Count('uuid'),
            female=Count('uuid', filter=Q(sex='F')),
            verified=Count('uuid', filter=Q(status='approved')),
            pending=Count('uuid', filter=Q(status='pending'))
        )

        # Keep state parameters sticky in frontend elements
        context['kpi'] = kpi_stats
        context['search_query'] = self.search_query
        context['current_status'] = self.status_filter
        context['current_gender'] = self.gender_filter
        return context

    def post(self, request, *args, **kwargs):
        """
        Admin action dedicated ONLY to verifying/approving accounts 
        created directly by jobseekers (including walk-ins).
        """
        applicant_uuid = request.POST.get('applicant_uuid')
        new_status = request.POST.get('status')
        
        if applicant_uuid and new_status in ['approved', 'rejected', 'pending']:
            applicant = get_object_or_404(ApplicantProfile, uuid=applicant_uuid)
            applicant.status = new_status
            
            # Record who verified the account for audit logging
            if hasattr(applicant, 'verified_by'):
                applicant.verified_by = request.user
                
            applicant.save()
            
            messages.success(
                request, 
                f"Applicant {applicant.first_name} {applicant.last_name} status updated to '{new_status.title()}'."
            )
            return redirect('applicant_registry')

        messages.error(request, "Invalid request parameters.")
        return redirect('applicant_registry')

class ApplicantVerificationView(DetailView):
    model = ApplicantProfile
    template_name = 'applicant_verification.html'
    context_object_name = 'applicant'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def post(self, request, *args, **kwargs):
        applicant = self.get_object()
        action = request.POST.get('action')
        
        if action == 'verify':
            applicant.status = 'approved'
            # Optional: Record which PESO officer verified the account
            if hasattr(applicant, 'verified_by'):
                applicant.verified_by = request.user
            applicant.save()
            messages.success(request, f"Applicant {applicant.first_name} {applicant.last_name} has been successfully verified.")
            return redirect('AdminSide:applicants_list')
            
        elif action == 'reject':
            applicant.status = 'rejected'
            applicant.save()
            messages.warning(request, f"Applicant {applicant.first_name} {applicant.last_name} has been marked as rejected.")
            return redirect('AdminSide:applicants_list')

        return redirect('AdminSide:applicant_verification', uuid=applicant.uuid)

class EmployerListView(ListView):
    model = EmployerProfile
    template_name = 'employer_list.html'
    context_object_name = 'employers'

    def post(self, request, *args, **kwargs):
        """Handles inline admin verification status updates via POST."""
        employer_id = request.POST.get('employer_id')
        action = request.POST.get('action')
        
        if employer_id and action == 'approve':
            employer = get_object_or_404(EmployerProfile, id=employer_id)
            employer.verification_status = 'Approved'  # Matches your model's 'verification_status' field
            employer.save()
            messages.success(request, f"{employer.company_name} has been verified successfully.")
            
        return redirect('employers:registry')

    def get_queryset(self):
        active_jobs_subquery = Jobs.objects.filter(
            employer=OuterRef('pk'),
            status='Active'  # Adjust if your choice token is lowercase like 'active'
        ).values('employer').annotate(count=Count('id')).values('count')

        hired_applied_subquery = AppliedJobs.objects.filter(
            applied_job__employer=OuterRef('pk'),
            status='hired'
        ).values('applied_job__employer').annotate(count=Count('id')).values('count')

        hired_offered_subquery = OfferedJobs.objects.filter(
            offered_job__employer=OuterRef('pk'),
            status='hired'
        ).values('offered_job__employer').annotate(count=Count('id')).values('count')

        queryset = EmployerProfile.objects.annotate(
            active_posts_count=Subquery(active_jobs_subquery),
            hired_applied_count=Subquery(hired_applied_subquery),
            hired_offered_count=Subquery(hired_offered_subquery)
        ).order_by('-id')

        self.search_query = self.request.GET.get('search', '').strip()
        self.selected_status = self.request.GET.get('status', 'All')

        if self.search_query:
            queryset = queryset.filter(
                Q(company_name__icontains=self.search_query) |
                Q(company_address__icontains=self.search_query)
            )

        if self.selected_status != 'All':
            queryset = queryset.filter(verification_status=self.selected_status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        kpi_counts = EmployerProfile.objects.aggregate(
            approved_count=Count('id', filter=Q(verification_status='Approved')),
            pending_count=Count('id', filter=Q(verification_status='Pending'))
        )

        for employer in context['employers']:
            applied = employer.hired_applied_count or 0
            offered = employer.hired_offered_count or 0
            employer.total_hired_count = applied + offered

        context.update({
            'search_query': self.search_query,
            'selected_status': self.selected_status,
            'total_approved': kpi_counts['approved_count'] or 0,
            'total_pending': kpi_counts['pending_count'] or 0,
            'total_results': self.get_queryset().count(),
        })
        return context
    
class ReferralListView(ListView):
    model = OfferedJobs
    template_name = 'referrals_list.html'
    context_object_name = 'referrals'

    def get_queryset(self):
        # Optimizing foreign key lookups based on your schema fields
        queryset = OfferedJobs.objects.select_related(
            'applicant', 
            'offered_job', 
            'offered_job__employer'
        ).order_by('-date_offered')

        # Capture filtering text and quick-tab strings
        self.search_query = self.request.GET.get('search', '').strip()
        self.selected_status = self.request.GET.get('status', 'All')

        # Global Multi-Field Text Search
        if self.search_query:
            queryset = queryset.filter(
                Q(applicant__first_name__icontains=self.search_query) |
                Q(applicant__last_name__icontains=self.search_query) |
                Q(offered_job__job_title__icontains=self.search_query) |
                Q(offered_job__employer__company_name__icontains=self.search_query)
            )

        # Apply specific status tab matching your model's APPLICATION_STATUS choices
        if self.selected_status != 'All':
            queryset = queryset.filter(status=self.selected_status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate metric pill counters dynamically using your model choices
        kpis = OfferedJobs.objects.aggregate(
            total=Count('id'),
            female=Count('id', filter=Q(applicant__sex='F')),  # Assumes 'sex' field exists on ApplicantProfile
            pending=Count('id', filter=Q(status='pending')),
            reviewed=Count('id', filter=Q(status='reviewed')),
            interview=Count('id', filter=Q(status='for interview')),
            hired=Count('id', filter=Q(status='hired')),
            rejected=Count('id', filter=Q(status='rejected')),
        )

        context.update({
            'search_query': self.search_query,
            'selected_status': self.selected_status,
            'kpis': kpis,
            'total_results': self.get_queryset().count()
        })
        return context
    
class SpecialProgramsListView(ListView):
    template_name = 'special_program.html'
    context_object_name = 'beneficiaries'

    def get_queryset(self):
        self.active_program = self.request.GET.get('program', 'spes')
        self.search_query = self.request.GET.get('search', '').strip()
        self.sex_filter = self.request.GET.get('sex', '').strip()
        self.has_nc_filter = self.request.GET.get('has_nc', '').strip()
        self.graduated_filter = self.request.GET.get('graduated', '').strip()
        self.absorbed_filter = self.request.GET.get('absorbed', '').strip()

        model_class = PROGRAM_CONFIG.get(self.active_program, {}).get('model')

        if not model_class:
            return []

        queryset = model_class.objects.all()

        # Text search
        if self.search_query:
            search_filters = (
                Q(first_name__icontains=self.search_query) |
                Q(last_name__icontains=self.search_query) |
                Q(uuid__icontains=self.search_query)
            )
            if self.search_query.isdigit():
                search_filters |= Q(id=int(self.search_query))
            queryset = queryset.filter(search_filters)

        # Sex / Gender filter
        if self.sex_filter:
            queryset = queryset.filter(sex=self.sex_filter)

        # NC Certification filter
        if self.has_nc_filter in ['1', '0'] and hasattr(model_class, 'has_nc_certification'):
            queryset = queryset.filter(has_nc_certification=(self.has_nc_filter == '1'))

        # Graduated filter
        if self.graduated_filter in ['1', '0'] and hasattr(model_class, 'has_graduated'):
            queryset = queryset.filter(has_graduated=(self.graduated_filter == '1'))

        # Absorbed filter
        if self.absorbed_filter in ['1', '0']:
            if hasattr(model_class, 'is_absorbed_by_employer'):
                queryset = queryset.filter(is_absorbed_by_employer=(self.absorbed_filter == '1'))
            elif hasattr(model_class, 'is_absorbed_by_agency'):
                queryset = queryset.filter(is_absorbed_by_agency=(self.absorbed_filter == '1'))

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Global registry indicators
        global_program_counts = {
            'spes_count': SpecialProgramForEmploymentOfStudents.objects.count(),
            'gip_count': GovernmentInternshipProgram.objects.count(),
            'tupad_count': TupadBeneficiary.objects.count(),
            'dilp_count': DisplacedInformalLaborProgram.objects.count(),
            'career_guidance_count': CareerGuidanceBeneficiary.objects.count(),
        }

        # 2. Compute program-specific KPI blocks (Stripped of female-sub-breakdowns)
        program_kpis = {}
        if self.active_program == 'spes':
            program_kpis = SpecialProgramForEmploymentOfStudents.objects.aggregate(
                total=Count('uuid'),
                female=Count('uuid', filter=Q(sex='F')),
                graduated=Count('uuid', filter=Q(has_graduated=True)),
                nc=Count('uuid', filter=Q(has_nc_certification=True)),
                absorbed=Count('uuid', filter=Q(is_absorbed_by_employer=True)),
                elem=Count('uuid', filter=Q(education_level='elementary')),
                jhs=Count('uuid', filter=Q(education_level='juniors_hs')),
                shs=Count('uuid', filter=Q(education_level='senior_hs')),
                college=Count('uuid', filter=Q(education_level='college')),
                techvoc=Count('uuid', filter=Q(education_level='tech_voc')),
                oosy=Count('uuid', filter=Q(is_out_of_school_youth=True))
            )
        elif self.active_program == 'gip':
            program_kpis = GovernmentInternshipProgram.objects.aggregate(
                total=Count('uuid'),
                female=Count('uuid', filter=Q(sex='F')),
                nc=Count('uuid', filter=Q(has_nc_certification=True)),
                absorbed=Count('uuid', filter=Q(is_absorbed_by_agency=True)),
                als=Count('uuid', filter=Q(education_level='als')),
                jhs=Count('uuid', filter=Q(education_level='juniors_hs')),
                shs=Count('uuid', filter=Q(education_level='senior_hs')),
                techvoc=Count('uuid', filter=Q(education_level='tech_voc')),
                college=Count('uuid', filter=Q(education_level='college'))
            )
        elif self.active_program == 'tupad':
            program_kpis = TupadBeneficiary.objects.aggregate(
                total=Count('uuid'),
                female=Count('uuid', filter=Q(sex='F')),
                short_term=Count('uuid', filter=Q(project_type='short')),
                long_term=Count('uuid', filter=Q(project_type='long'))
            )
        elif self.active_program == 'dilp':
            program_kpis = DisplacedInformalLaborProgram.objects.aggregate(
                total=Count('uuid'),
                female=Count('uuid', filter=Q(sex='F')),
                individual=Count('uuid', filter=Q(project_category='individual')),
                group=Count('uuid', filter=Q(project_category='group'))
            )
        elif self.active_program == 'career_guidance':
            program_kpis = CareerGuidanceBeneficiary.objects.aggregate(
                total=Count('uuid'),
                female=Count('uuid', filter=Q(sex='F')),
                orientation=Count('uuid', filter=Q(activity_type='orientation')),
                coaching=Count('uuid', filter=Q(activity_type='coaching')),
                lmi_briefing=Count('uuid', filter=Q(activity_type='lmi_briefing')),
                received_lmi=Count('uuid', filter=Q(has_received_lmi_materials=True))
            )

        # 3. Dynamic age parsing
        current_year = timezone.now().year
        beneficiaries_list = list(context['beneficiaries'])
        for b in beneficiaries_list:
            b.computed_age = current_year - b.date_of_birth.year if b.date_of_birth else "--"

        context.update({
            'active_program': self.active_program,
            'search_query': getattr(self, 'search_query', ''),
            'globals': global_program_counts,
            'kpis': program_kpis,
            'beneficiaries': beneficiaries_list
        })
        return context

class EnrollBeneficiaryView(View):
    """
    Class-Based View to handle enrollment and editing of beneficiaries 
    under the dynamically selected special program form.
    """
    template_name = 'enroll_beneficiary.html'

    def get_program_config(self, request):
        active_program = request.GET.get('program', 'spes')
        if active_program not in PROGRAM_CONFIG:
            active_program = 'spes'
        return active_program, PROGRAM_CONFIG[active_program]

    def get_instance(self, request, config):
        """
        Retrieves the beneficiary instance if the 'edit' parameter is present in the URL.
        Returns None if creating a new entry.
        """
        edit_id = request.GET.get('edit')
        if not edit_id:
            return None

        model_class = config.get('model') or config.get('model_class')

        if model_class is None:
            from .models import Beneficiaries
            model_class = Beneficiaries

        return get_object_or_404(model_class, uuid=edit_id)

    def extract_address_data(self, request_post):
        """
        Helper method to resolve municipality and barangay from the current form inputs.
        It supports both the newer direct field names used by the template and the older
        select/manual field names used by earlier versions of the form.
        """
        municipality = (
            request_post.get('municipality', '').strip()
            or request_post.get('municipality_select', '').strip()
            or request_post.get('municipality_manual', '').strip()
        )

        barangay = (
            request_post.get('barangay', '').strip()
            or request_post.get('barangay_select', '').strip()
            or request_post.get('barangay_manual', '').strip()
        )

        return municipality, barangay

    def get(self, request, *args, **kwargs):
        active_program, config = self.get_program_config(request)
        instance = self.get_instance(request, config)

        form = config['form_class'](instance=instance)

        context = {
            'form': form,
            'active_program': active_program,
            'program_name': config['name'],
            'badge_color': config['badge_color'],
            'available_programs': PROGRAM_CONFIG,
            'is_editing': bool(instance),
            'beneficiary': instance,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        active_program, config = self.get_program_config(request)
        instance = self.get_instance(request, config)

        # Extract address values
        municipality, barangay = self.extract_address_data(request.POST)

        # Copy POST querydict to make it mutable so we can inject resolved address attributes
        post_data = request.POST.copy()
        post_data['municipality'] = municipality
        post_data['barangay'] = barangay

        form = config['form_class'](post_data, request.FILES or None, instance=instance)

        if form.is_valid():
            beneficiary = form.save(commit=False)
            
            # Explicitly set field attributes on model instance if needed
            if hasattr(beneficiary, 'municipality'):
                beneficiary.municipality = municipality
            if hasattr(beneficiary, 'barangay'):
                beneficiary.barangay = barangay
                
            beneficiary.save()
            
            # Handle M2M relationships saved by ModelForm
            if hasattr(form, 'save_m2m'):
                form.save_m2m()

            action_text = "updated" if instance else "enrolled"
            
            messages.success(
                request,
                f"Successfully {action_text} {beneficiary.first_name} {beneficiary.last_name} under {config['name']}!"
            )

            form = config['form_class']()
            context = {
                'form': form,
                'active_program': active_program,
                'program_name': config['name'],
                'badge_color': config['badge_color'],
                'available_programs': PROGRAM_CONFIG,
                'is_editing': False,
                'beneficiary': None,
            }
            return render(request, self.template_name, context)

        messages.error(request, "Please correct the errors in the form below.")
        context = {
            'form': form,
            'active_program': active_program,
            'program_name': config['name'],
            'badge_color': config['badge_color'],
            'available_programs': PROGRAM_CONFIG,
            'is_editing': bool(instance),
            'beneficiary': instance,
        }
        return render(request, self.template_name, context)
    
class PesoMonthlyReportView(View):
    template_name = 'report.html'

    # 1. PLACE THE DICTIONARY HERE AS A CLASS CONSTANT
    MONTH_NAMES = {
        "1": "January", "2": "February", "3": "March", "4": "April",
        "5": "May", "6": "June", "7": "July", "8": "August",
        "9": "September", "10": "October", "11": "November", "12": "December"
    }

    def _get_zero_matrix(self):
        return {
            'vacancies_posted': 0,
            'vacancies_posted_total': 0,
            'employers_registered': 0,
            'applicants_registered': 0,
            'applicants_registered_female': 0,
            'placed_private': 0,
            'placed_private_female': 0,
            'hired_private_total': 0,
            'hired_private_female': 0,
            'fairs_conducted': 0,
            'jobs_fairs_conducted': 0,
            'hots_total': 0,
            'spes_elem': 0,
            'spes_elementary': 0,
            'spes_college': 0,
            'gip_total': 0,
            'gip_female': 0,
            'lmi_youth_total': 0,
            'lmi_youth_female': 0,
            'child_labor_total': 0,
            'child_labor_referred': 0,
            'pop_projected': 0,
            'lfpr': '0.0%',
            'employment_rate': '0.0%',
        }

    def get(self, request, *args, **kwargs):
        month = request.GET.get('month', '')
        
        context = {
            'matrix_visible': False,
            'selected_province': 'Leyte',
            'selected_municipality': '',
            'selected_month': month,
            # 2. REFER TO IT USING self.MONTH_NAMES HERE
            'selected_month_name': self.MONTH_NAMES.get(month, ''),
            'selected_year': '',
            'metrics': self._get_zero_matrix(),
            'issues_concerns': ''
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        municipality = request.POST.get('municipality', '').strip()
        month = request.POST.get('month', '').strip()
        year = request.POST.get('year', '').strip()

        matrix_visible = False
        metrics = self._get_zero_matrix()

        if 'action_generate' in request.POST:
            if not municipality or not month or not year:
                messages.error(request, "Please fill out the Municipality, Month, and Year.")
            else:
                try:
                    system_data = generate_complete_peso_matrix(int(year), int(month))
                    metrics.update(system_data)
                except Exception:
                    pass
                matrix_visible = True
                messages.success(request, f"Generated parameters for {municipality}.")

        elif 'action_save' in request.POST:
            matrix_visible = True
            try:
                metrics['vacancies_posted_total'] = int(request.POST.get('vacancies_posted_total', 0))
                metrics['hired_private_total'] = int(request.POST.get('hired_private_total', 0))
                metrics['hired_private_female'] = int(request.POST.get('hired_private_female', 0))
                metrics['child_labor_total'] = int(request.POST.get('child_labor_total', 0))
                
                if metrics['hired_private_female'] > metrics['hired_private_total']:
                    messages.error(request, "Female placements cannot exceed total volumes.")
                else:
                    messages.success(request, "Report matrix data successfully verified.")
            except ValueError:
                messages.error(request, "Please ensure all manual inputs contain valid integers.")

        context = {
            'matrix_visible': matrix_visible,
            'selected_province': 'Leyte',
            'selected_municipality': municipality,
            'selected_month': month,
            # 3. REFER TO IT USING self.MONTH_NAMES HERE AS WELL
            'selected_month_name': self.MONTH_NAMES.get(month, ''),
            'selected_year': year,
            'metrics': metrics,
            'issues_concerns': request.POST.get('issues_concerns', '').strip()
        }
        return render(request, self.template_name, context)
    
import calendar
import json
import random
import logging
from smtplib import SMTPException
from datetime import datetime, timedelta
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.db.models import Count, Q, OuterRef, Subquery
from django.contrib import messages
from django.contrib.messages import get_messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, TemplateView, ListView
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic import FormView
from django.core.mail import send_mail
from .service import generate_complete_peso_matrix
from .models import (
    User,
    ApplicantProfile, 
    AppliedJobs, 
    EmployerProfile, 
    Jobs, 
    OfferedJobs, 
    SpecialProgramForEmploymentOfStudents, 
    GovernmentInternshipProgram, 
    TupadBeneficiary, 
    DisplacedInformalLaborProgram, 
    CareerGuidanceBeneficiary,
    PESOActivities
)
from .forms import (
    SpecialProgramForEmploymentOfStudentsForm,
    GovernmentInternshipProgramForm,
    CareerGuidanceBeneficiaryForm,
    TupadBeneficiaryForm,
    DisplacedInformalLaborProgramForm,
    JobVacancyForm,
    ReferralForm,
    EditProfileNameForm
)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from openpyxl import Workbook
from .models import Notification
from .utils import notify_admins

logger = logging.getLogger(__name__)

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

        list(get_messages(request))
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

class DashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        # Counter Metrics
        applicant_count = ApplicantProfile.objects.count()
        employer_count = EmployerProfile.objects.count()

        # Job postings count filtered to active status
        active_job_count = Jobs.objects.filter(status='Active').count()
        urgent_job_count = Jobs.objects.filter(
            status='Active',
            job_posting_expiry__gt=today,
            job_posting_expiry__lte=today + timedelta(days=7),
        ).count()
        
        referral_count = OfferedJobs.objects.count()
        weekly_start = timezone.make_aware(
            datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        )
        weekly_end = weekly_start + timedelta(days=7)
        weekly_referral_count = OfferedJobs.objects.filter(
            date_offered__gte=weekly_start,
            date_offered__lt=weekly_end,
        ).count()

        placement_count = (
            OfferedJobs.objects.filter(status='hired').count() +
            AppliedJobs.objects.filter(status='hired').count()
        )
        
        near_hire_count = (
            OfferedJobs.objects.filter(status='near_hire').count() +
            AppliedJobs.objects.filter(status='near_hire').count()
        )

        # Compare registrations to the previous calendar month.
        first_of_month = timezone.make_aware(datetime(today.year, today.month, 1))
        if today.month == 1:
            first_of_previous_month = timezone.make_aware(datetime(today.year - 1, 12, 1))
        else:
            first_of_previous_month = timezone.make_aware(datetime(today.year, today.month - 1, 1))
        if today.month == 12:
            first_of_next_month = timezone.make_aware(datetime(today.year + 1, 1, 1))
        else:
            first_of_next_month = timezone.make_aware(datetime(today.year, today.month + 1, 1))

        monthly_new_applicants = ApplicantProfile.objects.filter(
            created_at__gte=first_of_month,
            created_at__lt=first_of_next_month,
        ).count()
        previous_month_applicants = ApplicantProfile.objects.filter(
            created_at__gte=first_of_previous_month,
            created_at__lt=first_of_month,
        ).count()
        monthly_new_employers = EmployerProfile.objects.filter(
            created_at__gte=first_of_month,
            created_at__lt=first_of_next_month,
        ).count()

        if previous_month_applicants:
            applicant_change = (
                (monthly_new_applicants - previous_month_applicants)
                / previous_month_applicants
                * 100
            )
            applicant_change_display = f'{applicant_change:+g}%'
            applicant_change_caption = 'vs last month'
            applicant_change_class = (
                'bg-emerald-50 text-emerald-700'
                if applicant_change >= 0 else 'bg-rose-50 text-rose-700'
            )
        else:
            applicant_change_display = f'+{monthly_new_applicants} new'
            applicant_change_caption = 'this month'
            applicant_change_class = 'bg-emerald-50 text-emerald-700'

        # The placements card links to a combined list of direct applications and referrals.
        total_applications_and_referrals = AppliedJobs.objects.count() + referral_count
        placement_rate = (
            round(placement_count / total_applications_and_referrals * 100, 1)
            if total_applications_and_referrals else 0.0
        )

        recent_referrals = (
            OfferedJobs.objects.select_related(
                'applicant', 'applicant__user', 'offered_job',
                'offered_job__employer'
            )
            .order_by('-date_offered')[:5]
        )

        pending_approvals = sorted(
            list(
                ApplicantProfile.objects.filter(status='pending')
                .select_related('user')
                .order_by('created_at')[:5]
            ) + list(
                EmployerProfile.objects.filter(verification_status='pending')
                .select_related('user')
                .order_by('created_at')[:5]
            ),
            key=lambda profile: profile.created_at,
        )[:5]

        # Existing chart metric logic...
        chart_labels = []
        chart_periods = []
        referred_data = []
        hired_data = []
        near_hire_data = []

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

            monthly_referrals = OfferedJobs.objects.filter(date_offered__gte=start, date_offered__lt=end)
            monthly_applications = AppliedJobs.objects.filter(application_date__gte=start, application_date__lt=end)
            chart_labels.append(calendar.month_abbr[month])
            chart_periods.append(f'{year:04d}-{month:02d}')
            referred_data.append(monthly_referrals.count())
            hired_data.append(
                monthly_referrals.filter(status='hired').count() +
                monthly_applications.filter(status='hired').count()
            )
            near_hire_data.append(
                monthly_referrals.filter(status='near_hire').count() +
                monthly_applications.filter(status='near_hire').count()
            )

        # Count hired direct applications and PESO referrals by job type.
        job_type_lookup = {}
        hired_application_counts = AppliedJobs.objects.filter(status='hired').values(
            'applied_job__nature_of_work'
        ).annotate(count=Count('id'))
        hired_referral_counts = OfferedJobs.objects.filter(status='hired').values(
            'offered_job__nature_of_work'
        ).annotate(count=Count('id'))

        for item in hired_application_counts:
            code = item['applied_job__nature_of_work']
            job_type_lookup[code] = job_type_lookup.get(code, 0) + item['count']

        for item in hired_referral_counts:
            code = item['offered_job__nature_of_work']
            job_type_lookup[code] = job_type_lookup.get(code, 0) + item['count']

        sector_items = []
        colors = ['#1d3d75', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#94a3b8']
        
        for code, label in Jobs.NATURE_OF_WORK_CHOICES:
            count = job_type_lookup.get(code, 0)
            sector_items.append({
                'code': code,
                'label': label, 
                'value': count, 
                'color': colors[len(sector_items)] if len(sector_items) < len(colors) else colors[-1]
            })

        # Inject updated dynamic metrics into template context
        context.update({
            'applicant_count': applicant_count,
            'employer_count': employer_count,
            'active_job_count': active_job_count,
            'referral_count': referral_count,
            'placement_count': placement_count,
            'near_hire_count': near_hire_count,
            'urgent_job_count': urgent_job_count,
            'weekly_referral_count': weekly_referral_count,
            'monthly_new_applicants': monthly_new_applicants,
            'monthly_new_employers': monthly_new_employers,
            'applicant_change_display': applicant_change_display,
            'applicant_change_caption': applicant_change_caption,
            'applicant_change_class': applicant_change_class,
            'placement_rate': placement_rate,
            'current_month_name': calendar.month_name[today.month],
            'recent_referrals': recent_referrals,
            'pending_approvals': pending_approvals,
            'chart_labels': json.dumps(chart_labels),
            'chart_periods': json.dumps(chart_periods),
            'chart_referred': json.dumps(referred_data),
            'chart_hired': json.dumps(hired_data),
            'chart_near_hire': json.dumps(near_hire_data),
            'sector_items': sector_items,
            'sector_codes': json.dumps([item['code'] for item in sector_items]),
            'sector_labels': json.dumps([item['label'] for item in sector_items]),
            'sector_colors': json.dumps([item['color'] for item in sector_items]),
            'sector_data': json.dumps([item['value'] for item in sector_items]),
        })
        return context
    
class JobVacancyCreateView(LoginRequiredMixin, View):
    template_name = 'job_posting_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': JobVacancyForm()})

    def post(self, request, *args, **kwargs):
        form = JobVacancyForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.status = 'Active'
            job.save()
            return redirect('AdminSide:job_postings_list')

        return render(request, self.template_name, {'form': form})

class JobPostingsListView(LoginRequiredMixin, View):
    template_name = 'job_posting_list.html'

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
            jobs = jobs.filter(nature_of_work=sector_filter)
        if status_filter and status_filter != "All":
            jobs = jobs.filter(status=status_filter)

        context = {
            'jobs': jobs,
            'total_active': Jobs.objects.filter(status='Active').count(),
            'total_pending': Jobs.objects.filter(status='Pending').count(),
            'total_results': jobs.count(),
            'search_query': search_query,
            'selected_sector': sector_filter,
            'selected_status': status_filter,
        }
        return render(request, self.template_name, context)

class JobPostingDetailView(LoginRequiredMixin, View):
    template_name = 'job_posting_detail.html'

    def get(self, request, job_uuid, *args, **kwargs):
        # Fetch job record and verify status on loading
        job = get_object_or_404(Jobs.objects.select_related('employer'), uuid=job_uuid)
        job.check_and_close()

        # Retrieve direct applicants and PESO referrals
        direct_applications = AppliedJobs.objects.filter(applied_job=job).select_related('applicant', 'applicant__user')
        peso_referrals = OfferedJobs.objects.filter(offered_job=job).select_related('applicant', 'applicant__user')

        context = {
            'job': job,
            'direct_applications': direct_applications,
            'peso_referrals': peso_referrals,
            'total_applications_count': job.total_applicants_count,
        }
        return render(request, self.template_name, context)

    def post(self, request, job_uuid, *args, **kwargs):
        job = get_object_or_404(Jobs, uuid=job_uuid)
        action = request.POST.get('action')

        if action == 'close_job':
            job.status = 'Closed'
            job.save(update_fields=['status'])
            messages.success(request, f"Job posting '{job.job_title}' has been marked as Closed.")
        elif action == 'activate_job':
            job.status = 'Active'
            job.save(update_fields=['status'])
            messages.success(request, f"Job posting '{job.job_title}' is now Active.")

        return redirect('AdminSide:job_detail', job_uuid=job.uuid)
    
class ApplicantListView(LoginRequiredMixin, ListView):
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
            
            if new_status != 'approved':
                messages.success(
                    request,
                    f"Applicant {applicant.first_name} {applicant.last_name} status updated to '{new_status.title()}'."
                )
            return redirect('applicant_registry')

        messages.error(request, "Invalid request parameters.")
        return redirect('applicant_registry')

class ApplicantVerificationView(LoginRequiredMixin, DetailView):
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
            return redirect('AdminSide:applicant_verification', uuid=applicant.uuid)
            
        elif action == 'reject':
            applicant.status = 'rejected'
            applicant.save()
            return redirect('AdminSide:applicant_verification', uuid=applicant.uuid)

        return redirect('AdminSide:applicant_verification', uuid=applicant.uuid)

class EmployerListView(LoginRequiredMixin, ListView):
    model = EmployerProfile
    template_name = 'employer_list.html'
    context_object_name = 'employers'

    def post(self, request, *args, **kwargs):
        employer_id = request.POST.get('employer_id')
        action = request.POST.get('action')
        
        if employer_id:
            employer = get_object_or_404(EmployerProfile, id=employer_id)
            if action == 'approve':
                employer.verification_status = 'verified'
                employer.save()
            elif action == 'reject':
                employer.verification_status = 'rejected'
                employer.save()
                messages.warning(request, f"{employer.business_name} registration rejected.")
            
        return redirect('AdminSide:employers_list') # Adjust URL name as needed

    def get_queryset(self):
        active_jobs_subquery = Jobs.objects.filter(
            employer=OuterRef('pk'),
            status='Active'
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
                Q(business_name__icontains=self.search_query) |
                Q(street_address__icontains=self.search_query) |
                Q(barangay__icontains=self.search_query) |
                Q(municipality__icontains=self.search_query)
            )

        if self.selected_status != 'All':
            queryset = queryset.filter(verification_status=self.selected_status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        kpi_counts = EmployerProfile.objects.aggregate(
            approved_count=Count('id', filter=Q(verification_status='verified')),
            pending_count=Count('id', filter=Q(verification_status='pending'))
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

class EmployerVerificationView(LoginRequiredMixin, DetailView):
    model = EmployerProfile
    template_name = 'employer_verification.html'
    context_object_name = 'employer'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def post(self, request, *args, **kwargs):
        employer = self.get_object()
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '').strip()

        if action == 'approve':
            employer.verification_status = 'verified'
            employer.save()
        elif action == 'reject':
            employer.verification_status = 'rejected'
            employer.save()

        return redirect('AdminSide:employer_verification', uuid=employer.uuid)
    
class ReferralListView(LoginRequiredMixin, ListView):
    model = OfferedJobs
    template_name = 'referrals_list.html'
    context_object_name = 'application_statuses'

    def get_queryset(self):
        applications = AppliedJobs.objects.select_related(
            'applicant', 'applicant__user', 'applied_job', 'applied_job__employer'
        )
        referrals = OfferedJobs.objects.select_related(
            'applicant', 'applicant__user', 'offered_job', 'offered_job__employer'
        )

        self.search_query = self.request.GET.get('search', '').strip()
        self.selected_status = self.request.GET.get('status', 'All').strip()
        self.selected_source = self.request.GET.get('source', 'all').strip()
        self.selected_period = self.request.GET.get('period', '').strip()
        self.selected_job_type = self.request.GET.get('job_type', '').strip()
        if self.selected_source not in {'all', 'direct', 'referral'}:
            self.selected_source = 'all'
        if self.selected_job_type not in dict(Jobs.NATURE_OF_WORK_CHOICES):
            self.selected_job_type = ''

        if self.search_query:
            applications = applications.filter(
                Q(applicant__first_name__icontains=self.search_query) |
                Q(applicant__last_name__icontains=self.search_query) |
                Q(applied_job__job_title__icontains=self.search_query) |
                Q(applied_job__employer__business_name__icontains=self.search_query)
            )
            referrals = referrals.filter(
                Q(applicant__first_name__icontains=self.search_query) |
                Q(applicant__last_name__icontains=self.search_query) |
                Q(offered_job__job_title__icontains=self.search_query) |
                Q(offered_job__employer__business_name__icontains=self.search_query)
            )

        if self.selected_status == 'near_hire':
            applications = applications.filter(status='near_hire')
            referrals = referrals.filter(status='near_hire')
        elif self.selected_status != 'All':
            applications = applications.filter(status=self.selected_status)
            referrals = referrals.filter(status=self.selected_status)

        if self.selected_job_type:
            applications = applications.filter(applied_job__nature_of_work=self.selected_job_type)
            referrals = referrals.filter(offered_job__nature_of_work=self.selected_job_type)

        if self.selected_source == 'direct':
            referrals = referrals.none()
        elif self.selected_source == 'referral':
            applications = applications.none()

        try:
            period_start = datetime.strptime(self.selected_period, '%Y-%m')
        except ValueError:
            period_start = None

        if period_start:
            period_start = timezone.make_aware(period_start)
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
            applications = applications.filter(application_date__gte=period_start, application_date__lt=period_end)
            referrals = referrals.filter(date_offered__gte=period_start, date_offered__lt=period_end)
            self.selected_period = period_start.strftime('%Y-%m')
        else:
            self.selected_period = ''

        statuses = []
        for application in applications:
            application.source_type = 'Direct Application'
            application.job = application.applied_job
            application.offered_job = application.applied_job
            application.submitted_at = application.application_date
            application.date_offered = application.application_date
            application.remarks = ''
            application.status_label = 'Near Hire' if application.status == 'near_hire' else application.get_status_display()
            statuses.append(application)

        for referral in referrals:
            referral.source_type = 'PESO Referral'
            referral.job = referral.offered_job
            referral.submitted_at = referral.date_offered
            referral.status_label = 'Near Hire' if referral.status == 'near_hire' else referral.get_status_display()
            statuses.append(referral)

        statuses.sort(key=lambda record: record.submitted_at, reverse=True)
        return statuses

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'search_query': self.search_query,
            'selected_status': self.selected_status,
            'selected_source': self.selected_source,
            'selected_period': self.selected_period,
            'selected_job_type': self.selected_job_type,
            'job_type_choices': Jobs.NATURE_OF_WORK_CHOICES,
            'total_results': len(context['application_statuses']),
        })
        return context

class ReferralCreateView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    template_name = 'referrals_form.html'

    def get(self, request, *args, **kwargs):
        form = ReferralForm(initial={'referred_by': request.user.get_full_name() or request.user.username})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = ReferralForm(request.POST)
        if form.is_valid():
            referral = form.save()
            messages.success(
                request, 
                f"Referral for {referral.applicant.first_name} {referral.applicant.last_name} created successfully!"
            )
            return redirect('AdminSide:referrals_list')
        
        messages.error(request, "Please correct the errors in the referral form.")
        return render(request, self.template_name, {'form': form})

class SpecialProgramsListView(LoginRequiredMixin, ListView):
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

class EnrollBeneficiaryView(LoginRequiredMixin, View):
    """
    Class-Based View to handle enrollment and editing of beneficiaries 
    under the dynamically selected special program form.
    """
    template_name = 'special_program_beneficiary_form.html'

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
    
class PesoMonthlyReportView(LoginRequiredMixin, View):
    template_name = 'report.html'

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
            'returned_training': 0,
            'referred_placement': 0,
            'referred_placement_female': 0,
            'applicants_placed': 0,
            'applicants_placed_female': 0,
            'placed_private': 0,
            'placed_private_female': 0,
            'placed_gov': 0,
            'placed_gov_female': 0,
            'placed_overseas': 0,
            'placed_overseas_female': 0,
            'placement_rate': '0.0%',
            'lra_qualified': 0,
            'lra_near_hire': 0,
            'sra_qualified': 0,
            'sra_near_hire': 0,
            'jobs_fairs_conducted': 0,
            'fair_conducted_local': 0,
            'fair_conducted_overseas': 0,
            'participating_establishments': 0,
            'establishments_local': 0,
            'establishments_overseas': 0,
            'vacancies_solicited': 0,
            'vacancies_solicited_local': 0,
            'vacancies_solicited_overseas': 0,
            'fair_placement_rate': '0.0%',
            'fair_applicants_total': 0,
            'fair_hots': 0,
            'fair_referred': 0,
            'fair_qualified': 0,
            'fair_near_hire': 0,
            'fair_interviews': 0,
            'fair_ref_skills': 0,
            'fair_ref_agency': 0,
            'spes_elementary': 0,
            'spes_jhs': 0,
            'spes_shs': 0,
            'spes_college': 0,
            'spes_tech_voc': 0,
            'spes_osy': 0,
            'spes_graduates': 0,
            'spes_nc': 0,
            'spes_absorbed': 0,
            'gip_total': 0,
            'gip_female': 0,
            'gip_als': 0,
            'gip_jhs': 0,
            'gip_shs': 0,
            'gip_tech_voc': 0,
            'gip_college': 0,
            'gip_graduates_nc': 0,
            'gip_absorbed': 0,
            'jobstart_assisted': 0,
            'jobstart_trainings': 0,
            'jobstart_life_skills': 0,
            'jobstart_tech_training': 0,
            'jobstart_internship': 0,
            'jobstart_placed': 0,
            'jobstart_finishers': 0,
            'lmi_youth': 0,
            'lmi_youth_female': 0,
            'lmi_non_youth': 0,
            'lmi_non_youth_female': 0,
            'lmi_institutions': 0,
            'cdsp_school': 0,
            'cdsp_peso': 0,
            'cdsp_workplace': 0,
            'applicants_coached': 0,
            'dilp_total_workers': 0,
            'individual_assistance_total': 0,
            'ind_formation': 0,
            'ind_enhancement': 0,
            'ind_restoration': 0,
            'group_assistance_total': 0,
            'grp_formation': 0,
            'grp_enhancement': 0,
            'grp_restoration': 0,
            'tupad_total': 0,
            'tupad_short': 0,
            'tupad_long': 0,
            'child_angel_tree': 0,
            'child_parent_livelihood': 0,
            'child_rescue': 0,
            'child_lgu_assist1': 0,
            'child_lgu_assist2': 0,
            'pop_projected': 0,
            'pop_poor': 0,
            'pop_working': 0,
            'lfpr': '0.0%',
            'labor_force_count': 0,
            'employment_rate': '0.0%',
            'employed_count': 0,
            'unemployment_rate': '0.0%',
            'unemployed_count': 0,
            'underemployment_rate': '0.0%',
            'underemployed_count': 0,
        }

    def _generate_peso_matrix(self, year, month, municipality=''):
        matrix = self._get_zero_matrix()

        # Calculate dynamic database counts for the given month and year
        start_date = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1))

        # 1. Job search, employers & applicants
        vacancies = Jobs.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        ).count()
        employers = EmployerProfile.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        ).count()
        applicants_qs = ApplicantProfile.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        )
        
        applied_qs = AppliedJobs.objects.filter(
            application_date__gte=start_date, application_date__lt=end_date
        )
        offered_qs = OfferedJobs.objects.filter(
            date_offered__gte=start_date, date_offered__lt=end_date
        )

        referred_count = applied_qs.count() + offered_qs.count()
        referred_female_count = (
            applied_qs.filter(applicant__sex='F').count() +
            offered_qs.filter(applicant__sex='F').count()
        )

        hired_applied = applied_qs.filter(status='hired')
        hired_offered = offered_qs.filter(status='hired')
        placed_count = hired_applied.count() + hired_offered.count()
        placed_female_count = (
            hired_applied.filter(applicant__sex='F').count() +
            hired_offered.filter(applicant__sex='F').count()
        )

        matrix.update({
            'vacancies_posted': vacancies,
            'employers_registered': employers,
            'applicants_registered': applicants_qs.count(),
            'applicants_registered_female': applicants_qs.filter(sex='F').count(),
            'referred_placement': referred_count,
            'referred_placement_female': referred_female_count,
            'applicants_placed': placed_count,
            'applicants_placed_female': placed_female_count,
            'placed_private': placed_count,
            'placed_private_female': placed_female_count,
            'placement_rate': f"{round((placed_count / referred_count * 100), 1)}%" if referred_count > 0 else '0.0%',
        })

        # 2. SPES Program Counts
        spes_qs = SpecialProgramForEmploymentOfStudents.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        )
        matrix.update({
            'spes_elementary': spes_qs.filter(education_level='elementary').count(),
            'spes_jhs': spes_qs.filter(education_level='juniors_hs').count(),
            'spes_shs': spes_qs.filter(education_level='senior_hs').count(),
            'spes_college': spes_qs.filter(education_level='college').count(),
            'spes_tech_voc': spes_qs.filter(education_level='tech_voc').count(),
            'spes_osy': spes_qs.filter(is_out_of_school_youth=True).count(),
            'spes_graduates': spes_qs.filter(has_graduated=True).count(),
            'spes_nc': spes_qs.filter(has_nc_certification=True).count(),
            'spes_absorbed': spes_qs.filter(is_absorbed_by_employer=True).count(),
        })

        # 3. GIP Program Counts
        gip_qs = GovernmentInternshipProgram.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        )
        matrix.update({
            'gip_total': gip_qs.count(),
            'gip_female': gip_qs.filter(sex='F').count(),
            'gip_als': gip_qs.filter(education_level='als').count(),
            'gip_jhs': gip_qs.filter(education_level='juniors_hs').count(),
            'gip_shs': gip_qs.filter(education_level='senior_hs').count(),
            'gip_tech_voc': gip_qs.filter(education_level='tech_voc').count(),
            'gip_college': gip_qs.filter(education_level='college').count(),
            'gip_graduates_nc': gip_qs.filter(has_nc_certification=True).count(),
            'gip_absorbed': gip_qs.filter(is_absorbed_by_agency=True).count(),
        })

        # 4. TUPAD Emergency Employment Counts
        tupad_qs = TupadBeneficiary.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        )
        matrix.update({
            'tupad_total': tupad_qs.count(),
            'tupad_short': tupad_qs.filter(project_type='short').count(),
            'tupad_long': tupad_qs.filter(project_type='long').count(),
        })

        # 5. DILP Livelihood Program Counts
        dilp_qs = DisplacedInformalLaborProgram.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        )
        matrix.update({
            'dilp_total_workers': dilp_qs.count(),
            'individual_assistance_total': dilp_qs.filter(project_category='individual').count(),
            'group_assistance_total': dilp_qs.filter(project_category='group').count(),
        })

        # 6. Career Guidance / LMI Activities
        cg_qs = CareerGuidanceBeneficiary.objects.filter(
            created_at__gte=start_date, created_at__lt=end_date
        )
        youth_list = [b for b in cg_qs if b.date_of_birth and (year - b.date_of_birth.year) <= 30]
        non_youth_list = [b for b in cg_qs if b.date_of_birth and (year - b.date_of_birth.year) > 30]

        matrix.update({
            'lmi_youth': len(youth_list),
            'lmi_youth_female': len([b for b in youth_list if b.sex == 'F']),
            'lmi_non_youth': len(non_youth_list),
            'lmi_non_youth_female': len([b for b in non_youth_list if b.sex == 'F']),
            'applicants_coached': cg_qs.filter(activity_type='coaching').count(),
            'jobs_fairs_conducted': PESOActivities.objects.filter(
                created_at__gte=start_date, created_at__lt=end_date
            ).count(),
        })

        return matrix

    def _get_month_name(self, month_str):
        if not month_str:
            return ''
        try:
            clean_key = str(int(month_str))
            return self.MONTH_NAMES.get(clean_key, '')
        except (ValueError, TypeError):
            return ''

    def _build_context(self, request, **kwargs):
        month = kwargs.get('month', '')
        return {
            'matrix_visible': kwargs.get('matrix_visible', False),
            'selected_province': 'Leyte',
            'selected_municipality': kwargs.get('municipality', ''),
            'selected_month': month,
            'selected_month_name': self._get_month_name(month),
            'selected_year': kwargs.get('year', ''),
            'metrics': kwargs.get('metrics', self._get_zero_matrix()),
            'issues_concerns': kwargs.get('issues_concerns', '')
        }

    def get(self, request, *args, **kwargs):
        if kwargs.get('excel'):
            return self.excel(request, *args, **kwargs)

        municipality = request.GET.get('municipality', '').strip()
        month = request.GET.get('month', '').strip()
        year = request.GET.get('year', '').strip()
        metrics = self._get_zero_matrix()
        matrix_visible = False

        if month and year:
            try:
                metrics = self._generate_peso_matrix(int(year), int(month), municipality)
                matrix_visible = True
            except (TypeError, ValueError):
                pass

        context = self._build_context(
            request,
            matrix_visible=matrix_visible,
            municipality=municipality,
            month=month,
            year=year,
            metrics=metrics,
        )
        return render(request, self.template_name, context)

    def excel(self, request, *args, **kwargs):
        month = request.GET.get('month', '').strip()
        year = request.GET.get('year', '').strip()
        municipality = request.GET.get('municipality', '').strip()
        other_accomplishments = request.GET.get('other_accomplishments', '').strip()
        issues_concerns = request.GET.get('issues_concerns', '').strip()

        if not month or not year:
            return HttpResponse('Month and year are required.', status=400)

        try:
            metrics = self._generate_peso_matrix(int(year), int(month), municipality)
        except (TypeError, ValueError):
            return HttpResponse('Invalid month or year.', status=400)

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = 'PESO Report'

        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.worksheet.page import PageMargins

        thin_gray = Side(style='thin', color='CBD5E1')
        border = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
        title_fill = PatternFill('solid', fgColor='0F172A')
        section_fill = PatternFill('solid', fgColor='E2E8F0')
        subsection_fill = PatternFill('solid', fgColor='F1F5F9')
        header_fill = PatternFill('solid', fgColor='CBD5E1')

        worksheet.merge_cells('A1:C1')
        worksheet['A1'] = 'PESO MONITORING REPORT'
        worksheet['A1'].font = Font(bold=True, size=16, color='FFFFFF')
        worksheet['A1'].fill = title_fill
        worksheet['A1'].alignment = Alignment(horizontal='center')
        worksheet.append(['Province of Leyte', 'Leyte', ''])
        worksheet.append(['Municipality / City', municipality, ''])
        worksheet.append(['For the month of', f'{self._get_month_name(month)} {year}', ''])
        worksheet.append([])
        worksheet.append(['INDICATORS', 'TOTAL', 'FEMALE'])

        for cell in worksheet[5]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')

        def add_section(label, subsection=False):
            worksheet.append([label, '', ''])
            row = worksheet.max_row
            worksheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
            cell = worksheet.cell(row=row, column=1)
            cell.font = Font(bold=True)
            cell.fill = subsection_fill if subsection else section_fill
            cell.border = border

        def add_metric(label, total_key, female_key=None):
            worksheet.append([
                label,
                metrics.get(total_key, 0),
                metrics.get(female_key, 0) if female_key else 'N/A',
            ])
            row = worksheet.max_row
            for cell in worksheet[row]:
                cell.border = border
                cell.alignment = Alignment(vertical='top', wrap_text=True)
            worksheet.cell(row=row, column=2).alignment = Alignment(horizontal='center')
            worksheet.cell(row=row, column=3).alignment = Alignment(horizontal='center')

        add_section('1. EMPLOYMENT FACILITATION')
        add_section('1.1 JOB SEARCH ASSISTANCE', True)
        add_metric('Vacancies posted in PEIS', 'vacancies_posted')
        add_metric('Employers / Businesses Registered in PEIS', 'employers_registered')
        add_metric('Job Applicants Registered in PEIS', 'applicants_registered', 'applicants_registered_female')
        add_metric('Referred for Job Placement', 'referred_placement', 'referred_placement_female')
        add_metric('Job Applicants Placed', 'applicants_placed', 'applicants_placed_female')
        add_metric('Private sector (hired employees)', 'placed_private', 'placed_private_female')
        add_metric('Government sector', 'placed_gov', 'placed_gov_female')
        add_metric('Overseas', 'placed_overseas', 'placed_overseas_female')
        add_metric('Placement Rate of Referred Applicants', 'placement_rate')
        add_section('1.2 LOCAL RECRUITMENT ASSISTANCE (LRA)', True)
        add_metric('Qualified Applicants', 'lra_qualified')
        add_metric('Near Hire Applicants', 'lra_near_hire')
        add_section('1.3 SPECIAL RECRUITMENT ASSISTANCE (SRA)', True)
        add_metric('Qualified Applicants', 'sra_qualified')
        add_metric('Near Hire Applicants', 'sra_near_hire')
        add_section('1.4 JOBS FAIR', True)
        add_metric('Jobs Fairs Conducted', 'jobs_fairs_conducted')
        add_metric('Applicants / HOTS', 'fair_applicants_total')
        add_metric('Applicants Hired on the Spot', 'fair_hots')
        add_metric('Job Applicants Referred', 'fair_referred')

        add_section('2. YOUTH-BRIDGING EMPLOYMENT ASSISTANCE')
        add_section('2.1 SPECIAL PROGRAM FOR THE EMPLOYMENT OF STUDENTS (SPES)', True)
        for label, key in [
            ('Elementary', 'spes_elementary'), ('Junior High School', 'spes_jhs'),
            ('Senior High School', 'spes_shs'), ('College', 'spes_college'),
            ('Tech-Voc', 'spes_tech_voc'), ('Out-of-School Youth', 'spes_osy'),
            ('SPES Beneficiaries Graduated', 'spes_graduates'),
            ('SPES Beneficiaries with NCs', 'spes_nc'),
            ('Absorbed SPES Beneficiaries', 'spes_absorbed'),
        ]:
            add_metric(label, key)
        add_section('2.2 GOVERNMENT INTERNSHIP PROGRAM (GIP)', True)
        add_metric('Youth Placed', 'gip_total', 'gip_female')
        for label, key in [
            ('Alternative Learning System', 'gip_als'), ('Junior High School', 'gip_jhs'),
            ('Senior High School', 'gip_shs'), ('Tech-Voc', 'gip_tech_voc'),
            ('College', 'gip_college'), ('GIP Graduates with NCs', 'gip_graduates_nc'),
            ('Absorbed GIP Interns', 'gip_absorbed'),
        ]:
            add_metric(label, key)

        add_section('3. PESO-LED ADVOCACY AND TRAININGS')
        add_section('3.1 LABOR MARKET INFORMATION ACTIVITIES', True)
        add_metric('Youth (30 years old and below)', 'lmi_youth', 'lmi_youth_female')
        add_metric('Non-youth (31 years old and above)', 'lmi_non_youth', 'lmi_non_youth_female')
        add_metric('Job Applicants Coached', 'applicants_coached')

        add_section('4. DOLE INTEGRATED LIVELIHOOD AND EMERGENCY EMPLOYMENT PROGRAM (DILEEP)')
        add_metric('Total workers provided livelihood assistance', 'dilp_total_workers')
        add_metric('Individual Projects', 'individual_assistance_total')
        add_metric('Group Projects', 'group_assistance_total')
        add_section('4.2 TUPAD PROJECTS', True)
        add_metric('Workers provided emergency employment assistance', 'tupad_total')
        add_metric('Short-term (10-30 days)', 'tupad_short')
        add_metric('Long-term (31-90 days)', 'tupad_long')

        add_section('5. CHILD LABOR PREVENTION AND ELIMINATION PROGRAM')
        for label, key in [
            ('Project Angel Tree', 'child_angel_tree'),
            ('Livelihood assistance to parents / guardians', 'child_parent_livelihood'),
            ('Rescue operations conducted through SBM', 'child_rescue'),
            ('LGU / PESO-led Assistance 1', 'child_lgu_assist1'),
            ('LGU / PESO-led Assistance 2', 'child_lgu_assist2'),
        ]:
            add_metric(label, key)

        add_section('6. OTHER PESO ACCOMPLISHMENTS')
        worksheet.append([other_accomplishments or 'None recorded', '', ''])
        other_row = worksheet.max_row
        worksheet.merge_cells(start_row=other_row, start_column=1, end_row=other_row, end_column=3)
        worksheet.cell(row=other_row, column=1).border = border
        worksheet.cell(row=other_row, column=1).alignment = Alignment(wrap_text=True, vertical='top')
        worksheet.row_dimensions[other_row].height = 42

        add_section('7. MONTHLY LABOR MARKET ANALYSIS')
        for label, key in [
            ('Projected City / Municipal Population', 'pop_projected'),
            ('Estimated City / Municipal Poor Population', 'pop_poor'),
            ('Projected City / Municipal Working Population', 'pop_working'),
            ('Labor Force Participation Rate', 'lfpr'),
            ('Labor Force in the City / Municipality', 'labor_force_count'),
            ('Employment Rate', 'employment_rate'),
            ('Employed Persons', 'employed_count'),
            ('Unemployment Rate', 'unemployment_rate'),
            ('Unemployed Persons', 'unemployed_count'),
            ('Underemployment Rate', 'underemployment_rate'),
            ('Underemployed Persons', 'underemployed_count'),
        ]:
            add_metric(label, key)

        add_section('8. ISSUES AND CONCERNS')
        worksheet.append([issues_concerns or 'None recorded', '', ''])
        issues_row = worksheet.max_row
        worksheet.merge_cells(start_row=issues_row, start_column=1, end_row=issues_row, end_column=3)
        worksheet.cell(row=issues_row, column=1).border = border
        worksheet.cell(row=issues_row, column=1).alignment = Alignment(wrap_text=True, vertical='top')
        worksheet.row_dimensions[issues_row].height = 60

        worksheet.column_dimensions['A'].width = 56
        worksheet.column_dimensions['B'].width = 16
        worksheet.column_dimensions['C'].width = 16
        worksheet.page_setup.paperSize = worksheet.PAPERSIZE_LEGAL
        worksheet.page_setup.orientation = worksheet.ORIENTATION_PORTRAIT
        worksheet.page_setup.fitToWidth = 1
        worksheet.page_setup.fitToHeight = 0
        worksheet.sheet_properties.pageSetUpPr.fitToPage = True
        worksheet.page_margins = PageMargins(
            left=0.75,
            right=0.75,
            top=0.75,
            bottom=0.75,
            header=0.15,
            footer=0.15,
        )
        worksheet.sheet_view.showGridLines = False
        for row in worksheet.iter_rows(min_row=2, max_row=4, max_col=3):
            for cell in row:
                cell.border = border
        for row in worksheet.iter_rows():
            worksheet.row_dimensions[row[0].row].height = 22

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="peso_report_{year}_{int(month):02d}.xlsx"'
        )
        workbook.save(response)
        return response

class AccountSettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'account_settings.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'name_form': EditProfileNameForm(instance=request.user),
            'password_form': PasswordChangeForm(user=request.user)
        })

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        user = request.user

        # --- ACTION: UPDATE NAME / PROFILE ---
        if action == 'update_profile':
            name_form = EditProfileNameForm(request.POST, instance=user)
            if name_form.is_valid():
                name_form.save()
                messages.success(request, "Profile information updated successfully.")
                return redirect('AdminSide:account_settings')

            messages.error(request, "Please check the form inputs for errors.")
            return render(request, self.template_name, {
                'name_form': name_form,
                'password_form': PasswordChangeForm(user=user),
            })

        # --- ACTION: UPDATE AVATAR PHOTO ---
        elif action == 'update_avatar':
            avatar_file = request.FILES.get('avatar')
            if avatar_file:
                # Assigns to user model profile_picture field if present
                if hasattr(user, 'profile_picture'):
                    user.profile_picture = avatar_file
                    user.save()
                    messages.success(request, "Profile picture updated successfully.")
                else:
                    messages.error(request, "Profile picture field is not configured on the User model.")
            else:
                messages.error(request, "Please select a valid image file to upload.")

            return redirect('AdminSide:account_settings')

        # --- ACTION 1: REQUEST OTP FOR EMAIL UPDATE ---
        elif action == 'request_email_otp':
            new_email = request.POST.get('email', '').strip()
            username = request.POST.get('username', '').strip()

            otp = f"{random.randint(100000, 999999)}"
            request.session['email_otp'] = otp
            request.session['pending_email'] = new_email
            request.session['pending_username'] = username

            send_mail(
                subject="PESO Admin - Verification Code",
                message=f"Hello {user.first_name},\n\nYour OTP code to update your email address is: {otp}",
                from_email=None,
                recipient_list=[new_email],
                fail_silently=False,
            )

            messages.info(request, f"Verification code sent to {new_email}.")
            return render(request, self.template_name, {
                'password_form': PasswordChangeForm(user=user),
                'show_email_otp_modal': True
            })

        # --- ACTION 2: VERIFY EMAIL OTP ---
        elif action == 'verify_email_otp':
            input_otp = request.POST.get('otp', '').strip()
            stored_otp = request.session.get('email_otp')

            if stored_otp and input_otp == stored_otp:
                user.email = request.session.pop('pending_email', user.email)
                user.username = request.session.pop('pending_username', user.username)
                user.save()
                del request.session['email_otp']

                messages.success(request, "Email address updated successfully.")
            else:
                messages.error(request, "Invalid or expired OTP code.")

            return redirect('AdminSide:account_settings')

        # --- ACTION 3: REQUEST OTP FOR PASSWORD CHANGE ---
        elif action == 'request_password_otp':
            form = PasswordChangeForm(user=user, data=request.POST)
            if form.is_valid():
                request.session['pending_password_data'] = request.POST.dict()

                otp = f"{random.randint(100000, 999999)}"
                request.session['password_otp'] = otp

                send_mail(
                    subject="PESO Admin - Password Security Code",
                    message=f"Hello {user.first_name},\n\nYour security OTP to confirm your password change is: {otp}",
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                messages.info(request, f"Security code sent to your registered email ({user.email}).")
                return render(request, self.template_name, {
                    'password_form': form,
                    'show_password_otp_modal': True
                })
            else:
                messages.error(request, "Please correct the password errors below.")
                return render(request, self.template_name, {
                    'password_form': form,
                    'open_password_modal': True
                })

        # --- ACTION 4: VERIFY PASSWORD OTP ---
        elif action == 'verify_password_otp':
            input_otp = request.POST.get('otp', '').strip()
            stored_otp = request.session.get('password_otp')

            if stored_otp and input_otp == stored_otp:
                password_data = request.session.pop('pending_password_data', None)
                del request.session['password_otp']

                if password_data:
                    form = PasswordChangeForm(user=user, data=password_data)
                    if form.is_valid():
                        updated_user = form.save()
                        update_session_auth_hash(request, updated_user)
                        messages.success(request, "Password updated successfully.")
                    else:
                        messages.error(request, "Form validation failed. Please try again.")
            else:
                messages.error(request, "Invalid security OTP code.")

            return redirect('AdminSide:account_settings')

        return redirect('AdminSide:account_settings')

class HelpView(LoginRequiredMixin, TemplateView):
    template_name = 'help.html'
    support_email = 'capessonect650@gmail.com'

    def post(self, request, *args, **kwargs):
        subject = request.POST.get('subject', '').strip()
        message_body = request.POST.get('message', '').strip()
        error = None

        if not subject or not message_body:
            error = "Enter both a subject and a description of the issue."
        elif len(subject) > 150:
            error = "The subject must be 150 characters or fewer."
        elif '\r' in subject or '\n' in subject:
            error = "The subject must be a single line."
        elif len(message_body) > 5000:
            error = "The report must be 5,000 characters or fewer."

        try:
            validate_email(request.user.email)
        except ValidationError:
            error = "Add a valid email address to your account settings before contacting support."

        if error:
            messages.error(request, error)
            return self.render_to_response(self.get_context_data(
                support_modal_open=True,
                support_subject=subject,
                support_message=message_body,
            ))

        email = EmailMessage(
            subject=f"CAPESONNECT Support: {subject}",
            body=(
                f"Support request from {request.user.get_full_name() or request.user.username}\n"
                f"Reply-to: {request.user.email}\n\n"
                f"{message_body}"
            ),
            from_email=None,
            to=[self.support_email],
            reply_to=[request.user.email],
        )

        try:
            sent_count = email.send()
        except (OSError, SMTPException):
            logger.exception("Failed to send a CAPESONNECT support request.")
            messages.error(request, "The report could not be sent. Please try again later.")
            return self.render_to_response(self.get_context_data(
                support_modal_open=True,
                support_subject=subject,
                support_message=message_body,
            ))

        if sent_count != 1:
            messages.error(request, "The report could not be sent. Please try again later.")
            return self.render_to_response(self.get_context_data(
                support_modal_open=True,
                support_subject=subject,
                support_message=message_body,
            ))

        messages.success(request, "Your support report was sent successfully.")
        return redirect('AdminSide:account_help')

class NotificationListView(LoginRequiredMixin, ListView):
    """
    Renders the dedicated notification inbox page listing all notifications 
    for the current user with read/unread filtering.
    """
    model = Notification
    template_name = 'notifications.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        status_filter = self.request.GET.get('status', 'all').lower()

        if status_filter == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status_filter == 'read':
            queryset = queryset.filter(is_read=True)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_notifications = Notification.objects.filter(recipient=self.request.user)
        
        context.update({
            'unread_count': user_notifications.filter(is_read=False).count(),
            'total_count': user_notifications.count(),
            'selected_status': self.request.GET.get('status', 'all'),
        })
        return context

class NotificationHeaderApiView(LoginRequiredMixin, View):
    """
    AJAX endpoint returning the unread count and the 5 newest notifications
    for the navbar dropdown while keeping read notifications visible.
    """
    def get(self, request, *args, **kwargs):
        user_notifications = Notification.objects.filter(recipient=request.user)
        latest_qs = user_notifications.order_by('-created_at')[:5]

        data = {
            'unread_count': user_notifications.filter(is_read=False).count(),
            'total_count': user_notifications.count(),
            'notifications': [
                {
                    'id': str(n.id) if hasattr(n, 'id') else str(n.uuid),
                    'title': getattr(n, 'title', 'Notification'),
                    'message': getattr(n, 'message', str(n)),
                    'notification_type': getattr(n, 'notification_type', 'info'),
                    'category_label': n.get_notification_type_display(),
                    'target_url': getattr(n, 'target_url', '#'),
                    'created_at': n.created_at.strftime('%b %d, %Y %I:%M %p') if hasattr(n, 'created_at') else '',
                    'is_read': n.is_read,
                }
                for n in latest_qs
            ]
        }
        return JsonResponse(data)

class MarkNotificationAsReadView(LoginRequiredMixin, View):
    """
    Marks a single notification as read. Supports both standard POST redirects and AJAX calls.
    """
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()})

        # Redirect to target_url if present, otherwise default to inbox
        redirect_url = getattr(notification, 'target_url', None) or request.META.get('HTTP_REFERER', 'AdminSide:notifications_list')
        return redirect(redirect_url)

class MarkAllNotificationsAsReadView(LoginRequiredMixin, View):
    """
    Marks all unread notifications for the current user as read.
    """
    def post(self, request, *args, **kwargs):
        updated_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).update(is_read=True)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'updated_count': updated_count, 'unread_count': 0})

        messages.success(request, f"Marked {updated_count} notification(s) as read.")
        return redirect(request.META.get('HTTP_REFERER', 'AdminSide:notifications_list'))

class DeleteNotificationView(LoginRequiredMixin, View):
    """
    Deletes a single notification record.
    """
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()})

        messages.success(request, "Notification deleted.")
        return redirect('AdminSide:notifications_list')
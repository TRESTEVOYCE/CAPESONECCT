import calendar
import json
from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .models import ApplicantProfile, AppliedJobs, EmployerProfile, Jobs


class DashboardView(TemplateView):
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
        job_type_counts = Jobs.objects.values('job_type').annotate(count=Count('id'))
        job_type_lookup = {item['job_type']: item['count'] for item in job_type_counts}
        sector_items = []
        colors = ['#1d3d75', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#94a3b8']
        
        for code, label in Jobs.JOB_TYPE_CHOICES:
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
        # Read Filtering Parameters
        search_query = request.GET.get('search', '').strip()
        sector_filter = request.GET.get('sector', '').strip()
        status_filter = request.GET.get('status', '').strip()

        # Database Query Construction
        jobs = Jobs.objects.all().select_related('employer').order_by('-job_id_number')

        # Baseline Status Counters
        total_active = Jobs.objects.filter(status='Active').count()
        total_pending = Jobs.objects.filter(status='Pending').count()

        # Execute Queries Filters
        if search_query:
            jobs = jobs.filter(
                Q(job_title__icontains=search_query) |
                Q(employer__company_name__icontains=search_query) |
                Q(job_id_number__icontains=search_query.replace('JP-', '').replace('jp-', ''))
            )
        if sector_filter and sector_filter != "All":
            jobs = jobs.filter(sector=sector_filter)
        if status_filter and status_filter != "All":
            jobs = jobs.filter(status=status_filter)

        total_results = jobs.count()

        context = {
            'jobs': jobs,
            'total_active': total_active,
            'total_pending': total_pending,
            'total_results': total_results,
            'search_query': search_query,
            'selected_sector': sector_filter,
            'selected_status': status_filter,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Create or resolve default placeholder profile for admin postings
        admin_employer, _ = EmployerProfile.objects.get_or_create(
            company_name="PESO Internal Postings",
            defaults={"location": "Manila"}
        )

        # Generate automatic incremented numeric string ID entries
        last_job = Jobs.objects.order_by('-job_id_number').first()
        next_numeric_id = (last_job.job_id_number + 1) if (last_job and last_job.job_id_number) else 301

        # Process dates expiration values
        expiry_date = timezone.now() + timedelta(days=30)

        # Insert new Record
        Jobs.objects.create(
            job_id_number=next_numeric_id,
            job_title=request.POST.get('job_title'),
            sector=request.POST.get('sector'),
            job_description=request.POST.get('job_description', 'No description provided.'),
            job_requirements=request.POST.get('job_requirements', 'No requirements provided.'),
            job_location=request.POST.get('job_location', 'Manila'),
            job_type=request.POST.get('job_type', 'full_time'),
            vacancy=int(request.POST.get('vacancy', 1)),
            salary=float(request.POST.get('salary', 0)),
            employer=admin_employer,
            status=request.POST.get('status', 'Active'),
            job_posting_expiry=expiry_date
        )
        return redirect('job_postings_list')
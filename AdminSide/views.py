import calendar
import json
from datetime import datetime, timedelta
from django.db.models import Count, Q, OuterRef, Subquery
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, ListView
from .models import ApplicantProfile, AppliedJobs, EmployerProfile, Jobs, OfferedJobs, SpecialProgramForEmploymentOfStudents, GovernmentInternshipProgram, TupadBeneficiary, DisplacedInformalLaborProgram, JobStartBeneficiary
from .service import generate_complete_peso_matrix

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
        applicant_uuid = request.POST.get('applicant_uuid')
        new_status = request.POST.get('status')
        
        if new_status in ['approved', 'rejected']:
            applicant = get_object_or_404(ApplicantProfile, uuid=applicant_uuid)
            applicant.status = new_status
            applicant.save()
            messages.success(request, f"Application for {applicant.first_name} has been verified successfully.")
            
        return redirect('applicant_registry')
    
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
        self.active_program = self.request.GET.get('program', 'spes').lower()
        self.search_query = self.request.GET.get('search', '').strip()

        # Route baseline queryset across the 5 sub-models
        if self.active_program == 'gip':
            queryset = GovernmentInternshipProgram.objects.all().order_by('-created_at')
        elif self.active_program == 'tupad':
            queryset = TupadBeneficiary.objects.all().order_by('-created_at')
        elif self.active_program == 'dilp':
            queryset = DisplacedInformalLaborProgram.objects.all().order_by('-created_at')
        elif self.active_program == 'jobstart':
            queryset = JobStartBeneficiary.objects.all().order_by('-created_at')
        else:
            self.active_program = 'spes'
            queryset = SpecialProgramForEmploymentOfStudents.objects.all().order_by('-created_at')

        # Global Text Search Filter
        if self.search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=self.search_query) |
                Q(last_name__icontains=self.search_query) |
                Q(barangay__icontains=self.search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Global registry indicators
        global_program_counts = {
            'spes_count': SpecialProgramForEmploymentOfStudents.objects.count(),
            'gip_count': GovernmentInternshipProgram.objects.count(),
            'tupad_count': TupadBeneficiary.objects.count(),
            'dilp_count': DisplacedInformalLaborProgram.objects.count(),
            'jobstart_count': JobStartBeneficiary.objects.count(),
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
        elif self.active_program == 'jobstart':
            program_kpis = JobStartBeneficiary.objects.aggregate(
                total=Count('uuid'),
                female=Count('uuid', filter=Q(sex='F')),
                lst_completed=Count('uuid', filter=Q(current_phase='lst_completed')),
                tst_completed=Count('uuid', filter=Q(current_phase='tst_completed')),
                internship=Count('uuid', filter=Q(current_phase='internship')),
                employed=Count('uuid', filter=Q(is_placed_or_employed=True))
            )

        # 3. Dynamic age parsing
        current_year = timezone.now().year
        beneficiaries_list = list(context['beneficiaries'])
        for b in beneficiaries_list:
            b.computed_age = current_year - b.date_of_birth.year if b.date_of_birth else "--"

        context.update({
            'active_program': self.active_program,
            'search_query': self.search_query,
            'globals': global_program_counts,
            'kpis': program_kpis,
            'beneficiaries': beneficiaries_list
        })
        return context
    
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
            'vacancies_posted_total': 0, 'hired_private_total': 0, 'hired_private_female': 0,
            'fairs_conducted': 0, 'hots_total': 0, 'spes_elem': 0, 'spes_college': 0,
            'gip_total': 0, 'gip_female': 0, 'lmi_youth_total': 0, 'lmi_youth_female': 0,
            'child_labor_total': 0, 'child_labor_referred': 0, 'pop_projected': 0, 
            'lfpr': '0.0%', 'employment_rate': '0.0%'
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
    
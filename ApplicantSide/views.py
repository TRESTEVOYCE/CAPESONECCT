from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from JobMatchingEngine.database import get_job_collection, build_applicant_profile_text
from AdminSide.models import Jobs, ApplicantProfile, AppliedJobs, SavedJobs, ApplicantSkills
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import ProfilePictureForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ApplicantEducationForm, ApplicantPersonalInfoForm, ApplicantSkillFormSet, ApplicantPreferredJobForm,ApplicantDocumentsForm,ApplicantSkillForm,ProfilePictureForm
from django.views import View


 
class ApplicantPersonalInfoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ApplicantProfile
    form_class = ApplicantPersonalInfoForm
    template_name = 'applicant_personal_info_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ApplicantEducationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ApplicantProfile
    form_class = ApplicantEducationForm
    template_name = 'applicant_education_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ApplicantPreferredJobCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ApplicantProfile
    form_class = ApplicantPreferredJobForm
    template_name = 'applicant_preferred_job_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ApplicantDocumentsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ApplicantProfile
    form_class = ApplicantDocumentsForm
    template_name = 'applicant_documents_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ApplicantSkillCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ApplicantSkills
    form_class = ApplicantSkillForm
    template_name = 'applicant_skill_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def form_valid(self, form):
        response = super().form_valid(form)
        applicant = self.request.user.applicant_profile
        applicant.skills.add(self.object)
        return response
    

class ApplicantPersonalUpdateInfoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPersonalInfoForm
    template_name = 'applicant_personal_info_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, _ = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile
    

class ApplicantEducationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantEducationForm
    template_name = 'applicant_education_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, _ = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile


class ApplicantSkillUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantSkillFormSet
    template_name = 'applicant_skill_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, _ = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile


class ApplicantPreferredJobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPreferredJobForm
    template_name = 'applicant_preferred_job_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, _ = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile


class ApplicantDocumentsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantDocumentsForm
    template_name = 'applicant_documents_form.html'
    success_url = reverse_lazy('applicant-dashboard')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, _ = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile


class ApplicantProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ApplicantProfile
    success_url = reverse_lazy('login')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)


class LogoutView(LoginRequiredMixin, UserPassesTestMixin, DjangoLogoutView):
    success_url = reverse_lazy('landing_page') 

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'
    

class DashBoardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'applicant-dashboard.html'
    context_object_name = 'matching_jobs'
    login_url = '/signin/'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        applicant_profile = ApplicantProfile.objects.filter(
            user=self.request.user
        ).first()

        if applicant_profile:
            # Build applicant profile text for AI matching
            applicant_profile_text = build_applicant_profile_text(
                applicant_profile
            )

            # Get ChromaDB job collection
            collection = get_job_collection()

            # Find jobs similar to the applicant's profile
            results = collection.query(
                query_texts=[applicant_profile_text],
                n_results=10
            )

            # Get job UUIDs returned by ChromaDB
            job_uuids = [
                result['metadata']['job_uuid']
                for result in results['results'][0]['matches']
            ]

            # Get matching active jobs from Django database
            matching_jobs = Jobs.objects.filter(
                uuid__in=job_uuids,
                status='Active'
            )

            # If there are AI matches, show them.
            # Otherwise, show all active jobs.
            if matching_jobs.exists():
                context['matching_jobs'] = matching_jobs
            else:
                context['matching_jobs'] = Jobs.objects.filter(
                    status='Active'
                )

            # Applicant's applications
            applications = AppliedJobs.objects.filter(
                applicant=applicant_profile
            )

            context['application_count'] = applications.count()

            # Saved jobs
            context['saved_jobs_count'] = SavedJobs.objects.filter(
                applicant=applicant_profile
            ).count()

            # Applications under review
            context['under_review_count'] = applications.filter(
                status__in=['pending', 'reviewed']
            ).count()

            # Applications for interview
            context['shortlisted_count'] = applications.filter(
                status='for interview'
            ).count()

            # Rejected applications
            context['rejected_count'] = applications.filter(
                status='rejected'
            ).count()

            # Withdrawn applications
            context['withdrawn_count'] = applications.filter(
                status='withdrawn'
            ).count()

            # Profile completion
            completed = 0
            total = 6

            if (
                applicant_profile.first_name
                and applicant_profile.last_name
            ):
                completed += 1

            if (
                applicant_profile.education_level
                and applicant_profile.school_name
            ):
                completed += 1

            if applicant_profile.skills.exists():
                completed += 1

            if applicant_profile.preferred_job.exists():
                completed += 1

            if (
                applicant_profile.resume
                or applicant_profile.curriculum_vitae
            ):
                completed += 1

            if applicant_profile.applicant_id_picture:
                completed += 1

            context['profile_strength'] = int(
                (completed / total) * 100
            )

        else:
            # No applicant profile
            context['matching_jobs'] = Jobs.objects.filter(
                status='Active'
            )

            context['application_count'] = 0
            context['saved_jobs_count'] = 0
            context['under_review_count'] = 0
            context['shortlisted_count'] = 0
            context['rejected_count'] = 0
            context['withdrawn_count'] = 0
            context['profile_strength'] = 0
        # Total number of active jobs
        context['total_jobs'] = Jobs.objects.filter(
            status='Active'
        ).count()

        return context
    
class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def get_queryset(self):
        jobs = Jobs.objects.filter(status='Active')

        # Search
        q = self.request.GET.get('q')

        if q:
            jobs = jobs.filter(
                Q(job_title__icontains=q) |
                Q(job_description__icontains=q) |
                Q(employer__business_name__icontains=q)
            )

        # Location
        location = self.request.GET.get('location')

        if location:
            jobs = jobs.filter(
                place_of_work__icontains=location
            )

        # Job type / nature of work
        job_types = self.request.GET.getlist('job_type')

        if job_types:
            jobs = jobs.filter(
                nature_of_work__in=job_types
            )

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        applicant_profile = ApplicantProfile.objects.filter(
            user=self.request.user
        ).first()

        # Keep track of selected Quick Filters
        context['selected_job_types'] = self.request.GET.getlist(
            'job_type'
        )

        available_jobs = self.get_queryset()

        if applicant_profile:
            applicant_text = build_applicant_profile_text(
                applicant_profile
            )

            collection = get_job_collection()

            results = collection.query(
                query_texts=[applicant_text],
                n_results=10
            )

            job_uuids = [
                result['metadata']['job_uuid']
                for result in results['results'][0]['matches']
            ]

            matching_jobs = available_jobs.filter(
                uuid__in=job_uuids
            )

            # If there are matching jobs, show them.
            # Otherwise, fallback to normal active jobs.
            if matching_jobs.exists():
                context['matching_jobs'] = matching_jobs
            else:
                context['matching_jobs'] = available_jobs

        else:
            context['matching_jobs'] = available_jobs

        return context
    
class JobDetailsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Jobs
    template_name = 'job_details.html'
    context_object_name = 'job'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )


class SortJobView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    context_object_name = 'matching_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_queryset(self):
        sort_by = self.request.GET.get('sort_by', 'date_posted')
        if sort_by == 'date_posted':
            return Jobs.objects.all().order_by('-date_posted')
        elif sort_by == 'salary':
            return Jobs.objects.all().order_by('-salary')
        else:
            return Jobs.objects.all()


class AppliedJobsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AppliedJobs
    template_name = 'applied_jobs.html'
    context_object_name = 'applied_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_queryset(self):
        try:
            applicant_profile = self.request.user.applicant_profile
        except ApplicantProfile.DoesNotExist:
            return AppliedJobs.objects.none()
        return AppliedJobs.objects.filter(applicant=applicant_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = self.get_queryset()

        context['applied_count'] = applications.count()
        context['endorsed_count'] = applications.filter(status__in=['endorsed', 'approved']).count()
        context['interviewed_count'] = applications.filter(status='for interview').count()
        context['hired_count'] = applications.filter(status='hired').count()
        return context


class SavedJobsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SavedJobs
    template_name = 'saved_jobs.html'
    context_object_name = 'saved_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_queryset(self):
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        if applicant_profile:
            return applicant_profile.saved_jobs.all()
        return SavedJobs.objects.none()


class SearchJobView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def get_queryset(self):
        jobs = Jobs.objects.filter(
            status='Active'
        )

        # Search
        q = self.request.GET.get('q')

        if q:
            jobs = jobs.filter(
                Q(job_title__icontains=q) |
                Q(job_description__icontains=q) |
                Q(employer__business_name__icontains=q)
            )

        # Location
        location = self.request.GET.get('location')

        if location:
            jobs = jobs.filter(
                place_of_work__icontains=location
            )

        # Job type / nature of work
        job_types = self.request.GET.getlist('job_type')

        if job_types:
            jobs = jobs.filter(
                nature_of_work__in=job_types
            )

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Keep selected quick filters checked
        context['selected_job_types'] = self.request.GET.getlist(
            'job_type'
        )

        return context
class ApplyJobView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def post(self, request, pk):

        applicant_profile = ApplicantProfile.objects.filter(
            user=request.user
        ).first()

        if not applicant_profile:
            messages.warning(
                request,
                'Please complete your Profile first.'
            )
            return redirect('applicant-dashboard')

        if applicant_profile.status != 'approved':
            messages.warning(
                request,
                'Your applicant profile must be approved before you can apply for jobs.'
            )
            return redirect('job_details', pk=pk)

        job = get_object_or_404(
            Jobs,
            pk=pk,
            status='Active'
        )

        if AppliedJobs.objects.filter(
            applicant=applicant_profile,
            applied_job=job
        ).exists():
            messages.warning(
                request,
                'You have already applied for this job.'
            )
            return redirect('job_details', pk=job.pk)

        AppliedJobs.objects.create(
            employer=job.employer,
            applicant=applicant_profile,
            applied_job=job,
            status='pending'
        )

        messages.success(
            request,
            'Your application has been submitted successfully.'
        )

        return redirect('applied_jobs')

class SaveJobView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def post(self, request, pk):

        applicant_profile = ApplicantProfile.objects.filter(
            user=request.user
        ).first()

        if not applicant_profile:
            messages.warning(
                request,
                'Please complete your profile first.'
            )
            return redirect('applicant-dashboard')

        job = get_object_or_404(
            Jobs,
            pk=pk,
            status='Active'
        )

        saved_job, created = SavedJobs.objects.get_or_create(
            applicant=applicant_profile,
            saved_job=job
        )

        if created:
            messages.success(
                request,
                'Job saved successfully.'
            )
        else:
            messages.info(
                request,
                'You have already saved this job.'
            )

        return redirect('job_details', pk=job.pk)


@login_required
def edit_profile_picture(request):
    if not (getattr(request.user, 'role', None) == 'applicant'):
        return redirect('login')
    
    # Safe lookup: prevents 404 if profile hasn't been created via personal_info yet
    profile = ApplicantProfile.objects.filter(user=request.user).first()
    #if not profile:
       # messages.warning(request, 'Please complete your personal info setup first.')
        #return redirect('personal_info')
    
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('personal_info')
    else:
        form = ProfilePictureForm(instance=profile)
    
    return render(request, 'edit_profile_picture.html', {'form': form})


@login_required
def view_profile(request):
    if not (getattr(request.user, 'role', None) == 'applicant'):
        return redirect('login')
    
    profile = ApplicantProfile.objects.filter(user=request.user).first()
    #if not profile:
        #messages.warning(request, 'Please complete your personal info setup first.')
       # return redirect('personal_info')
    
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('view_profile')
    else:
        form = ProfilePictureForm(instance=profile)
    
    return render(request, 'view_profile.html', {
        'profile': profile,
        'form': form
    })
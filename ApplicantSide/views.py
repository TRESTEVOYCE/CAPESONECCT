from django.shortcuts import render, redirect
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
from .forms import (
    ApplicantEducationForm, 
    ApplicantPersonalInfoForm, 
    ApplicantSkillFormSet, 
    ApplicantPreferredJobForm, 
    ApplicantDocumentsForm,
    ApplicantSkillForm,
    ProfilePictureForm
)
 
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
    login_url = '/login/'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        applicant_profile = ApplicantProfile.objects.filter(
            user=self.request.user
        ).first()

        if applicant_profile:
            applicant_profile_text = build_applicant_profile_text(applicant_profile)
            collection = get_job_collection()

            results = collection.query(
                query_texts=[applicant_profile_text],
                n_results=10
            )

            job_uuids = [
                result['metadata']['job_uuid']
                for result in results['results'][0]['matches']
            ]

            context['matching_jobs'] = Jobs.objects.filter(uuid__in=job_uuids)

            applications = AppliedJobs.objects.filter(
                applicant=applicant_profile
            )

            context['application_count'] = applications.count()
            context['saved_jobs_count'] = SavedJobs.objects.filter(applicant=applicant_profile).count()
            context['under_review_count'] = applications.filter(status__in=['pending', 'reviewed']).count()
            context['shortlisted_count'] = applications.filter(status='for interview').count()
            context['rejected_count'] = applications.filter(status='rejected').count()
            context['withdrawn_count'] = 0

            completed = 0
            total = 6

            if applicant_profile.first_name and applicant_profile.last_name:
                completed += 1
            if applicant_profile.education_level and applicant_profile.school_name:
                completed += 1
            if applicant_profile.skills.exists():
                completed += 1
            if applicant_profile.preferred_job.exists():
                completed += 1
            if applicant_profile.resume or applicant_profile.curriculum_vitae:
                completed += 1
            if applicant_profile.applicant_id_picture:
                completed += 1

            context['profile_strength'] = int((completed / total) * 100)

        else:
            context['matching_jobs'] = []
            context['application_count'] = 0
            context['saved_jobs_count'] = 0
            context['under_review_count'] = 0
            context['shortlisted_count'] = 0
            context['rejected_count'] = 0
            context['withdrawn_count'] = 0
            context['profile_strength'] = 0

        context['total_jobs'] = Jobs.objects.filter(status='Active').count()
        return context
    
class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_queryset(self):
        jobs = Jobs.objects.filter(status='Active')
        q = self.request.GET.get('q')
        job_types = self.request.GET.getlist('job_type')

        if q:
            jobs = jobs.filter(
                Q(job_title__icontains=q) |
                Q(job_description__icontains=q) |
                Q(employer__business_name__icontains=q)
            )

        if job_types:
            jobs = jobs.filter(nature_of_work__in=job_types)

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()

        if applicant_profile:
            applicant_text = build_applicant_profile_text(applicant_profile)
            collection = get_job_collection()
            results = collection.query(query_texts=[applicant_text])

            job_uuids = [
                result['metadata']['job_uuid']
                for result in results['results'][0]['matches']
            ]
            context['matching_jobs'] = Jobs.objects.filter(uuid__in=job_uuids)
        else:
            context['matching_jobs'] = []

        return context

    
class JobDetailsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Jobs
    template_name = 'job_details.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_uuid = self.kwargs.get('uuid')
        job = Jobs.objects.filter(uuid=job_uuid).first()
        context['job'] = job
        return context


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
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Jobs.objects.filter(
                Q(job_title__icontains=query) |
                Q(job_description__icontains=query) |
                Q(employer__business_name__icontains=query)
            )
        else:
            return Jobs.objects.all()


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
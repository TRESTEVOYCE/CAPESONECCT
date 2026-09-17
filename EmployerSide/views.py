from django.shortcuts import render, redirect
from AdminSide.models import EmployerProfile, Jobs, AppliedJobs, ApplicantProfile
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView,TemplateView
from .forms import EmployerProfileForm,JobsForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

#home or the dashboard view for the employer
class HomeView(TemplateView):
    template_name = 'home.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def get(self, request, *args, **kwargs):
        # Prevent RelatedObjectDoesNotExist by checking if profile exists first
        if not hasattr(request.user, 'employer_profile'):
            return redirect('register_employer')  # Update with your actual URL name for creating a profile
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Safe to query now because the 'get' method intercept blocks users without profiles
        applied_jobs = AppliedJobs.objects.filter(applied_jobs_employer=self.request.user.employer_profile)
        jobs = Jobs.objects.filter(employer=self.request.user.employer_profile)
        context['applied_jobs'] = applied_jobs.count()
        context['jobs'] = jobs.count()
        return context

    
#view to create an employer profile usually in the profile or settings page
class EmployerProfileCreateView(CreateView):
    model = EmployerProfile
    form_class = EmployerProfileForm
    template_name = 'employer_profile_form.html'
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only create their own profile
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)

    #to ensure that the form is valid and the user is set to the current user
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
#view to list all applicants who have applied to the employer's job postings
class ApplicantsListView(ListView):
    model = AppliedJobs
    template_name = 'applicants_list.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer
    
    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return AppliedJobs.objects.filter(applied_jobs_employer=self.request.user.employer_profile)

#view to display details of a specific applicant
class ApplicantDetailView(DetailView):
    model = ApplicantProfile
    template_name = 'applicant_detail.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_employer
    
    def get_queryset(self):
         return ApplicantProfile.objects.filter(
            applied_jobs__applied_job__employer=self.request.user.employer_profile
            ).distinct()

#view to update the status of an applicant's job application
class ApplicantJobStatusView(UpdateView):
    model = AppliedJobs
    fields = ['status']
    success_url = reverse_lazy('home')

    #to ensure that the employer can only update their own job postings
    def get_queryset(self):
        return AppliedJobs.objects.filter(applied_jobs_employer=self.request.user.employer_profile)

#to ensure that only authenticated employers can access this view
class JobCreationView(CreateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only create their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employer_profile)

    #to ensure that the form is valid and the user is set to the current user
    def form_valid(self, form):
        form.instance.employer = self.request.user.employer_profile
        return super().form_valid(form)

class JobUpdateView(UpdateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only update their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employer_profile)

class JobDeleteView(DeleteView):
    model = Jobs
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only delete their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employer_profile)

class JobListView(ListView):
    model = Jobs
    template_name = 'job_list.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employer_profile)

class JobDetailView(DetailView):
    model = Jobs
    template_name = 'job_detail.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employer_profile)

class CompanyProfileView(DetailView):
    model = EmployerProfile
    template_name = 'company_profile.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only view their own profile
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)

class CompanyProfileUpdateView(UpdateView):
    model = EmployerProfile
    form_class = EmployerProfileForm
    template_name = 'employer_profile_form.html'
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only update their own profile
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)

class AccountDeleteView(DeleteView):
    model = EmployerProfile
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only delete their own profile
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)


class SettingsView(TemplateView):

    template_name = 'settings.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer
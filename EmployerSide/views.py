from django.shortcuts import render
from AdminSide.models import EmployerProfile,Jobs,AppliedJobs,ApplicantProfile
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .forms import EmployerProfileForm,JobsForm


class EmployerProfileCreateView(CreateView):
    model = EmployerProfile
    form_class = EmployerProfileForm
    template_name = 'employer_profile_form.html'
    success_url = 'home'

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
    

class HomeView(ListView):
    template_name = 'home.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer
    
    #to ensure that the employer can only create their own profile
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class ApplicantsListView(ListView):
    model = AppliedJobs
    template_name = 'applicants_list.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer
    
    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return AppliedJobs.objects.filter(applied_jobs_employer=self.request.user.employerprofile)

class ApplicantDetailView(DetailView):
    model = ApplicantProfile
    template_name = 'applicant_detail.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer
    
    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return AppliedJobs.objects.filter(applied_jobs_employer=self.request.user.employerprofile)


class JobCreationView(CreateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_creation_form.html'
    success_url = 'home'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only create their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

    #to ensure that the form is valid and the user is set to the current user
    def form_valid(self, form):
        form.instance.employer = self.request.user.employerprofile
        return super().form_valid(form)

class JobUpdateView(UpdateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_update_form.html'
    success_url = 'home'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only update their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class JobDeleteView(DeleteView):
    model = Jobs
    template_name = 'job_delete_form.html'
    success_url = 'home'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only delete their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class JobListView(ListView):
    model = Jobs
    template_name = 'job_list.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class JobDetailView(DetailView):
    model = Jobs
    template_name = 'job_detail.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

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
    template_name = 'company_profile_update_form.html'
    success_url = 'home'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_employer

    #to ensure that the employer can only update their own profile
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)

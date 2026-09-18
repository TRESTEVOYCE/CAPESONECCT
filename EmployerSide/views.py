
from AdminSide.models import EmployerProfile,Jobs,AppliedJobs,ApplicantProfile
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView,TemplateView
from .forms import EmployerProfileForm,JobsForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView

#home or the dashboard view for the employer
class HomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'home.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        applied_jobs = AppliedJobs.objects.filter(
            employer=self.request.user.employer_profile
        )
        jobs = Jobs.objects.filter(
            employer=self.request.user.employer_profile
        )

        context['applied_jobs'] = applied_jobs.count()
        context['jobs'] = jobs.count()

        return context

    
#view to create an employer profile usually in the profile or settings page
class EmployerProfileCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = EmployerProfile
    form_class = EmployerProfileForm
    template_name = 'employer_profile_form.html'
    success_url = reverse_lazy('employer-home')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
        )

    def get_queryset(self):
        return EmployerProfile.objects.filter(
            user=self.request.user
        )

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
#view to list all applicants who have applied to the employer's job postings
class ApplicantsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AppliedJobs
    template_name = 'applicants_list.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return AppliedJobs.objects.filter(employer=self.request.user.employer_profile)

#view to display details of a specific applicant
class ApplicantDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ApplicantProfile
    template_name = 'applicant_detail.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.role == 'employer' 
    
    def get_queryset(self):
         return ApplicantProfile.objects.filter(
            employer=self.request.user.employerprofile
            ).distinct()

#view to update the status of an applicant's job application
class ApplicantJobStatusView(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = AppliedJobs
    fields = ['status']
    success_url = reverse_lazy('home')

    #to ensure that the employer can only update their own job postings
    def get_queryset(self):
        return AppliedJobs.objects.filter(employer=self.request.user.employerprofile)

#to ensure that only authenticated employers can access this view
class JobCreationView(LoginRequiredMixin, UserPassesTestMixin,CreateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only create their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

    #to ensure that the form is valid and the user is set to the current user
    def form_valid(self, form):
        form.instance.employer = self.request.user.employerprofile
        return super().form_valid(form)

class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only update their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Jobs
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only delete their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'job_list.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Jobs
    template_name = 'job_detail.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only view their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employerprofile)

class AccountDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EmployerProfile
    success_url = reverse_lazy('home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only delete their own profile
    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)


class SettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):

    template_name = 'settings.html'

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

class LogoutView(LoginRequiredMixin,LogoutView): 
     next_page = reverse_lazy('landing_page')
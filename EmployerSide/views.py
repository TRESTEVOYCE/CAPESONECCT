
from AdminSide.models import EmployerProfile,Jobs,AppliedJobs,ApplicantProfile,User
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView,TemplateView
from django.views import View
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .forms import EmployerProfileForm,JobsForm,ProfilePictureForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView
from JobMatchingEngine.database import upsert_job_vector
from AdminSide.utils import notify_admins

#home or the dashboard view for the employer
class HomeView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'home.html'
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def get_queryset(self):
            return Jobs.objects.filter(
                employer__user=self.request.user
            ).order_by('-created_at')[:10]

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

class CompanyProfileView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'company_profile.html'

    def test_func(self):
            return (
                self.request.user.is_authenticated
                and self.request.user.role == 'employer'
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.employer_profile
        return context
    
class EmployerProfilePictureView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = ProfilePictureForm
    template_name = 'company_profile.html'
    success_url = reverse_lazy('company_profile_view')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
        )

    def get_object(self):
        return self.request.user
    
#view to create an employer profile usually in the profile or settings page
class EmployerProfileCreateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EmployerProfile
    form_class = EmployerProfileForm
    template_name = 'employer_profile_form.html'
    success_url = reverse_lazy('employer-home')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer' 
        )

    def get_object(self):
        return EmployerProfile.objects.get(user=self.request.user)
    

class EmployerReverificationAppealView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'employer'

    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(EmployerProfile, user=request.user)
        if profile.verification_status != 'rejected':
            messages.error(request, 'An appeal can only be submitted for a rejected employer profile.')
            return redirect('employer-home')

        reason = request.POST.get('reason', '').strip()
        if not reason or len(reason) > 2000:
            messages.error(request, 'Enter an appeal reason (up to 2,000 characters).')
            return redirect('employer-home')

        profile.verification_status = 'pending'
        profile.save(update_fields=['verification_status', 'updated_at'])
        notify_admins(
            title='Appeal for Reverification',
            message=f'{profile.business_name or request.user.username} requested employer profile reverification. Reason: {reason}',
            notification_type='APPEAL_REVERIFICATION',
            sender=request.user,
            reason=reason,
            target_url=reverse_lazy(
                'AdminSide:employer_verification',
                kwargs={'uuid': profile.uuid},
            ),
        )
        messages.success(request, 'Your appeal was submitted. Your profile is pending review.')
        return redirect('employer-home')


#view to list all applicants who have applied to the employer's job postings
class ApplicantsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AppliedJobs
    template_name = 'applicants_list.html'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
        )

    def get_queryset(self):
        employer_profile = self.request.user.employer_profile

        if employer_profile.verification_status != 'verified':
            return AppliedJobs.objects.none()

        return AppliedJobs.objects.filter(
            employer=employer_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['is_verified'] = (
            self.request.user.employer_profile.verification_status == 'verified'
        )

        return context
    
#view to display details of a specific applicant
class ApplicantDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ApplicantProfile
    template_name = 'applicant_detail.html'

    def test_func(self):
        employer_profile = getattr(
            self.request.user,
            'employerprofile',
            None
        )

        return (
            self.request.user.role == 'employer'
            and employer_profile
            and employer_profile.verification_status == 'verified'
        )

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
class JobCreationView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('employer-home')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        employer_profile = getattr(
            self.request.user,
            'employer_profile',
            None
        )

        context['is_verified'] = (
            employer_profile is not None
            and employer_profile.verification_status == 'verified'
        )

        return context

    def form_valid(self, form):
        form.instance.employer = self.request.user.employer_profile

        response = super().form_valid(form)

        notify_admins(
            title='New Job Post',
            message=f'{self.object.job_title} was posted by {self.request.user.employer_profile.business_name or self.request.user.username}.',
            notification_type='NEW_JOB_POST',
            sender=self.request.user,
            target_url=reverse_lazy('AdminSide:job_detail', kwargs={'job_uuid': self.object.uuid}),
        )

        upsert_job_vector(self.object)

        return response
    
class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('home')
    raise_exception = True

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
            and self.request.user.employer_profile.verification_status == 'verified'
        )

    def get_queryset(self):
        return Jobs.objects.filter(
            employer=self.request.user.employer_profile
        )

class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Jobs
    template_name = 'job_confirm_delete.html'
    success_url = reverse_lazy('employer-home')
    raise_exception = True
    
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
            and self.request.user.employer_profile.verification_status == 'verified'
            )
    
    #to ensure that the employer can only delete their own job postings
    def get_queryset(self):
        return Jobs.objects.filter(employer=self.request.user.employer_profile)

class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'employer-job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
        )

    def get_queryset(self):
        employer_profile = self.request.user.employer_profile

        if employer_profile.verification_status != 'verified':
            return Jobs.objects.none()

        return Jobs.objects.filter(
            employer__user=self.request.user
        ).order_by('-created_at')
    
    
class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Jobs
    template_name = 'job_detail.html'
    context_object_name = 'job'

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
            and self.request.user.employer_profile.verification_status == 'verified'
        )

    def get_queryset(self):
        return Jobs.objects.filter(
            employer=self.request.user.employer_profile
        )

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
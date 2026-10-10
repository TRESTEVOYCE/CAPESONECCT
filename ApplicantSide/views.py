import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, TemplateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from JobMatchingEngine.database import get_job_collection, build_applicant_profile_text, query_matching_jobs
from AdminSide.models import Jobs, ApplicantProfile, AppliedJobs, SavedJobs, OfferedJobs, User
from django.contrib.auth.views import LogoutView as DjangoLogoutView, PasswordChangeView
from django.db.models import Q
from django.urls import reverse_lazy
from django.views import View
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import (
    ApplicantPersonalInfoForm, ApplicantAddressForm, ApplicantEducationForm,
    ApplicantTrainingForm, ApplicantPreferredJobForm, ApplicantWorkExperienceFormSet,
    ApplicantSkillsForm, ApplicantSkillFormSet, ApplicantDocumentsForm,
    ProfilePictureForm, UpdateEmailForm, UpdatePasswordForm, UpdateUsernameForm,
)
from django.contrib.auth import update_session_auth_hash


class ApplicantPersonalInfoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPersonalInfoForm
    template_name = 'step_1_personal_info.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-address')

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Personal information saved successfully.')
        return redirect(self.get_success_url())


class ApplicantAddressView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantAddressForm
    template_name = 'step_2_address.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-education')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Address information saved successfully.')
        return redirect(self.get_success_url())


class ApplicantEducationView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantEducationForm
    template_name = 'step_3_education.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-training')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Educational information saved successfully.')
        return redirect(self.get_success_url())


class ApplicantTrainingView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantTrainingForm
    template_name = 'step_4_training.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-preferred-job')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Training information saved successfully.')
        return redirect(self.get_success_url())


class ApplicantPreferredJobView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPreferredJobForm
    template_name = 'step_5_job_pref.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-work-experience')

    def form_valid(self, form):
        profile = form.save()
        matches = query_matching_jobs(applicant=profile, total_results=10)
        self.request.session['job_matches'] = matches['ids']
        messages.success(self.request, 'Job preferences saved successfully.')
        return redirect(self.get_success_url())


class ApplicantWorkExperienceView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'step_6_work.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_profile(self):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()
        work_formset = ApplicantWorkExperienceFormSet(instance=profile)
        return render(request, self.template_name, {'work_formset': work_formset})

    def post(self, request, *args, **kwargs):
        profile = self.get_profile()
        work_formset = ApplicantWorkExperienceFormSet(request.POST, instance=profile)
        if work_formset.is_valid():
            work_formset.save()
            messages.success(request, 'Work experience saved successfully.')
            return redirect('applicant-skills')
        return render(request, self.template_name, {'work_formset': work_formset})


class ApplicantSkillsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'step_7_skills.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_profile(self):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()
        form = ApplicantSkillsForm(instance=profile)
        skill_formset = ApplicantSkillFormSet(queryset=profile.skills.all(), prefix='skills')
        return render(request, self.template_name, {'form': form, 'skill_formset': skill_formset})

    def post(self, request, *args, **kwargs):
        profile = self.get_profile()
        form = ApplicantSkillsForm(request.POST, instance=profile)
        skill_formset = ApplicantSkillFormSet(
            request.POST, queryset=profile.skills.all(), prefix='skills'
        )
        if form.is_valid() and skill_formset.is_valid():
            form.save()
            skills = skill_formset.save()
            profile.skills.set(skills)
            matches = query_matching_jobs(applicant=profile, total_results=10)
            request.session['job_matches'] = matches['ids']
            messages.success(request, 'Skills information saved successfully.')
            return redirect('applicant-documents')
        return render(request, self.template_name, {'form': form, 'skill_formset': skill_formset})


class ApplicantDocumentsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantDocumentsForm
    template_name = 'step_8_certification.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile, created = ApplicantProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-dashboard')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Documents submitted successfully.')
        return redirect(self.get_success_url())


class LogoutView(LoginRequiredMixin, UserPassesTestMixin, DjangoLogoutView):
    success_url = reverse_lazy('landing_page')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'


class DashBoardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'applicant-dashboard.html'
    context_object_name = 'matching_jobs'
    login_url = reverse_lazy('signin')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        context['applicant_profile'] = applicant_profile

        if applicant_profile:
            applicant_profile_text = build_applicant_profile_text(applicant_profile)
            collection = get_job_collection()
            results = collection.query(query_texts=[applicant_profile_text], n_results=10)

            job_uuids = [
                metadata['job_uuid'] for metadata in results['metadatas'][0]
                if metadata and 'job_uuid' in metadata
            ]

            matching_jobs = Jobs.objects.filter(uuid__in=job_uuids, status='Active')

            if matching_jobs.exists():
                context['matching_jobs'] = matching_jobs
            else:
                context['matching_jobs'] = Jobs.objects.filter(status='Active')

            applications = AppliedJobs.objects.filter(applicant=applicant_profile)
            context['application_count'] = applications.count()
            context['saved_jobs_count'] = SavedJobs.objects.filter(applicant=applicant_profile).count()
            context['under_review_count'] = applications.filter(status__in=['pending', 'reviewed']).count()
            context['shortlisted_count'] = applications.filter(status='for interview').count()
            context['rejected_count'] = applications.filter(status='rejected').count()
            context['withdrawn_count'] = applications.filter(status='withdrawn').count()

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
            context['matching_jobs'] = Jobs.objects.filter(status='Active')
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
        if q:
            jobs = jobs.filter(
                Q(job_title__icontains=q) |
                Q(job_description__icontains=q) |
                Q(employer__business_name__icontains=q)
            )

        location = self.request.GET.get('location')
        if location:
            jobs = jobs.filter(place_of_work__icontains=location)

        job_types = self.request.GET.getlist('job_type')
        if job_types:
            jobs = jobs.filter(nature_of_work__in=job_types)

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()

        context['selected_job_types'] = self.request.GET.getlist('job_type')
        available_jobs = self.get_queryset()

        if applicant_profile:
            applicant_text = build_applicant_profile_text(applicant_profile)
            collection = get_job_collection()
            results = collection.query(query_texts=[applicant_text], n_results=10)
            job_uuids = []

            if results.get('metadatas'):
                job_uuids = [
                    metadata['job_uuid'] for metadata in results['metadatas'][0]
                    if metadata and 'job_uuid' in metadata
                ]

            matching_jobs = available_jobs.filter(uuid__in=job_uuids)

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
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'


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
        applicant_profile = self.request.user.applicant_profile
        context['applied_count'] = applications.count()
        context['endorsed_count'] = OfferedJobs.objects.filter(applicant=applicant_profile).count()
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
        jobs = Jobs.objects.filter(status='Active')

        q = self.request.GET.get('q')
        if q:
            jobs = jobs.filter(
                Q(job_title__icontains=q) |
                Q(job_description__icontains=q) |
                Q(employer__business_name__icontains=q)
            )

        location = self.request.GET.get('location')
        if location:
            jobs = jobs.filter(place_of_work__icontains=location)

        job_types = self.request.GET.getlist('job_type')
        if job_types:
            jobs = jobs.filter(nature_of_work__in=job_types)

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_job_types'] = self.request.GET.getlist('job_type')
        return context


class ApplyJobView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def post(self, request, pk):
        applicant_profile = ApplicantProfile.objects.filter(user=request.user).first()
        if not applicant_profile:
            messages.warning(request, 'Please complete your Profile first.')
            return redirect('applicant-dashboard')

        if applicant_profile.status != 'approved':
            messages.warning(request, 'Your applicant profile must be approved before you can apply for jobs.')
            return redirect('job_details', pk=pk)

        job = get_object_or_404(Jobs, pk=pk, status='Active')
        if AppliedJobs.objects.filter(applicant=applicant_profile, applied_job=job).exists():
            messages.warning(request, 'You have already applied for this job.')
            return redirect('job_details', pk=job.pk)

        AppliedJobs.objects.create(
            employer=job.employer, applicant=applicant_profile,
            applied_job=job, status='pending'
        )
        messages.success(request, 'Your application has been submitted successfully.')
        return redirect('applied_jobs')


class SaveJobView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def post(self, request, pk):
        applicant_profile = ApplicantProfile.objects.filter(user=request.user).first()
        if not applicant_profile:
            messages.warning(request, 'Please complete your profile first.')
            return redirect('applicant-dashboard')

        job = get_object_or_404(Jobs, pk=pk, status='Active')
        saved_job, created = SavedJobs.objects.get_or_create(
            applicant=applicant_profile, saved_job=job
        )

        if created:
            messages.success(request, 'Job saved successfully.')
        else:
            messages.info(request, 'You have already saved this job.')

        return redirect('job_details', pk=job.pk)


class ApplicantRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('signin')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def handle_no_permission(self):
        return redirect('signin')


class UnsaveJobView(ApplicantRequiredMixin, View):
    def get(self, request, pk):
        applicant_profile = get_object_or_404(ApplicantProfile, user=request.user)
        saved_job = get_object_or_404(SavedJobs, pk=pk, applicant=applicant_profile)
        saved_job.delete()
        messages.success(request, 'Job removed from saved jobs.')
        return redirect('saved_jobs')


class EditProfilePictureView(ApplicantRequiredMixin, UpdateView):
    model = ApplicantProfile
    form_class = ProfilePictureForm
    template_name = 'edit_profile_picture.html'
    success_url = reverse_lazy('personal_info')

    def get_object(self):
        return ApplicantProfile.objects.filter(user=self.request.user).first()

    def form_valid(self, form):
        messages.success(self.request, 'Profile picture updated successfully.')
        return super().form_valid(form)


class ViewProfileView(ApplicantRequiredMixin, UpdateView):
    model = User
    form_class = ProfilePictureForm
    template_name = 'view_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('view_profile')

    def form_valid(self, form):
        messages.success(self.request, 'Profile picture updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = ApplicantProfile.objects.filter(user=self.request.user).first()
        context['profile_picture'] = self.request.user
        return context


class MyProfileView(ApplicantRequiredMixin, TemplateView):
    template_name = 'applicant_personal_info_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        context['profile'] = profile
        context['applicant_profile'] = profile
        return context

    def get_object(self):
        return ApplicantProfile.objects.filter(user=self.request.user).first()


# ==========================================
# SETTINGS & SECURE ACCOUNT MANAGEMENT VIEWS
# ==========================================

class SettingsView(ApplicantRequiredMixin, TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = ApplicantProfile.objects.filter(user=self.request.user).first()
        return context

    def post(self, request, *args, **kwargs):
        full_name = request.POST.get('full_name')
        if full_name:
            user = request.user
            user.first_name = full_name.strip()
            user.save()
            
            applicant_profile = ApplicantProfile.objects.filter(user=user).first()
            if applicant_profile and hasattr(applicant_profile, 'full_name'):
                applicant_profile.full_name = full_name.strip()
                applicant_profile.save()

            messages.success(request, "Your name has been updated successfully.")

        messages.success(request, "Your settings preferences have been saved.")
        return redirect('settings')


@login_required
def send_email_otp(request):
    if request.method == "POST":
        new_email = request.POST.get("email")
        if not new_email:
            return JsonResponse({"status": "error", "message": "Email is required."}, status=400)
        
        if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
            return JsonResponse({"status": "error", "message": "This email address is already in use."}, status=400)
        
        otp_code = str(random.randint(100000, 999999))
        
        request.session['pending_new_email'] = new_email
        request.session['email_otp_code'] = otp_code
        
        try:
            send_mail(
                subject="Your CAPESONNECT Verification Code",
                message=f"Your One-Time Password (OTP) to change your email is: {otp_code}. Valid for 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_email],
                fail_silently=False,
            )
            return JsonResponse({"status": "success", "message": "OTP sent successfully."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


@login_required
def update_email_view(request):
    if getattr(request.user, 'role', '') != 'applicant':
        return redirect('applicant-dashboard')
        
    if request.method == "POST":
        entered_otp = request.POST.get("otp_code", "").strip()
        session_email = request.session.get('pending_new_email')
        session_otp = request.session.get('email_otp_code')
        
        if not session_otp or not session_email:
            messages.error(request, "Please request a verification code first.")
        elif entered_otp != session_otp:
            messages.error(request, "Invalid verification code. Please try again.")
        elif User.objects.filter(email=session_email).exclude(pk=request.user.pk).exists():
            messages.error(request, "This email address is already registered to another account.")
        else:
            user = request.user
            user.email = session_email
            if hasattr(user, 'username') and user.username == user.email:
                user.username = session_email
            user.save()
            
            request.session.pop('pending_new_email', None)
            request.session.pop('email_otp_code', None)
            
            messages.success(request, "Your email address has been successfully updated.")
            return redirect('settings')
            
    return render(request, 'change_email.html')


@login_required
def send_password_otp_view(request):
    otp = str(random.randint(100000, 999999))
    
    request.session['password_otp'] = otp
    request.session['otp_verified'] = False

    send_mail(
        subject='Password Change Verification Code — CAPESONNECT',
        message=f'Your security verification code to change your password is: {otp}. This code expires shortly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=False,
    )
    
    return redirect('verify-password-otp')


@login_required
def verify_password_otp_view(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        if user_otp == request.session.get('password_otp'):
            request.session['otp_verified'] = True
            return redirect('update-password')
        else:
            messages.error(request, "Invalid OTP code. Please try again.")
            
    return render(request, 'verify_otp.html')


class SecurePasswordChangeView(PasswordChangeView):
    template_name = 'change_password.html'
    success_url = reverse_lazy('settings')

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('otp_verified', False):
            messages.warning(request, "Please verify your email with an OTP first.")
            return redirect('send-password-otp')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        request = self.request
        request.session.pop('password_otp', None)
        request.session.pop('otp_verified', None)
        
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Your password has been changed successfully.")
        return super().form_valid(form)


class UpdateUsernameView(ApplicantRequiredMixin, UpdateView):
    model = User
    form_class = UpdateUsernameForm
    template_name = 'update_username.html'
    success_url = reverse_lazy('my_profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Username updated successfully.')
        return super().form_valid(form)


class ApplicantProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ApplicantProfile
    success_url = reverse_lazy('login')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)


# ==========================================
# HELP & SUPPORT API / VIEW
# ==========================================

@login_required
def send_applicant_support_message_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject = data.get('subject', 'CAPESONNECT Applicant Support')
            user_message = data.get('message', '')
            
            user_email = getattr(request.user, 'email', None) or 'Not provided'
            sender_info = f"Applicant Username: {request.user.username}\nEmail: {user_email}\n\n"
            full_message = sender_info + "Message:\n" + user_message
            
            send_mail(
                subject=subject,
                message=full_message,
                from_email=None,
                recipient_list=['pesocarigaraadmin@gmail.com'],
                fail_silently=False,
            )
            
            return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


class HelpPageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'applicant_help.html'

    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'applicant'
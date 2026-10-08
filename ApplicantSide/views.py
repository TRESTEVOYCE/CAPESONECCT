from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, TemplateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from JobMatchingEngine.database import get_job_collection, build_applicant_profile_text
from AdminSide.models import Jobs, ApplicantProfile, AppliedJobs, SavedJobs, ApplicantSkills,OfferedJobs
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db.models import Q
from django.urls import reverse_lazy
from .forms import ProfilePictureForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import (
    ApplicantPersonalInfoForm,
    ApplicantAddressForm,
    ApplicantEducationForm,
    ApplicantTrainingForm,
    ApplicantPreferredJobForm,
    ApplicantWorkExperienceFormSet,
    ApplicantSkillsForm,
    ApplicantSkillFormSet,
    ApplicantDocumentsForm,
    ProfilePictureForm,
)
from AdminSide.utils import notify_admins


class ApplicantProfileRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.role == 'applicant'
            and not ApplicantProfile.objects.filter(user=request.user).exists()
        ):
            messages.info(request, 'Complete your personal information before continuing your profile.')
            return redirect('personal_info')
        return super().dispatch(request, *args, **kwargs)


class ApplicantPersonalInfoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPersonalInfoForm
    template_name = 'step_1_personal_info.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        if profile is None:
            profile = ApplicantProfile(
                user=self.request.user,
                first_name=self.request.user.first_name,
                last_name=self.request.user.last_name,
            )
        return profile

    def get_success_url(self):
        return reverse_lazy('applicant-address')

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()

        messages.success(
        self.request,
        'Personal information saved successfully.'
     )

        return redirect(self.get_success_url())


class ApplicantAddressView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantAddressForm
    template_name = 'step_2_address.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('applicant-education')

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            'Address information saved successfully.'
        )

        return redirect(self.get_success_url())


class ApplicantEducationView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantEducationForm
    template_name = 'step_3_education.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('applicant-training')

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            'Educational information saved successfully.'
        )

        return redirect(self.get_success_url())


class ApplicantTrainingView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantTrainingForm
    template_name = 'step_4_training.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('applicant-preferred-job')

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            'Training information saved successfully.'
        )

        return redirect(self.get_success_url())


class ApplicantPreferredJobView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantPreferredJobForm
    template_name = 'step_5_job_pref.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('applicant-work-experience')

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            'Job preferences saved successfully.'
        )

        return redirect(self.get_success_url())


class ApplicantWorkExperienceView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'step_6_work.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_profile(self):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()

        work_formset = ApplicantWorkExperienceFormSet(
            instance=profile
        )

        return render(
            request,
            self.template_name,
            {
                'work_formset': work_formset
            }
        )

    def post(self, request, *args, **kwargs):
        profile = self.get_profile()

        work_formset = ApplicantWorkExperienceFormSet(
            request.POST,
            instance=profile
        )

        if work_formset.is_valid():
            work_formset.save()

            messages.success(
                request,
                'Work experience saved successfully.'
            )

            return redirect('applicant-skills')

        return render(
            request,
            self.template_name,
            {
                'work_formset': work_formset
            }
        )

class ApplicantSkillsView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'step_7_skills.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_profile(self):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()

        form = ApplicantSkillsForm(
            instance=profile
        )

        skill_formset = ApplicantSkillFormSet(
            queryset=profile.skills.all(),
            prefix='skills'
        )

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'skill_formset': skill_formset
            }
        )

    def post(self, request, *args, **kwargs):
        profile = self.get_profile()

        form = ApplicantSkillsForm(
            request.POST,
            instance=profile
        )

        skill_formset = ApplicantSkillFormSet(
            request.POST,
            queryset=profile.skills.all(),
            prefix='skills'
        )

        if form.is_valid() and skill_formset.is_valid():
            form.save()

            skills = skill_formset.save()

            profile.skills.set(skills)

            messages.success(
                request,
                'Skills information saved successfully.'
            )

            return redirect('applicant-documents')

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'skill_formset': skill_formset
            }
        )


class ApplicantDocumentsView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ApplicantProfile
    form_class = ApplicantDocumentsForm
    template_name = 'step_8_certification.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_object(self, queryset=None):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('applicant-dashboard')

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            'Documents submitted successfully.'
        )

        return redirect(self.get_success_url())


class ApplicantReverificationAppealView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'applicant'

    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(ApplicantProfile, user=request.user)
        if profile.status != 'rejected':
            messages.error(request, 'An appeal can only be submitted for a rejected account.')
            return redirect('applicant-dashboard')

        reason = request.POST.get('reason', '').strip()
        if not reason or len(reason) > 2000:
            messages.error(request, 'Enter an appeal reason (up to 2,000 characters).')
            return redirect('applicant-dashboard')

        profile.status = 'pending'
        profile.save(update_fields=['status', 'updated_at'])
        notify_admins(
            title='Appeal for Reverification',
            message=f'{profile.first_name} {profile.last_name} requested applicant account reverification. Reason: {reason}',
            notification_type='APPEAL_REVERIFICATION',
            sender=request.user,
            reason=reason,
            target_url=reverse_lazy(
                'AdminSide:applicant_verification',
                kwargs={'uuid': profile.uuid},
            ),
        )
        messages.success(request, 'Your appeal was submitted. Your account is pending review.')
        return redirect('applicant-dashboard')


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
    login_url = reverse_lazy('signin')

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
        context['applicant_profile'] = applicant_profile

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
           # Get job UUIDs returned by ChromaDB
            job_uuids = [
                metadata['job_uuid']
                for metadata in results['metadatas'][0]
                if metadata and 'job_uuid' in metadata
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

            job_uuids = []

            if results.get('metadatas'):
                job_uuids = [
                    metadata['job_uuid']
                    for metadata in results['metadatas'][0]
                    if metadata and 'job_uuid' in metadata
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
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def get_queryset(self):
        try:
            applicant_profile = self.request.user.applicant_profile
        except ApplicantProfile.DoesNotExist:
            return AppliedJobs.objects.none()

        return AppliedJobs.objects.filter(
            applicant=applicant_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = self.get_queryset()

        applicant_profile = self.request.user.applicant_profile

        context['applied_count'] = applications.count()

        # PESO referrals / endorsements
        context['endorsed_count'] = OfferedJobs.objects.filter(
            applicant=applicant_profile
        ).count()

        # Employer interview status
        context['interviewed_count'] = applications.filter(
            status='for interview'
        ).count()

        # Hired status
        context['hired_count'] = applications.filter(
            status='hired'
        ).count()

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

class ApplicantRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('signin')

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'applicant'
        )

    def handle_no_permission(self):
        return redirect('signin')

class UnsaveJobView(ApplicantRequiredMixin, View):

    def get(self, request, pk):
        applicant_profile = get_object_or_404(
            ApplicantProfile,
            user=request.user
        )

        saved_job = get_object_or_404(
            SavedJobs,
            pk=pk,
            applicant=applicant_profile
        )

        saved_job.delete()

        messages.success(
            request,
            'Job removed from saved jobs.'
        )

        return redirect('saved_jobs')

class EditProfilePictureView(ApplicantRequiredMixin, UpdateView):
    model = ApplicantProfile
    form_class = ProfilePictureForm
    template_name = 'edit_profile_picture.html'
    success_url = reverse_lazy('personal_info')

    def get_object(self):
        return ApplicantProfile.objects.filter(
            user=self.request.user
        ).first()

    def form_valid(self, form):
        messages.success(
            self.request,
            'Profile picture updated successfully.'
        )
        return super().form_valid(form)


class ViewProfileView(ApplicantRequiredMixin, UpdateView):
    model = ApplicantProfile
    form_class = ProfilePictureForm
    template_name = 'view_profile.html'

    def get_object(self):
        return ApplicantProfile.objects.filter(
            user=self.request.user
        ).first()

    def get_success_url(self):
        return reverse_lazy('view_profile')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Profile picture updated successfully.'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = self.object

        context['profile'] = profile
        context['applicant_profile'] = profile

        return context

class MyProfileView(ApplicantRequiredMixin,TemplateView):
    template_name = 'applicant_personal_info_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = ApplicantProfile.objects.filter(
            user=self.request.user
        ).first()

        context['profile'] = profile
        context['applicant_profile'] = profile
        context['account_email'] = self.request.user.email
        return context
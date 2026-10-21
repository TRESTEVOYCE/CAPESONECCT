import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, TemplateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from JobMatchingEngine.database import get_job_collection, build_applicant_profile_text,query_matching_jobs
from AdminSide.models import Jobs, ApplicantProfile, ApplicantWorkExperience, AppliedJobs, SavedJobs, ApplicantSkills,OfferedJobs, Notification, User,AuditLog, ProfileChangeLog
from django.contrib.auth.views import LogoutView as DjangoLogoutView, PasswordChangeView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from .forms import ProfilePictureForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import (
    ApplicantPersonalInfoForm, ApplicantAddressForm, ApplicantEducationForm,
    ApplicantTrainingForm, ApplicantPreferredJobForm, ApplicantWorkExperienceFormSet,
    ApplicantSkillsForm, ApplicantSkillFormSet, ApplicantDocumentsForm,
    ProfilePictureForm, UpdateEmailForm, UpdatePasswordForm, UpdateUsernameForm,
)
from django.contrib.auth import update_session_auth_hash
from AdminSide.utils import notify_admins
from JobMatchingEngine.database import query_matching_jobs
from AdminSide.services.profile_sensitivity import (
    capture_profile_changes,
    capture_related_profile_changes,
    classify_profile_changes,
    mark_profile_for_reverification,
)


def record_profile_changes(profile, user, changes, change_model=None):
    """Safely record profile changes using the correct ProfileChangeLog model fields."""
    if not changes:
        return
    target_user = user if isinstance(user, User) else getattr(profile, 'user', None)
    for field, vals in changes.items():
        old_val = None
        new_val = None
        if isinstance(vals, (list, tuple)) and len(vals) == 2:
            old_val, new_val = vals
        elif isinstance(vals, dict):
            old_val = vals.get('old')
            new_val = vals.get('new')
        else:
            new_val = vals
        
        ProfileChangeLog.objects.create(
            user=target_user,
            field_name=str(field),
            old_value=str(old_val) if old_val is not None else '',
            new_value=str(new_val) if new_val is not None else ''
        )


def _stamp_uploaded_profile_proofs(profile, uploaded_fields, files):
    timestamp = timezone.now()
    timestamp_fields = []
    for field_name, timestamp_field in uploaded_fields.items():
        if files.get(field_name):
            setattr(profile, timestamp_field, timestamp)
            timestamp_fields.append(timestamp_field)
    if timestamp_fields:
        profile.save(update_fields=[*timestamp_fields, 'updated_at'])


def _mark_applicant_for_reverification(request, profile, changed_fields, change_model=None):
    classification = classify_profile_changes(
        change_model or profile,
        changed_fields,
    )
    should_notify_admins = (
        classification.requires_reverification
        and profile.status in {'approved', 'pending', 'reverify_pending'}
    )
    status_changed = mark_profile_for_reverification(
        profile,
        changed_fields,
        change_model,
    )
    if status_changed:
        request.session.pop('job_matches', None)
        messages.warning(
            request,
            'Your profile has been updated and is pending re-verification. '
            'You cannot apply for jobs until it is approved again.',
        )
    if should_notify_admins:
        notifications = notify_admins(
            title='Applicant Profile Updated - Re-Verification Required',
            message=(
                f'{profile.first_name} {profile.last_name} updated sensitive profile '
                'information. Review the profile changes and supporting documents.'
            ),
            notification_type='RESUBMISSION',
            sender=request.user,
            target_url=reverse(
                'AdminSide:applicant_verification',
                kwargs={'uuid': profile.uuid},
            ),
        )
        if not notifications:
            messages.error(
                request,
                'Your update was saved, but no PESO administrator is configured to receive '
                'the re-verification notification.',
            )
    return status_changed

class ApplicantRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('signin')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'applicant'

    def handle_no_permission(self):
        return redirect('signin')


APPLICANT_NOTIFICATION_TYPES = (
    'APPLICATION_STATUS',
    'VERIFICATION_APPROVED',
    'VERIFICATION_REJECTED',
)


class ApplicantNotificationAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'applicant'

class ApplicantNotificationListView(ApplicantNotificationAccessMixin, ListView):
    model = Notification
    template_name = 'applicant_notification.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        queryset = Notification.objects.filter(
            recipient=self.request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
        )
        self.status_filter = self.request.GET.get('status', 'all').lower()
        if self.status_filter == 'unread':
            queryset = queryset.filter(is_read=False)
        elif self.status_filter == 'read':
            queryset = queryset.filter(is_read=True)
        else:
            self.status_filter = 'all'
        return queryset.order_by('-created_at', '-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = Notification.objects.filter(
            recipient=self.request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
        )
        context.update({
            'applicant_profile': ApplicantProfile.objects.filter(user=self.request.user).first(),
            'unread_count': notifications.filter(is_read=False).count(),
            'total_count': notifications.count(),
            'selected_status': self.status_filter,
        })
        return context

class ApplicantNotificationHeaderApiView(ApplicantNotificationAccessMixin, View):
    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
        )
        latest_notifications = notifications.order_by('-created_at', '-pk')[:5]
        return JsonResponse({
            'unread_count': notifications.filter(is_read=False).count(),
            'total_count': notifications.count(),
            'notifications': [
                {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'reason': notification.reason,
                    'notification_type': notification.notification_type,
                    'target_url': notification.target_url or '#',
                    'created_at': notification.created_at.strftime('%b %d, %Y %I:%M %p'),
                    'is_read': notification.is_read,
                    'read_url': reverse('applicant-notification-read', args=[notification.id]),
                }
                for notification in latest_notifications
            ],
        })

class ApplicantMarkNotificationReadView(ApplicantNotificationAccessMixin, View):
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
        )
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        unread_count = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
            is_read=False,
        ).count()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'unread_count': unread_count})
        return redirect(notification.target_url or 'applicant-notifications')

class ApplicantMarkAllNotificationsReadView(ApplicantNotificationAccessMixin, View):
    def post(self, request, *args, **kwargs):
        updated_count = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
            is_read=False,
        ).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'updated_count': updated_count,
                'unread_count': 0,
            })
        messages.success(request, f'Marked {updated_count} notification(s) as read.')
        return redirect('applicant-notifications')

class ApplicantDeleteNotificationView(ApplicantNotificationAccessMixin, View):
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
        )
        notification.delete()
        unread_count = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=APPLICANT_NOTIFICATION_TYPES,
            is_read=False,
        ).count()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'unread_count': unread_count})
        messages.success(request, 'Notification deleted.')
        return redirect('applicant-notifications')

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
        changes = capture_profile_changes(form.instance)
        self.object = form.save()
        record_profile_changes(self.object, self.request.user, changes)
        _mark_applicant_for_reverification(
            self.request,
            self.object,
            form.changed_data,
        )
        messages.success(self.request, 'Personal information saved successfully.')
        return redirect(self.get_success_url())

class ApplicantAddressView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
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
        changes = capture_profile_changes(form.instance)
        profile = form.save()
        record_profile_changes(profile, self.request.user, changes)
        _mark_applicant_for_reverification(
            self.request,
            profile,
            form.changed_data,
        )
        messages.success(self.request, 'Address information saved successfully.')
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
        attainment = form.cleaned_data.get('highest_educational_attainment')
        for attainment_name in (
            'no_formal',
            'elem_level',
            'elem_grad',
            'hs_level',
            'hs_grad',
            'college_level',
            'college_grad',
            'tech_voc',
            'post_grad',
        ):
            setattr(
                form.instance,
                f'edu_{attainment_name}',
                attainment_name == attainment,
            )
        changes = capture_profile_changes(form.instance)
        profile = form.save()
        record_profile_changes(profile, self.request.user, changes)
        _stamp_uploaded_profile_proofs(
            profile,
            {'education_proof_document': 'education_proof_uploaded_at'},
            form.files,
        )
        _mark_applicant_for_reverification(
            self.request,
            profile,
            form.changed_data,
        )
        messages.success(self.request, 'Educational information saved successfully.')
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
        profile = form.save(commit=False)

        # Extract multi-entry array fields from step_4_training_2.html
        titles = self.request.POST.getlist('training_title[]')
        hours = self.request.POST.getlist('training_hours[]')
        institutions = self.request.POST.getlist('training_institution[]')
        dates = self.request.POST.getlist('training_date[]')

        # Map entry 1
        if len(titles) > 0 and titles[0].strip():
            profile.training_title_1 = titles[0].strip()
            profile.training_hours_1 = int(hours[0]) if len(hours) > 0 and hours[0].isdigit() else None
            profile.training_institution_1 = institutions[0].strip() if len(institutions) > 0 else ''
            profile.training_date_1 = dates[0] if len(dates) > 0 and dates[0] else None
        else:
            profile.training_title_1 = ''
            profile.training_hours_1 = None
            profile.training_institution_1 = ''
            profile.training_date_1 = None

        # Map entry 2
        if len(titles) > 1 and titles[1].strip():
            profile.training_title_2 = titles[1].strip()
            profile.training_hours_2 = int(hours[1]) if len(hours) > 1 and hours[1].isdigit() else None
            profile.training_institution_2 = institutions[1].strip() if len(institutions) > 1 else ''
            profile.training_date_2 = dates[1] if len(dates) > 1 and dates[1] else None
        else:
            profile.training_title_2 = ''
            profile.training_hours_2 = None
            profile.training_institution_2 = ''
            profile.training_date_2 = None

        changes = capture_profile_changes(profile)
        profile.save()
        record_profile_changes(profile, self.request.user, changes)

        _stamp_uploaded_profile_proofs(
            profile,
            {
                'technical_certification_document': 'technical_certification_uploaded_at',
                'professional_license_document': 'professional_license_uploaded_at',
            },
            form.files,
        )
        _mark_applicant_for_reverification(
            self.request,
            profile,
            form.changed_data,
        )
        messages.success(self.request, 'Training information saved successfully.')
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
        profile = form.save(commit=False)
        
        # Capture dynamic occupations from POST array
        occupations = self.request.POST.getlist('pref_occupation[]')
        profile.pref_occupation_1 = occupations[0] if len(occupations) > 0 else ''
        profile.pref_occupation_2 = occupations[1] if len(occupations) > 1 else ''
        profile.pref_occupation_3 = occupations[2] if len(occupations) > 2 else ''
        
        changes = capture_profile_changes(
            profile,
            many_to_many_values={
                'preferred_job': form.cleaned_data.get('preferred_job', []),
            },
        )
        profile.save()
        record_profile_changes(profile, self.request.user, changes)
        _mark_applicant_for_reverification(
            self.request,
            profile,
            form.changed_data,
        )
        if profile.status == 'approved':
            matches = query_matching_jobs(applicant=profile, total_results=10)
            self.request.session['job_matches'] = matches['ids']
        else:
            self.request.session.pop('job_matches', None)
        messages.success(self.request, 'Job preferences saved successfully.')
        return redirect(self.get_success_url())

class ApplicantWorkExperienceView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'step_6_work.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_profile(self):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()
        work_formset = ApplicantWorkExperienceFormSet(instance=profile)
        return render(request, self.template_name, {'work_formset': work_formset})

    def post(self, request, *args, **kwargs):
        profile = self.get_profile()
        work_formset = ApplicantWorkExperienceFormSet(
            request.POST,
            request.FILES,
            instance=profile,
        )
        if work_formset.is_valid():
            old_work_experiences = list(
                profile.work_experiences.order_by('pk').values(
                    'company', 'address', 'position', 'dates', 'status'
                )
            )
            new_work_experiences = []
            for work_form in work_formset.forms:
                if work_form.cleaned_data.get('DELETE'):
                    continue
                values = {
                    field: work_form.cleaned_data.get(field, '')
                    for field in ('company', 'address', 'position', 'dates', 'status')
                }
                if any(values.values()):
                    new_work_experiences.append(values)
            changes = capture_related_profile_changes(
                'work_experiences',
                old_work_experiences,
                new_work_experiences,
            )
            changed_fields = set()
            for form in work_formset.forms:
                if form.has_changed():
                    changed_fields.update(form.changed_data)
                    if form.cleaned_data.get('DELETE'):
                        changed_fields.add('__deleted__')
            work_formset.save()
            record_profile_changes(profile, request.user, changes)
            uploaded_at = timezone.now()
            for work_form in work_formset.forms:
                if work_form.files.get(work_form.add_prefix('proof_document')):
                    work_form.instance.proof_document_uploaded_at = uploaded_at
                    work_form.instance.save(
                        update_fields=['proof_document_uploaded_at'],
                    )
            _mark_applicant_for_reverification(
                request,
                profile,
                changed_fields,
                ApplicantWorkExperience,
            )
            messages.success(request, 'Work experience saved successfully.')
            return redirect('applicant-skills')
        return render(request, self.template_name, {'work_formset': work_formset})


class ApplicantSkillsView(ApplicantProfileRequiredMixin, LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'step_7_skills.html'

    def test_func(self):
        return self.request.user.role == 'applicant'

    def get_profile(self):
        return ApplicantProfile.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()
        form = ApplicantSkillsForm(instance=profile)
        skill_formset = ApplicantSkillFormSet(queryset=profile.skills.all(), prefix='skills')
        return render(request, self.template_name, {'form': form, 'skill_formset': skill_formset})

    def post(self, request, *args, **kwargs):
        profile = self.get_profile()
        form = ApplicantSkillsForm(request.POST, request.FILES, instance=profile)
        skill_formset = ApplicantSkillFormSet(
            request.POST, queryset=profile.skills.all(), prefix='skills'
        )
        form_valid = form.is_valid()
        skill_formset_valid = skill_formset.is_valid()
        changed_skill_records = any(
            skill_form.has_changed()
            for skill_form in skill_formset.forms
        )
        if (
            profile.status in {'approved', 'reverify_pending'}
            and changed_skill_records
            and not request.FILES.get('technical_certification_document')
        ):
            form.add_error(
                None,
                ApplicantSkillsForm.proof_required_message,
            )
            form_valid = False
        if form_valid and skill_formset_valid:
            old_skills = list(
                profile.skills.order_by('pk').values_list('skill_name', flat=True)
            )
            new_skills = []
            for skill_form in skill_formset.forms:
                if skill_form.cleaned_data.get('DELETE'):
                    continue
                skill_name = skill_form.cleaned_data.get('skill_name', '')
                if skill_name:
                    new_skills.append(skill_name)
            changes = capture_profile_changes(form.instance)
            changes.update(
                capture_related_profile_changes(
                    'skills',
                    old_skills,
                    new_skills,
                )
            )
            form.save()
            skills = skill_formset.save()
            profile.skills.add(*skills)
            record_profile_changes(profile, request.user, changes)
            _stamp_uploaded_profile_proofs(
                profile,
                {
                    'technical_certification_document':
                        'technical_certification_uploaded_at',
                },
                request.FILES,
            )
            changed_fields = set(form.changed_data)
            for skill_form in skill_formset.forms:
                if skill_form.has_changed():
                    changed_fields.update(skill_form.changed_data)
                    if skill_form.cleaned_data.get('DELETE'):
                        changed_fields.add('__deleted__')
            _mark_applicant_for_reverification(
                request,
                profile,
                changed_fields,
                ApplicantSkills if any(
                    skill_form.has_changed()
                    for skill_form in skill_formset.forms
                ) else ApplicantProfile,
            )
            if profile.status == 'approved':
                matches = query_matching_jobs(applicant=profile, total_results=10)
                request.session['job_matches'] = matches['ids']
            else:
                request.session.pop('job_matches', None)
            messages.success(request, 'Skills information saved successfully.')
            return redirect('applicant-documents')
        return render(request, self.template_name, {'form': form, 'skill_formset': skill_formset})

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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        # Bind request.FILES to the form so Cloudinary stores the image
        form = self.form_class(request.POST, request.FILES, instance=self.object)
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        changes = capture_profile_changes(form.instance)
        profile = form.save()
        record_profile_changes(profile, self.request.user, changes)
        _mark_applicant_for_reverification(
            self.request,
            profile,
            form.changed_data,
        )
        messages.success(self.request, 'Documents submitted successfully.')
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

    def post(self, request, *args, **kwargs):
        AuditLog.objects.create(
            user=request.user,
            action='Logout',
            details=f"Applicant {request.user.email} logged out."  # Changed from description to details
        )
        return super().post(request, *args, **kwargs)

class DashBoardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'applicant-dashboard.html'
    context_object_name = 'matching_jobs'
    login_url = reverse_lazy('signin')

    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        context['applicant_profile'] = applicant_profile

      
        matching_list = []

        if applicant_profile:
            # Initialize matching_jobs before checking the applicant's status
            matching_jobs = Jobs.objects.filter(
                status='Active',
                employer__verification_status='verified',
            )

            if applicant_profile.status == 'approved':
                applicant_profile_text = build_applicant_profile_text(
                    applicant_profile
                )

                collection = get_job_collection()
                results = collection.query(
                    query_texts=[applicant_profile_text],
                    n_results=10,
                )

                job_uuids = [
                    metadata['job_uuid']
                    for metadata in results['metadatas'][0]
                    if metadata and 'job_uuid' in metadata
                ]

                recommended_jobs = Jobs.objects.filter(
                    uuid__in=job_uuids,
                    status='Active',
                    employer__verification_status='verified',
                )

                if recommended_jobs.exists():
                    matching_jobs = recommended_jobs

            for job in matching_jobs:
                if job.pk:
                    matching_list.append({
                        'job': job,
                        'score': 88,
                        'edu_score': 100,
                        'exp_score': 85,
                        'skills_score': 80,
                        'certs_score': 50,
                    })

            context['matching_jobs'] = matching_list


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
            if applicant_profile.applicant_id_picture_front or applicant_profile.applicant_id_picture_back:
                completed += 1

            context['profile_strength'] = int((completed / total) * 100)
        else:
            for job in Jobs.objects.filter(status='Active'):
                if job.pk:
                    matching_list.append({
                        'job': job,
                        'score': 75,
                        'edu_score': 80,
                        'exp_score': 70,
                        'skills_score': 75,
                        'certs_score': 40
                    })
            context['matching_jobs'] = matching_list
            context['application_count'] = 0
            context['saved_jobs_count'] = 0
            context['under_review_count'] = 0
            context['shortlisted_count'] = 0
            context['rejected_count'] = 0
            context['withdrawn_count'] = 0
            context['profile_strength'] = 0

        context['total_jobs'] = Jobs.objects.filter(
            status='Active',
            employer__verification_status='verified',
        ).count()
        return context

class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'job_list.html'
    context_object_name = 'jobs'

    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

    def get_queryset(self):
        jobs = Jobs.objects.filter(
            status='Active',
            employer__verification_status='verified',
        )

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
            if applicant_profile.status != 'approved':
                context['matching_jobs'] = Jobs.objects.none()
            else:
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
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

    def get_queryset(self):
        return Jobs.objects.filter(
            status='Active',
            employer__verification_status='verified',
        )

class SortJobView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    context_object_name = 'matching_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

    def get_queryset(self):
        jobs = Jobs.objects.filter(
            status='Active',
            employer__verification_status='verified',
        )
        sort_by = self.request.GET.get('sort_by', 'date_posted')
        if sort_by == 'date_posted':
            return jobs.order_by('-date_posted')
        elif sort_by == 'salary':
            return jobs.order_by('-salary')
        else:
            return jobs

class AppliedJobsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AppliedJobs
    template_name = 'applied_jobs.html'
    context_object_name = 'applied_jobs'

    def test_func(self):
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

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
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

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
        return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'applicant'

    def get_queryset(self):
        jobs = Jobs.objects.filter(
            status='Active',
            employer__verification_status='verified',
        )

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
        applicant_profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        if not applicant_profile or applicant_profile.status != 'approved':
            context['matching_jobs'] = Jobs.objects.none()
        return context

###class ApplyJobView(LoginRequiredMixin, UserPassesTestMixin, View):


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

        job = get_object_or_404(
            Jobs,
            pk=pk,
            status='Active',
            employer__verification_status='verified',
        )
        if AppliedJobs.objects.filter(applicant=applicant_profile, applied_job=job).exists():
            messages.warning(request, 'You have already applied for this job.')
            return redirect('job_details', pk=job.pk)

        AppliedJobs.objects.create(
            employer=job.employer, applicant=applicant_profile,
            applied_job=job, status='pending'
        )

        AuditLog.objects.create(
            user=request.user,
            action='Job Application Submitted',
            description=f"{request.user.email} applied for the job '{job.job_title}'."
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

        job = get_object_or_404(
            Jobs,
            pk=pk,
            status='Active',
            employer__verification_status='verified',
        )
        saved_job, created = SavedJobs.objects.get_or_create(
            applicant=applicant_profile, saved_job=job
        )

        if created:
            messages.success(request, 'Job saved successfully.')
        else:
            messages.info(request, 'You have already saved this job.')

        return redirect('job_details', pk=job.pk)


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
    success_url = reverse_lazy('view_profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile picture updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        context['profile'] = profile
        context['applicant_profile'] = profile
        return context


class MyProfileView(ApplicantRequiredMixin, TemplateView):
    template_name = 'applicant_personal_info_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        context['profile'] = profile
        context['applicant_profile'] = profile
        context['account_email'] = self.request.user.email
        return context

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
            updated_name = full_name.strip()
            name_changed = user.first_name != updated_name
            user.first_name = updated_name
            changes = capture_profile_changes(user) if name_changed else {}
            user.save()
            
            applicant_profile = ApplicantProfile.objects.filter(user=user).first()
            if applicant_profile:
                record_profile_changes(
                    applicant_profile,
                    user,
                    changes,
                    change_model=User,
                )
            if applicant_profile and name_changed:
                _mark_applicant_for_reverification(
                    request,
                    applicant_profile,
                    {'first_name'},
                    change_model=User,
                )
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
            email_changed = user.email != session_email
            user.email = session_email
            if hasattr(user, 'username') and user.username == user.email:
                user.username = session_email
            changes = capture_profile_changes(user) if email_changed else {}
            user.save()
            profile = ApplicantProfile.objects.filter(user=user).first()
            if profile:
                record_profile_changes(
                    profile,
                    user,
                    changes,
                    change_model=User,
                )
            
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
        profile = ApplicantProfile.objects.filter(user=self.request.user).first()
        changes = capture_profile_changes(form.instance)
        response = super().form_valid(form)
        if profile:
            record_profile_changes(
                profile,
                self.request.user,
                changes,
                change_model=User,
            )
            _mark_applicant_for_reverification(
                self.request,
                profile,
                form.changed_data,
                change_model=User,
            )
        messages.success(self.request, 'Username updated successfully.')
        return response


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
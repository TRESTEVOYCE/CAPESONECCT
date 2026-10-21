
from AdminSide.models import EmployerProfile,Jobs,AppliedJobs,ApplicantProfile,User,Notification
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView,TemplateView
from django.views import View
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from AdminSide.services.profile_sensitivity import (
    capture_profile_changes,
    classify_profile_changes,
    mark_profile_for_reverification,
    record_profile_changes,
)
from .forms import EmployerProfileForm,JobsForm,ProfilePictureForm
from AdminSide.models import EmployerProfile, Jobs, AppliedJobs, ApplicantProfile, User
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, TemplateView
from .forms import EmployerProfileForm, JobsForm, ProfilePictureForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LogoutView
from JobMatchingEngine.database import upsert_job_vector, build_job_text,build_applicant_profile_text
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from JobMatchingEngine.config import get_embedding_function
from django.urls import reverse_lazy
import random
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
import math
import json
from django.http import JsonResponse
import json
from .forms import EmployerProfileForm, JobsForm, ProfilePictureForm, JobSkillFormSet

@login_required
def update_applicant_status(request, pk):
    application = get_object_or_404(AppliedJobs, pk=pk, employer=request.user.employer_profile)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'reviewed', 'for interview', 'hired', 'rejected']:
            application.status = new_status
            application.save()
            messages.success(request, "Application status successfully updated.")
        else:
            messages.error(request, "Invalid status selection.")
    return redirect('applicant-detail', pk=application.pk)

@login_required
def send_support_message_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject = data.get('subject', 'CAPESONNECT Employer Support')
            user_message = data.get('message', '')
            
            user_email = getattr(request.user, 'email', None) or 'Not provided'
            sender_info = f"Employer Username: {request.user.username}\nEmail: {user_email}\n\n"
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
from AdminSide.utils import get_admin_users, notify_admins


def _mark_employer_for_reverification(
    request,
    profile,
    changed_fields,
    change_model=None,
):
    classification = classify_profile_changes(
        change_model or profile,
        changed_fields,
    )
    should_notify_admins = (
        classification.requires_reverification
        and profile.verification_status in {'verified', 'pending', 'reverify_pending'}
    )
    status_changed = mark_profile_for_reverification(
        profile,
        changed_fields,
        change_model,
    )
    if status_changed:
        messages.warning(
            request,
            'Your profile has been updated and is pending re-verification. '
            'Job posting is paused until it is approved again.',
        )
    if should_notify_admins:
        notifications = notify_admins(
            title='Employer Profile Updated - Re-Verification Required',
            message=(
                f'{profile.business_name or profile.user.username} updated sensitive '
                'business profile information. Review the profile changes and credentials.'
            ),
            notification_type='RESUBMISSION',
            sender=request.user,
            target_url=reverse(
                'AdminSide:employer_verification',
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

EMPLOYER_NOTIFICATION_TYPES = (
    'NEW_APPLICANT',
    'VERIFICATION_APPROVED',
    'VERIFICATION_REJECTED',
)


class EmployerNotificationAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'employer'


class EmployerNotificationListView(EmployerNotificationAccessMixin, ListView):
    model = Notification
    template_name = 'employer_notification.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        queryset = Notification.objects.filter(
            recipient=self.request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
        )
        self.status_filter = self.request.GET.get('status', 'all').lower()
        if self.status_filter == 'unread':
            queryset = queryset.filter(is_read=False)
        elif self.status_filter == 'read':
            queryset = queryset.filter(is_read=True)
        else:
            self.status_filter = 'all'
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = Notification.objects.filter(
            recipient=self.request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
        )
        context.update({
            'unread_count': notifications.filter(is_read=False).count(),
            'total_count': notifications.count(),
            'selected_status': getattr(self, 'status_filter', 'all'),
        })
        return context


class EmployerNotificationHeaderApiView(EmployerNotificationAccessMixin, View):
    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
        )
        latest_notifications = notifications.order_by('-created_at')[:5]
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
                    'category_label': notification.get_notification_type_display(),
                    'target_url': notification.target_url or '#',
                    'created_at': notification.created_at.strftime('%b %d, %Y %I:%M %p'),
                    'is_read': notification.is_read,
                    'read_url': reverse('employer-notification-read', args=[notification.id]),
                }
                for notification in latest_notifications
            ],
        })


class EmployerMarkNotificationReadView(EmployerNotificationAccessMixin, View):
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
        )
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        unread_count = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
            is_read=False,
        ).count()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'unread_count': unread_count})
        return redirect(notification.target_url or 'employer-notifications')


class EmployerMarkAllNotificationsReadView(EmployerNotificationAccessMixin, View):
    def post(self, request, *args, **kwargs):
        updated_count = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
            is_read=False,
        ).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'updated_count': updated_count,
                'unread_count': 0,
            })
        messages.success(request, f'Marked {updated_count} notification(s) as read.')
        return redirect('employer-notifications')


class EmployerDeleteNotificationView(EmployerNotificationAccessMixin, View):
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
            notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
        )
        notification.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            unread_count = Notification.objects.filter(
                recipient=request.user,
                notification_type__in=EMPLOYER_NOTIFICATION_TYPES,
                is_read=False,
            ).count()
            return JsonResponse({'status': 'success', 'unread_count': unread_count})
        messages.success(request, 'Notification deleted.')
        return redirect('employer-notifications')


#home or the dashboard view for the employer
class HomeView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Jobs
    template_name = 'home.html'
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def get_queryset(self):
        queryset = Jobs.objects.filter(
            employer__user=self.request.user
        ).order_by('-created_at')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(job_title__icontains=query) |
                Q(job_description__icontains=query) |
                Q(place_of_work__icontains=query)
            )

        return queryset[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        applied_jobs = AppliedJobs.objects.filter(
            employer=self.request.user.employer_profile,
            applicant__status='approved',
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

    def form_valid(self, form):
        changes = capture_profile_changes(form.instance)
        employer_profile = getattr(self.request.user, 'employer_profile', None)
        response = super().form_valid(form)
        if employer_profile:
            record_profile_changes(
                employer_profile,
                self.request.user,
                changes,
                change_model=User,
            )
        return response
    
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

    def form_valid(self, form):
        changed_fields = form.changed_data
        changes = capture_profile_changes(form.instance)
        response = super().form_valid(form)
        record_profile_changes(self.object, self.request.user, changes)
        _mark_employer_for_reverification(
            self.request,
            self.object,
            changed_fields,
        )
        return response
    

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

        if not get_admin_users().exists():
            messages.error(request, 'Your appeal could not be sent because no administrator recipients are configured.')
            return redirect('employer-home')

        target_url = reverse(
            'AdminSide:employer_verification',
            kwargs={'uuid': profile.uuid},
        )
        title = 'Appeal for Reverification'
        message = (
            f'{profile.business_name or request.user.username} requested employer profile '
            f'reverification. Reason: {reason}'
        )
        profile.verification_status = 'pending'
        profile.save(update_fields=['verification_status', 'updated_at'])
        notifications = notify_admins(
            title=title,
            message=message,
            notification_type='APPEAL_REVERIFICATION',
            sender=request.user,
            reason=reason,
            target_url=target_url,
        )
        if not notifications:
            messages.error(request, 'Your appeal could not be sent because no administrator recipients are configured.')
            return redirect('employer-home')

        messages.success(request, 'Your appeal was submitted. Administrators were notified.')
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

        queryset = AppliedJobs.objects.filter(
            employer=employer_profile,
            applicant__status='approved',
        ).order_by('-application_date')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(applicant__first_name__icontains=query) |
                Q(applicant__last_name__icontains=query) |
                Q(applied_job__job_title__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_verified'] = (
            self.request.user.employer_profile.verification_status == 'verified'
        )
        return context
    
class ApplicantDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AppliedJobs
    template_name = 'applicant_detail.html'
    context_object_name = 'application'

    def test_func(self):
        employer_profile = getattr(
            self.request.user,
            'employer_profile',
            None
        )

        return (
            self.request.user.role == 'employer'
            and employer_profile is not None
            and employer_profile.verification_status == 'verified'
        )

    def get_queryset(self):
        return AppliedJobs.objects.filter(
            employer=self.request.user.employer_profile,
            applicant__status='approved',
        ).distinct()
    
class ApplicantJobStatusView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AppliedJobs
    fields = ['status']
    success_url = reverse_lazy('employer-home')

    def get_queryset(self):
        return AppliedJobs.objects.filter(employer=self.request.user.employerprofile)

class JobCreationView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('employer-home')

    def test_func(self):
        employer_profile = getattr(
            self.request.user,
            'employer_profile',
            None,
        )
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
            and employer_profile is not None
            and employer_profile.verification_status == 'verified'
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
        
        # Pass an unsaved Jobs() instance so the inline formset renders its extra row
        if self.request.POST:
            context['skill_formset'] = JobSkillFormSet(self.request.POST)
        else:
            context['skill_formset'] = JobSkillFormSet(instance=Jobs())
            
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        skill_formset = context['skill_formset']
        
        if form.is_valid() and skill_formset.is_valid():
            form.instance.employer = self.request.user.employer_profile
            self.object = form.save()
            
            skill_formset.instance = self.object
            skill_formset.save()
            
            upsert_job_vector(self.object)
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Jobs
    form_class = JobsForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('employer-home')
    raise_exception = True

    def test_func(self):
        employer_profile = getattr(self.request.user, 'employer_profile', None)
        return (
            self.request.user.is_authenticated
            and self.request.user.role == 'employer'
            and employer_profile is not None
            and employer_profile.verification_status == 'verified'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employer_profile = getattr(self.request.user, 'employer_profile', None)
        context['is_verified'] = (
            employer_profile is not None
            and employer_profile.verification_status == 'verified'
        )
        
        if self.request.POST:
            context['skill_formset'] = JobSkillFormSet(self.request.POST, instance=self.object)
        else:
            context['skill_formset'] = JobSkillFormSet(instance=self.object)
            
        return context

    def get_queryset(self):
        return Jobs.objects.filter(
            employer=self.request.user.employer_profile
        )

    def form_valid(self, form):
        context = self.get_context_data()
        skill_formset = context['skill_formset']
        
        if form.is_valid() and skill_formset.is_valid():
            self.object = form.save()
            skill_formset.instance = self.object
            skill_formset.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

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

        queryset = Jobs.objects.filter(
            employer__user=self.request.user
        ).order_by('-created_at')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(job_title__icontains=query) |
                Q(job_description__icontains=query) |
                Q(place_of_work__icontains=query)
            )

        return queryset
    
class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Jobs
    template_name = 'job_detail.html'
    context_object_name = 'job'
    raise_exception = True

    def test_func(self):
        user = self.request.user
        employer_profile = getattr(user, 'employer_profile', None)

        return (
            user.is_authenticated
            and user.role == 'employer'
            and employer_profile is not None
            and employer_profile.verification_status == 'verified'
        )

    def get_queryset(self):
        # Employers can only view their own job postings.
        return Jobs.objects.filter(
            employer=self.request.user.employer_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()

        # Get status from query params; default to 'pending'
        selected_status = self.request.GET.get('status', 'pending')

        # Filter applications for this specific job
        applicants = AppliedJobs.objects.filter(
            applied_job=job,
            status=selected_status
        ).order_by('-application_date')

        # Counts for badges/pills
        context['selected_status'] = selected_status
        context['applicants'] = applicants
        context['pending_count'] = AppliedJobs.objects.filter(applied_job=job, status='pending').count()
        context['reviewed_count'] = AppliedJobs.objects.filter(applied_job=job, status='reviewed').count()
        context['interview_count'] = AppliedJobs.objects.filter(applied_job=job, status='for interview').count()
        context['hired_count'] = AppliedJobs.objects.filter(applied_job=job, status='hired').count()
        context['rejected_count'] = AppliedJobs.objects.filter(applied_job=job, status='rejected').count()

        return context

class AccountDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EmployerProfile
    success_url = reverse_lazy('employer-home')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def get_queryset(self):
        return EmployerProfile.objects.filter(user=self.request.user)


class SettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'employer_settings.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = getattr(self.request.user, 'employer_profile', None)
        return context

    def post(self, request, *args, **kwargs):
        full_name = request.POST.get('full_name')
        if full_name:
            employer_profile = getattr(request.user, 'employer_profile', None)
            updated_name = full_name.strip()
            name_changed = request.user.username != updated_name
            request.user.username = updated_name
            changes = capture_profile_changes(request.user) if name_changed else {}
            request.user.save()
            if employer_profile:
                record_profile_changes(
                    employer_profile,
                    request.user,
                    changes,
                    change_model=User,
                )
            if employer_profile and name_changed:
                _mark_employer_for_reverification(
                    request,
                    employer_profile,
                    {'username'},
                    change_model=User,
                )
            messages.success(request, "Your profile name has been successfully updated.")
        
        messages.success(request, "Your employer preferences have been successfully updated.")
        return redirect('employer-settings')
    
class LogoutView(LoginRequiredMixin, LogoutView): 
    next_page = reverse_lazy('landing_page')
     
class EmployerPasswordChangeView(LoginRequiredMixin, UserPassesTestMixin, PasswordChangeView):
    template_name = 'change_password.html'
    success_url = reverse_lazy('employer-settings')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    def form_valid(self, form):
        messages.success(self.request, "Your password has been successfully updated.")
        return super().form_valid(form)

@login_required
def employer_email_change_view(request):
    if request.user.role != 'employer':
        return redirect('employer-home')
        
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
            if hasattr(user, 'username'):
                user.username = session_email
            user.save()
            
            request.session.pop('pending_new_email', None)
            request.session.pop('email_otp_code', None)
            
            messages.success(request, "Your email address and login credentials have been successfully updated.")
            return redirect('employer-settings')
            
    return render(request, 'change_email.html')

def send_email_otp(request):
    if request.method == "POST":
        new_email = request.POST.get("email")
        if not new_email:
            return JsonResponse({"status": "error", "message": "Email is required." }, status=400)
        
        otp_code = str(random.randint(100000, 999999))
        request.session['pending_new_email'] = new_email
        request.session['email_otp_code'] = otp_code
        
        try:
            send_mail(
                subject="Your CAPESONNECT Verification Code",
                message=f"Your One-Time Password (OTP) to change your email is: {otp_code}. Valid for 10 minutes.",
                from_email=None,
                recipient_list=[new_email],
                fail_silently=False,
            )
            return JsonResponse({"status": "success", "message": "OTP sent successfully."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

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

def verify_password_otp_view(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        if user_otp == request.session.get('password_otp'):
            request.session['otp_verified'] = True
            return redirect('employer-password-change')
        else:
            messages.error(request, "Invalid OTP code. Please try again.")
            
    return render(request, 'verify_otp.html')

class SecurePasswordChangeView(PasswordChangeView):
    template_name = 'change_password.html'
    success_url = '/employer/settings/'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('otp_verified', False):
            messages.warning(request, "Please verify your email with an OTP first.")
            return redirect('send-password-otp')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        request = self.request
        request.session.pop('password_otp', None)
        request.session.pop('otp_verified', None)
        messages.success(request, "Your password has been changed successfully.")
        return super().form_valid(form)
    
class HelpPageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'employer_help.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'
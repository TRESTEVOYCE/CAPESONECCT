
from AdminSide.models import EmployerProfile,Jobs,AppliedJobs,ApplicantProfile,User,Notification
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView,TemplateView
from django.views import View
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .forms import EmployerProfileForm,JobsForm,ProfilePictureForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LogoutView
from JobMatchingEngine.database import upsert_job_vector
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Q

import json
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required

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

        # Add search filtering here
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
            employer=employer_profile
        ).order_by('-application_date')

        # Capture search query for applicants using correct field lookups
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
    
#view to display details of a specific applicant
class ApplicantDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AppliedJobs
    template_name = 'applicant_detail.html'
    context_object_name = 'application'  # Matches `object` or `application` in your template

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
            employer=self.request.user.employer_profile
        ).distinct()
    
#view to update the status of an applicant's job application
class ApplicantJobStatusView(LoginRequiredMixin, UserPassesTestMixin,UpdateView):
    model = AppliedJobs
    fields = ['status']
    success_url = reverse_lazy('employer-home')

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
        return context

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

        queryset = Jobs.objects.filter(
            employer__user=self.request.user
        ).order_by('-created_at')

        # Capture search query for jobs
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
    success_url = reverse_lazy('employer-home')

    #to ensure that only authenticated employers can access this view
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'

    #to ensure that the employer can only delete their own profile
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
        # Handle updating the user's name/username from settings
        full_name = request.POST.get('full_name')
        if full_name:
            request.user.username = full_name.strip()
            request.user.save()
            messages.success(request, "Your profile name has been successfully updated.")
        
        # Handle saving other general preferences if needed
        messages.success(request, "Your employer preferences have been successfully updated.")
        return redirect('employer-settings')
    
    
class LogoutView(LoginRequiredMixin,LogoutView): 
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
        
    if request.method == 'POST':
        new_email = request.POST.get('email')
        if new_email:
            # Check if email is already taken
            if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                messages.error(request, "This email address is already in use.")
            else:
                request.user.email = new_email
                request.user.save()
                messages.success(request, "Your email address has been successfully updated.")
                return redirect('employer-settings')
                
    return render(request, 'change_email.html')

User = get_user_model()
def send_email_otp(request):
    if request.method == "POST":
        new_email = request.POST.get("email")
        if not new_email:
            return JsonResponse({"status": "error", "message": "Email is required." }, status=400)
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Store OTP and target email in session temporarily
        request.session['pending_new_email'] = new_email
        request.session['email_otp_code'] = otp_code
        
        # Send email via configured Django EMAIL_BACKEND
        try:
            send_mail(
                subject="Your CAPESONNECT Verification Code",
                message=f"Your One-Time Password (OTP) to change your email is: {otp_code}. Valid for 10 minutes.",
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=[new_email],
                fail_silently=False,
            )
            return JsonResponse({"status": "success", "message": "OTP sent successfully."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

@login_required
def employer_email_change_view(request):
    if request.user.role != 'employer':
        return redirect('employer-home')
        
    if request.method == "POST":
        entered_otp = request.POST.get("otp_code", "").strip()
        
        session_email = request.session.get('pending_new_email')
        session_otp = request.session.get('email_otp_code')
        
        # Validation checks
        if not session_otp or not session_email:
            messages.error(request, "Please request a verification code first.")
        elif entered_otp != session_otp:
            messages.error(request, "Invalid verification code. Please try again.")
        elif User.objects.filter(email=session_email).exclude(pk=request.user.pk).exists():
            messages.error(request, "This email address is already registered to another account.")
        else:
            # Update user's email and username to keep login credentials synchronized
            user = request.user
            user.email = session_email
            
            # If your login relies on username matching the email or being editable
            if hasattr(user, 'username'):
                user.username = session_email
                
            user.save()
            
            # Clear session data
            request.session.pop('pending_new_email', None)
            request.session.pop('email_otp_code', None)
            
            messages.success(request, "Your email address and login credentials have been successfully updated.")
            return redirect('employer-settings')
            
    return render(request, 'change_email.html')


def send_password_otp_view(request):
    # Generate a random 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in session temporarily
    request.session['password_otp'] = otp
    request.session['otp_verified'] = False

    # Send via Gmail (configured in settings.py)
    send_mail(
        subject='Password Change Verification Code — CAPESONCONNECT',
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
            return redirect('employer-password-change') # Proceed to the password form template above
        else:
            messages.error(request, "Invalid OTP code. Please try again.")
            
    return render(request, 'verify_otp.html')


class SecurePasswordChangeView(PasswordChangeView):
    template_name = 'change_password.html'
    success_url = '/employer/settings/'

    def dispatch(self, request, *args, **kwargs):
        # Check if OTP was verified in this session sequence
        if not request.session.get('otp_verified', False):
            messages.warning(request, "Please verify your email with an OTP first.")
            return redirect('send-password-otp')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Clear OTP session flags after successful update
        request = self.request
        request.session.pop('password_otp', None)
        request.session.pop('otp_verified', None)
        messages.success(request, "Your password has been changed successfully.")
        return super().form_valid(form)
    
    
class HelpPageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'employer_help.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'employer'
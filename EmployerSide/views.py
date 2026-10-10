
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
    success_url = reverse_lazy('employer-home')

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
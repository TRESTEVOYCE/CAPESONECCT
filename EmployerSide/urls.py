from django import urls
from django.urls import path
from .views import EmployerProfileCreateView, EmployerReverificationAppealView, HomeView, ApplicantsListView, ApplicantDetailView, JobCreationView, JobUpdateView, JobDeleteView,JobDetailView, AccountDeleteView,ApplicantJobStatusView,ApplicantJobStatusView,LogoutView,JobListView,CompanyProfileView,EmployerProfilePictureView,EmployerNotificationListView,EmployerNotificationHeaderApiView,EmployerMarkNotificationReadView,EmployerMarkAllNotificationsReadView,EmployerDeleteNotificationView

urlpatterns = [
    path('notifications/', EmployerNotificationListView.as_view(), name='employer-notifications'),
    path('notifications/api/header/', EmployerNotificationHeaderApiView.as_view(), name='employer-notifications-header'),
    path('notifications/<int:notification_id>/read/', EmployerMarkNotificationReadView.as_view(), name='employer-notification-read'),
    path('notifications/read-all/', EmployerMarkAllNotificationsReadView.as_view(), name='employer-notifications-read-all'),
    path('notifications/<int:notification_id>/delete/', EmployerDeleteNotificationView.as_view(), name='employer-notification-delete'),
    path('company_profile/',CompanyProfileView.as_view(),name='company_profile_view'),
    path('employer-profile/create/', EmployerProfileCreateView.as_view(), name='employer-profile-create'),
    path('employer-profile/appeal/', EmployerReverificationAppealView.as_view(), name='employer-reverification-appeal'),
    path('home/', HomeView.as_view(), name='employer-home'),
    path('applicants/', ApplicantsListView.as_view(), name='applicants-list'),
    path('applicants/<int:pk>/', ApplicantDetailView.as_view(), name='applicant-detail'),
    path('jobs/create/', JobCreationView.as_view(), name='job_create'),
    path('jobs/<int:pk>/update/', JobUpdateView.as_view(), name='job-update'),
    path('jobs/<int:pk>/delete/', JobDeleteView.as_view(), name='job-delete'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
    path('applicants/<int:pk>/job-status/', ApplicantJobStatusView.as_view(), name='applicant-job-status'),
    path('applicants/<int:pk>/job-status/update/', ApplicantJobStatusView.as_view(), name='applicant-job-status-update'),
    path('logout/',LogoutView.as_view(), name='employer-logout'),
    path('jobs_posted/',JobListView.as_view(),name="employer-job_list"),
    path('employer-profile/picture/',EmployerProfilePictureView.as_view(),name='employer-profile-picture'),

]
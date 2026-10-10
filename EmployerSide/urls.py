from django import urls
from django.urls import path
from EmployerSide import views
from .views import EmployerProfileCreateView, HomeView, ApplicantsListView, ApplicantDetailView, JobCreationView, JobUpdateView, JobDeleteView,JobDetailView, AccountDeleteView,ApplicantJobStatusView,ApplicantJobStatusView,LogoutView,JobListView,CompanyProfileView,EmployerProfilePictureView, SettingsView, EmployerPasswordChangeView, employer_email_change_view , HelpPageView

urlpatterns = [
    path('company_profile/',CompanyProfileView.as_view(),name='company_profile_view'),
    path('employer-profile/create/', EmployerProfileCreateView.as_view(), name='employer-profile-create'),
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
    path('settings/', SettingsView.as_view(), name='employer-settings'),
    path('account/email/', employer_email_change_view, name='employer-email-change'),
    path('account/email/send-otp/', views.send_email_otp, name='send-email-otp'),
# Password Change with OTP Workflow Routes
    path('account/password/request-otp/', views.send_password_otp_view, name='send-password-otp'),
    path('account/password/verify-otp/', views.verify_password_otp_view, name='verify-password-otp'),
    path('account/password/', views.SecurePasswordChangeView.as_view(), name='employer-password-change'),
    
    # NEED/help
    path('help/', HelpPageView.as_view(), name='employer-help'),
    
    
]
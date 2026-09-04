from django import urls
from django.urls import path
from .views import EmployerProfileCreateView, HomeView, ApplicantsListView, ApplicantDetailView, JobCreationView, JobUpdateView, JobDeleteView,JobDetailView, CompanyProfileUpdateView, AccountDeleteView,ApplicantJobStatusView,CompanyProfileView,ApplicantJobStatusView

urlpatterns = [
    path('employer-profile/create/', EmployerProfileCreateView.as_view(), name='employer-profile-create'),
    path('home/', HomeView.as_view(), name='home'),
    path('applicants/', ApplicantsListView.as_view(), name='applicants-list'),
    path('applicants/<int:pk>/', ApplicantDetailView.as_view(), name='applicant-detail'),
    path('jobs/create/', JobCreationView.as_view(), name='job-create'),
    path('jobs/<int:pk>/update/', JobUpdateView.as_view(), name='job-update'),
    path('jobs/<int:pk>/delete/', JobDeleteView.as_view(), name='job-delete'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('company-profile/<int:pk>/update/', CompanyProfileUpdateView.as_view(), name='company-profile-update'),
    path('company-profile/<int:pk>/', CompanyProfileView.as_view(), name='company-profile'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
    path('applicants/<int:pk>/job-status/', ApplicantJobStatusView.as_view(), name='applicant-job-status'),
    path('applicants/<int:pk>/job-status/update/', ApplicantJobStatusView.as_view(), name='applicant-job-status-update'),
]

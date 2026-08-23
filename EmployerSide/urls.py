from django import urls
from django.urls import path
from .views import EmployerProfileCreateView, HomeView, ApplicantsListView, ApplicantDetailView

urlpatterns = [
    path('employer-profile/create/', EmployerProfileCreateView.as_view(), name='employer-profile-create'),
    path('home/', HomeView.as_view(), name='home'),
    path('applicants/', ApplicantsListView.as_view(), name='applicants-list'),
    path('applicants/<int:pk>/', ApplicantDetailView.as_view(), name='applicant-detail'),
]


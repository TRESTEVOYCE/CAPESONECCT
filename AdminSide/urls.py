# capes_admin/urls.py
from django.urls import path
from .views import DashboardView, JobPostingsListView, ApplicantListView, EmployerListView, ReferralListView, SpecialProgramsListView

app_name = 'AdminSide'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('jobs/', JobPostingsListView.as_view(), name='job_postings_list'),
    path('applicants/', ApplicantListView.as_view(), name='applicants_list'),
    path('employers/', EmployerListView.as_view(), name='employer_list'),
    path('referrals/', ReferralListView.as_view(), name='referrals_list'),
    path('special-programs/', SpecialProgramsListView.as_view(), name='special_programs_list'),
]
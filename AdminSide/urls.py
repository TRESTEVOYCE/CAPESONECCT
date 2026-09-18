# capes_admin/urls.py
from django.urls import path
from .views import AdminLoginView, AdminLogoutView, DashboardView, HelpView, JobPostingDetailView, JobPostingsListView, ApplicantListView, ApplicantVerificationView, EmployerListView, EmployerVerificationView, ReferralCreateView, ReferralListView, SpecialProgramsListView, EnrollBeneficiaryView, PesoMonthlyReportView, AccountSettingsView

app_name = 'AdminSide'

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin_login'),
    path('logout/', AdminLogoutView.as_view(), name='admin_logout'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('jobs/', JobPostingsListView.as_view(), name='job_postings_list'),
    path('jobs/<uuid:job_uuid>/', JobPostingDetailView.as_view(), name='job_detail'),
    path('applicants/', ApplicantListView.as_view(), name='applicants_list'),
    path('applicants/<uuid:uuid>/verify/', ApplicantVerificationView.as_view(), name='applicant_verification'),
    path('employers/', EmployerListView.as_view(), name='employer_list'),
    path('employers/<uuid:uuid>/verify/', EmployerVerificationView.as_view(), name='employer_verification'),
    path('referrals/', ReferralListView.as_view(), name='referrals_list'),
    path('referrals/create/', ReferralCreateView.as_view(), name='referrals_form'),
    path('special-programs/', SpecialProgramsListView.as_view(), name='special_programs_list'),
    path('special-programs/enroll/', EnrollBeneficiaryView.as_view(), name='enroll_beneficiary'),
    path('special-programs/<str:program_type>/', SpecialProgramsListView.as_view(), name='special_programs_filtered'),
    path('reports/', PesoMonthlyReportView.as_view(), name='peso_monthly_report'),
    path('reports/excel/', PesoMonthlyReportView.as_view(), {'excel': True}, name='peso_monthly_report_excel'),
    path('account/settings/', AccountSettingsView.as_view(), name='account_settings'),
    path('account/help/', HelpView.as_view(), name='account_help'),
]
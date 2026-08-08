from django.urls import path
from .views import SpecialProgramForEmploymentOfStudentsListView, SpecialProgramForEmploymentOfStudentsDetailView, GovernmentInternshipProgramListView, GovernmentInternshipProgramDetailView, TupadBeneficiaryListView, TupadBeneficiaryDetailView, DisplacedInformalLaborProgramListView, DisplacedInformalLaborProgramDetailView, CareerGuidanceBeneficiaryListView, CareerGuidanceBeneficiaryDetailView

urlpatterns = [
    path('special-programs/', SpecialProgramForEmploymentOfStudentsListView.as_view(), name='special-program-list'),
    path('special-programs/<uuid:uuid>/', SpecialProgramForEmploymentOfStudentsDetailView.as_view(), name='special-program-detail'),
    path('government-internships/', GovernmentInternshipProgramListView.as_view(), name='government-internship-list'),
    path('government-internships/<uuid:uuid>/', GovernmentInternshipProgramDetailView.as_view(), name='government-internship-detail'),
    path('tupad-beneficiaries/', TupadBeneficiaryListView.as_view(), name='tupad-beneficiary-list'),
    path('tupad-beneficiaries/<uuid:uuid>/', TupadBeneficiaryDetailView.as_view(), name='tupad-beneficiary-detail'),
    path('displaced-informal-labor-programs/', DisplacedInformalLaborProgramListView.as_view(), name='displaced-informal-labor-program-list'),
    path('displaced-informal-labor-programs/<uuid:uuid>/', DisplacedInformalLaborProgramDetailView.as_view(), name='displaced-informal-labor-program-detail'),
    path('career-guidance-beneficiaries/', CareerGuidanceBeneficiaryListView.as_view(), name='career-guidance-beneficiary-list'),
    path('career-guidance-beneficiaries/<uuid:uuid>/', CareerGuidanceBeneficiaryDetailView.as_view(), name='career-guidance-beneficiary-detail'),
]
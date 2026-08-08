from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import (
    User,
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    SpecialProgramForEmploymentOfStudents,
    CareerGuidanceBeneficiary,
)


BASE_BENEFICIARY_FIELDS = [
    'first_name',
    'middle_name',
    'last_name',
    'sex',
    'date_of_birth',
    'phone_number',
    'barangay',
    'municipality',
    'province',
    'region',
    'zip_code',
    'daily_salary',
    'start_date',
    'end_date',
    'is_done',
]


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')


# 1. SPES FORM
class SpecialProgramForEmploymentOfStudentsForm(forms.ModelForm):
    class Meta:
        model = SpecialProgramForEmploymentOfStudents

        fields = BASE_BENEFICIARY_FIELDS + [
            'education_level',
            'is_out_of_school_youth',
            'has_graduated',
            'has_nc_certification',
            'is_absorbed_by_employer',
            'school_name',
            'college_program',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 2. GIP FORM
class GovernmentInternshipProgramForm(forms.ModelForm):
    class Meta:
        model = GovernmentInternshipProgram

        fields = BASE_BENEFICIARY_FIELDS + [
            'education_level',
            'has_nc_certification',
            'is_absorbed_by_agency',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 3. TUPAD FORM
class TupadBeneficiaryForm(forms.ModelForm):
    class Meta:
        model = TupadBeneficiary

        fields = BASE_BENEFICIARY_FIELDS + [
            'project_type',
            'project_name',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 4. DILP FORM
class DisplacedInformalLaborProgramForm(forms.ModelForm):
    class Meta:
        model = DisplacedInformalLaborProgram

        fields = BASE_BENEFICIARY_FIELDS + [
            'project_category',
            'project_classification',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 5. CAREER GUIDANCE FORM
class CareerGuidanceBeneficiaryForm(forms.ModelForm):
    class Meta:
        model = CareerGuidanceBeneficiary

        fields = BASE_BENEFICIARY_FIELDS + [
            'participant_category',
            'activity_type',
            'school_or_institution',
            'preferred_curriculum_exit',
            'conducted_date',
            'has_received_lmi_materials',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'conducted_date': forms.DateInput(attrs={'type': 'date'}),
        }
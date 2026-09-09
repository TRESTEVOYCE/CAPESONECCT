from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import (
    User,
    EmployerProfile,
    Jobs, 
    GovernmentInternshipProgram,
    TupadBeneficiary,
    DisplacedInformalLaborProgram,
    SpecialProgramForEmploymentOfStudents,
    CareerGuidanceBeneficiary,
)

class TailwindFormMixin:
    """Applies clean Tailwind CSS classes automatically to all form fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-[#112954] focus:ring-[#112954] border-slate-300 rounded'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full text-xs border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[#112954]'
                })

class EmployerRegistrationForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = [
            'business_name', 'trade_name', 'acronym', 'office_type', 
            'tin_number', 'employer_type', 'total_workforce', 'line_of_business',
            'street_address', 'barangay', 'municipality', 'province',
            'owner_name', 'designation', 'contact_person', 'contact_position',
            'telephone_number', 'mobile_number', 'email',
            'certificate_of_registration', 'dti_sec_registration', 'business_permit',
            'public_doc_type', 'public_verification_document'
        ]

class EmployerJobVacancyForm(TailwindFormMixin, forms.ModelForm):
    """Used in the employer's own dashboard. Automatically handles current employer context."""
    class Meta:
        model = Jobs
        exclude = ['employer', 'status', 'created_at']
        widgets = {
            'job_posting_expiry': forms.DateInput(attrs={'type': 'date'}),
            'job_description': forms.Textarea(attrs={'rows': 3}),
            'other_qualifications': forms.Textarea(attrs={'rows': 2}),
        }

class EmployerVerificationForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ['employer_type', 'office_type', 'public_doc_type', 'public_verification_document']
        widgets = {
            'employer_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_employer_type'}),
            'office_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_office_type'}),
            'public_doc_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_public_doc_type'}),
            'public_verification_document': forms.FileInput(attrs={'class': 'form-control', 'id': 'id_public_verification_document'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        employer_type = cleaned_data.get('employer_type')
        public_doc_type = cleaned_data.get('public_doc_type')
        document = cleaned_data.get('public_verification_document')

        # Enforce document requirements for government agencies
        if self.instance and self.instance.is_public_agency:
            if not public_doc_type:
                self.add_error('public_doc_type', 'Please select a document type for government verification.')
            if not document and not self.instance.public_verification_document:
                self.add_error('public_verification_document', 'Please upload a proof document to proceed.')

        return cleaned_data
    
class JobVacancyForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Jobs
        fields = [
            'employer', 'job_title', 'job_description', 'nature_of_work',
            'place_of_work', 'salary', 'vacancy', 'application_quota', 'work_experience_months',
            'other_qualifications', 'accepts_pwd', 'pwd_disabilities',
            'accepts_ofw', 'educational_level', 'course_or_strand',
            'required_license', 'required_eligibility', 'required_certification',
            'languages_spoken', 'job_posting_expiry'
        ]
        widgets = {
            'job_posting_expiry': forms.DateInput(attrs={'type': 'date'}),
            'job_description': forms.Textarea(attrs={'rows': 3}),
            'other_qualifications': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit employers choices to verified employers only
        self.fields['employer'].queryset = EmployerProfile.objects.filter(verification_status='verified')

        
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
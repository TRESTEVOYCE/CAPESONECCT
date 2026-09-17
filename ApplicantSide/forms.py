from django import forms

from .models import (
    ApplicantProfile,
    ApplicantSkills,
)


class ApplicantPersonalInfoForm(forms.ModelForm):

    class Meta:
        model = ApplicantProfile

        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'date_of_birth',
            'sex',
            'civil_status',
            'phone_number',
            'house_street',
            'barangay',
            'municipality',
            'province',
            'region',
            'zip_code',
            'employment_status',
            'unemployment_reason',
            'actively_looking',
            'looking_duration',
            'is_4ps_beneficiary',
            'household_id_no',
            'is_ofw',
            'expected_salary',
        ]


class ApplicantEducationForm(forms.ModelForm):

    class Meta:
        model = ApplicantProfile

        fields = [
            'education_level',
            'school_name',
            'course_program',
            'year_graduated',
        ]


class ApplicantSkillForm(forms.ModelForm):

    class Meta:
        model = ApplicantSkills

        fields = [
            'skill_name',
        ]


ApplicantSkillFormSet = forms.modelformset_factory(
    ApplicantSkills,
    form=ApplicantSkillForm,
    extra=1,
    can_delete=True
)


class ApplicantPreferredJobForm(forms.ModelForm):

    class Meta:
        model = ApplicantProfile

        fields = [
            'preferred_job',
        ]


class ApplicantDocumentsForm(forms.ModelForm):

    class Meta:
        model = ApplicantProfile

        fields = [
            'resume',
            'curriculum_vitae',
            'applicant_id_picture',
        ]
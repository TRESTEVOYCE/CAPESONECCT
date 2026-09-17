from django import forms

from .models import (
    ApplicantProfile,
    ApplicantSkills,
)

TAILWIND_INPUT_CLASSES = {
    'class': 'border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 w-full bg-white text-slate-800'
}

def apply_tailwind_widgets(form):
    
    for field_name, field in form.fields.items():
        existing_class = field.widget.attrs.get('class', '')
        new_class = TAILWIND_INPUT_CLASSES['class']
        
        if isinstance(field.widget, (forms.FileInput, forms.ClearableFileInput)):
            field.widget.attrs['class'] = 'block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
        elif isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = 'h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500'
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = new_class + ' pr-8'
        else:
            field.widget.attrs['class'] = f"{existing_class} {new_class}".strip()

class ApplicantPersonalInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

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
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class ApplicantEducationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'education_level',  
        ]


class ApplicantSkillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'preferred_job',
        ]


class ApplicantDocumentsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'resume',
            'curriculum_vitae',
            'applicant_id_picture',
        ]
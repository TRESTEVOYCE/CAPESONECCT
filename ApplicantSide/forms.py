from django import forms

from AdminSide.models import (
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
            field.widget.attrs['class'] = 'h-4 w-4 rounded border-stone-300 text-teal-600 focus:ring-teal-500'
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = new_class + ' pr-8'
        else:
            field.widget.attrs['class'] = f"{existing_class} {new_class}".strip()


class ApplicantPersonalInfoForm(forms.ModelForm):
    # NSRP UI Helper fields mapped or handled via clean methods
    disability_visual = forms.BooleanField(required=False)
    disability_hearing = forms.BooleanField(required=False)
    disability_speech = forms.BooleanField(required=False)
    disability_physical = forms.BooleanField(required=False)
    disability_others = forms.BooleanField(required=False)

    emp_employed = forms.BooleanField(required=False)
    emp_unemployed = forms.BooleanField(required=False)
    emp_retired = forms.BooleanField(required=False)
    emp_wage_employed = forms.BooleanField(required=False)
    emp_new_entrant = forms.BooleanField(required=False)
    emp_terminated_local = forms.BooleanField(required=False)
    emp_self_employed = forms.BooleanField(required=False)
    emp_finished_contract = forms.BooleanField(required=False)
    emp_terminated_abroad = forms.BooleanField(required=False)
    emp_resigned = forms.BooleanField(required=False)
    
     #sex & civil status
    sex_male = forms.BooleanField(required=False)
    sex_female = forms.BooleanField(required=False)
    civil_single = forms.BooleanField(required=False)
    civil_married = forms.BooleanField(required=False)
    civil_widowed = forms.BooleanField(required=False)
    civil_separated = forms.BooleanField(required=False)
    civil_others = forms.BooleanField(required=False)
    civil_status_specify = forms.CharField(required=False, max_length=100)

    # 3-Row Job Preferences (UI helper inputs)
    preferred_occupation_1 = forms.CharField(required=False)
    preferred_industry_1 = forms.CharField(required=False)
    preferred_occupation_2 = forms.CharField(required=False)
    preferred_industry_2 = forms.CharField(required=False)
    preferred_occupation_3 = forms.CharField(required=False)
    preferred_industry_3 = forms.CharField(required=False)
    preferred_location_local = forms.CharField(required=False)
    preferred_location_overseas = forms.CharField(required=False)


# Multi-row helper slots (Training / Work)
    training_title_1 = forms.CharField(required=False)
    training_duration_1 = forms.CharField(required=False)
    training_institution_1 = forms.CharField(required=False)
    training_cert_1 = forms.CharField(required=False)
    training_completed_1 = forms.BooleanField(required=False)
    
    work_company_1 = forms.CharField(required=False)
    work_address_1 = forms.CharField(required=False)
    work_position_1 = forms.CharField(required=False)
    work_dates_1 = forms.CharField(required=False)
    work_status_1 = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    def save(self, commit=True):
        instance = super().save(commit=False)
        cd = self.cleaned_data

        # Map sex toggle/checkboxes if model expects string/char
        if cd.get('sex_male'):
            instance.sex = 'M'
        elif cd.get('sex_female'):
            instance.sex = 'F'

        # Map disabilities into a comma-delimited string or JSON payload
        disabilities = []
        if cd.get('disability_visual'): disabilities.append('Visual')
        if cd.get('disability_hearing'): disabilities.append('Hearing')
        if cd.get('disability_speech'): disabilities.append('Speech')
        if cd.get('disability_physical'): disabilities.append('Physical')
        if cd.get('disability_others'): disabilities.append('Others')
        if disabilities and hasattr(instance, 'disability_type'):
            instance.disability_type = ", ".join(disabilities)

        # Map employment status single primary flag
        if cd.get('emp_employed'): instance.employment_status = 'employed'
        elif cd.get('emp_unemployed'): instance.employment_status = 'unemployed'
        elif cd.get('emp_self_employed'): instance.employment_status = 'self-employed'
        elif cd.get('emp_retired'): instance.employment_status = 'retired'

        if commit:
            instance.save()
            self.save_m2m()
        return instance
     
    class Meta:
        model = ApplicantProfile
        fields = [
            'first_name', 'middle_name', 'last_name', 'suffix',
            'date_of_birth', 'sex', 'civil_status', 'place_of_birth', 'nationality',
            'phone_number', 'mobile_number_secondary', 'landline_number', 'email_address',
            'weight', 'height', 'phone_number', 'house_street', 'barangay',
            'municipality', 'province', 'region', 'zip_code',
            'employment_status', 'unemployment_reason',
            'actively_looking', 'looking_duration',
            'willing_to_work_immediately', 'when_willing_to_work',
            'is_4ps_beneficiary', 'household_id_no',
            'is_ofw', 'returning_to_ph_to_work', 'expected_salary',
        
            'school_university', 'course_program', 'year_graduated_attended',
            'award_1', 'award_2', 'award_3', 
            'school_status_yes', 'school_status_no',
            
            
            # Part 4: Training & Eligibility
            'training_title_1', 'training_hours_1', 'training_institution_1', 'training_date_1',
            'training_title_2', 'training_hours_2', 'training_institution_2', 'training_date_2',
    
    # Part 5: Job Preference
            'pref_local', 'pref_overseas', 
            'pref_occupation_1', 'pref_occupation_2', 'pref_occupation_3',
            'pref_location_local', 'pref_location_overseas', 'pref_salary',
    
    # Part 7: Skills
            'skill_computer', 'skill_driving', 'skill_customer_service',
            'skill_bookkeeping', 'skill_carpentry', 'skill_welding', 'other_skills',
    
    # Part 8: Certification & Documents
            'certification_agree', 'resume_file', 'supporting_doc',
]
              
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'height': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'cm'}),
            'weight': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'kg'}),
        }


class ApplicantEducationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'education_level', 
            'edu_no_formal', 'edu_college_grad', 'edu_elem_level', 'edu_elem_grad',
            'edu_hs_level', 'edu_hs_grad', 'edu_post_grad', 'edu_college_level', 'edu_tech_voc',
            'school_university', 'course_program', 'year_graduated_attended',
            'award_1', 'award_2', 'award_3', 
            'school_status_yes', 'school_status_no',
            
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
    valid_id = forms.FileField(required=False)
    resume = forms.FileField(required=False)
    tor_diploma = forms.FileField(required=False)

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
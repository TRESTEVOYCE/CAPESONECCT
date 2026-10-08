from django import forms
from AdminSide.models import ApplicantProfile,ApplicantSkills,ApplicantWorkExperience




TAILWIND_INPUT_CLASSES = {
    'class': (
        'border border-slate-300 rounded-xl px-3.5 py-2 text-sm '
        'focus:outline-none focus:ring-2 focus:ring-indigo-500/20 '
        'focus:border-indigo-600 w-full bg-white text-slate-800'
    )
}


def apply_tailwind_widgets(form):
    for field_name, field in form.fields.items():
        existing_class = field.widget.attrs.get('class', '')
        new_class = TAILWIND_INPUT_CLASSES['class']

        if isinstance(field.widget, (forms.FileInput, forms.ClearableFileInput)):
            field.widget.attrs['class'] = (
                'block w-full text-xs text-slate-500 '
                'file:mr-4 file:py-2 file:px-4 '
                'file:rounded-xl file:border-0 '
                'file:text-xs file:font-semibold '
                'file:bg-indigo-50 file:text-indigo-700 '
                'hover:file:bg-indigo-100'
            )

        elif isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = (
                'h-4 w-4 rounded border-stone-300 '
                'text-teal-600 focus:ring-teal-500'
            )

        elif isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = new_class + ' pr-8'

        else:
            field.widget.attrs['class'] = f'{existing_class} {new_class}'.strip()


class ApplicantPersonalInfoForm(forms.ModelForm):

    # SEX
    sex_male = forms.BooleanField(required=False)
    sex_female = forms.BooleanField(required=False)

    # CIVIL STATUS
    civil_single = forms.BooleanField(required=False)
    civil_married = forms.BooleanField(required=False)
    civil_widowed = forms.BooleanField(required=False)

    # EMPLOYMENT STATUS
    emp_employed = forms.BooleanField(required=False)
    emp_unemployed = forms.BooleanField(required=False)

    # UNEMPLOYMENT REASON
    emp_retired = forms.BooleanField(required=False)
    emp_new_entrant = forms.BooleanField(required=False)
    emp_terminated_local = forms.BooleanField(required=False)
    emp_finished_contract = forms.BooleanField(required=False)
    emp_terminated_abroad = forms.BooleanField(required=False)
    emp_resigned = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_tailwind_widgets(self)

        # -------------------------
        # SEX
        # -------------------------

        if self.instance.sex == 'M':
            self.initial['sex_male'] = True

        elif self.instance.sex == 'F':
            self.initial['sex_female'] = True

        # -------------------------
        # CIVIL STATUS
        # -------------------------

        if self.instance.civil_status == 'single':
            self.initial['civil_single'] = True

        elif self.instance.civil_status == 'married':
            self.initial['civil_married'] = True

        elif self.instance.civil_status == 'widowed':
            self.initial['civil_widowed'] = True

        # -------------------------
        # EMPLOYMENT STATUS
        # -------------------------

        if self.instance.employment_status == 'employed':
            self.initial['emp_employed'] = True

        elif self.instance.employment_status == 'unemployed':
            self.initial['emp_unemployed'] = True

            # Restore unemployment reason
            reason = self.instance.unemployment_reason

            if reason == 'retired':
                self.initial['emp_retired'] = True

            elif reason == 'fresh_grad':
                self.initial['emp_new_entrant'] = True

            elif reason == 'laid_off_local':
                self.initial['emp_terminated_local'] = True

            elif reason == 'finished_contract':
                self.initial['emp_finished_contract'] = True

            elif reason == 'laid_off_abroad':
                self.initial['emp_terminated_abroad'] = True

            elif reason == 'resigned':
                self.initial['emp_resigned'] = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        # -------------------------
        # SEX
        # -------------------------

        if self.cleaned_data.get('sex_male'):
            instance.sex = 'M'

        elif self.cleaned_data.get('sex_female'):
            instance.sex = 'F'

        # -------------------------
        # CIVIL STATUS
        # -------------------------

        if self.cleaned_data.get('civil_single'):
            instance.civil_status = 'single'

        elif self.cleaned_data.get('civil_married'):
            instance.civil_status = 'married'

        elif self.cleaned_data.get('civil_widowed'):
            instance.civil_status = 'widowed'

        # -------------------------
        # EMPLOYMENT STATUS
        # -------------------------

        if self.cleaned_data.get('emp_employed'):
            instance.employment_status = 'employed'
            instance.unemployment_reason = None

        elif self.cleaned_data.get('emp_unemployed'):
            instance.employment_status = 'unemployed'

            # -------------------------
            # UNEMPLOYMENT REASON
            # -------------------------

            if self.cleaned_data.get('emp_new_entrant'):
                instance.unemployment_reason = 'fresh_grad'

            elif self.cleaned_data.get('emp_finished_contract'):
                instance.unemployment_reason = 'finished_contract'

            elif self.cleaned_data.get('emp_resigned'):
                instance.unemployment_reason = 'resigned'

            elif self.cleaned_data.get('emp_retired'):
                instance.unemployment_reason = 'retired'

            elif self.cleaned_data.get('emp_terminated_local'):
                instance.unemployment_reason = 'laid_off_local'

            elif self.cleaned_data.get('emp_terminated_abroad'):
                instance.unemployment_reason = 'laid_off_abroad'

            else:
                instance.unemployment_reason = None

        if commit:
            instance.save()

        return instance

    class Meta:
        model = ApplicantProfile

        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'suffix',

            'date_of_birth',
            'place_of_birth',
            'nationality',

            'weight',
            'height',

            'actively_looking',
            'looking_duration',
            'willing_to_work_immediately',
            'when_willing_to_work',
            'is_4ps_beneficiary',
            'household_id_no',
            'is_ofw',
            'returning_to_ph_to_work',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'height': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'placeholder': 'cm'
                }
            ),

            'weight': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'placeholder': 'kg'
                }
            ),
        }




class ApplicantAddressForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile

        fields = [ 'house_street', 'barangay', 'municipality', 'province', 'region', 'zip_code', 'phone_number', 'mobile_number_secondary', 'landline_number', 'email_address'] 


class ApplicantEducationForm(forms.ModelForm):

    highest_educational_attainment = forms.ChoiceField(
        required=False,
        choices=[
            ('no_formal', 'No Formal Education'),
            ('elem_level', 'Elementary Level'),
            ('elem_grad', 'Elementary Graduate'),
            ('hs_level', 'High School Level'),
            ('hs_grad', 'High School Graduate'),
            ('college_level', 'College Level'),
            ('college_grad', 'College Graduate'),
            ('tech_voc', 'Technical Vocational Graduate'),
            ('post_grad', 'Post Graduate'),
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        education_fields = [
            'no_formal',
            'elem_level',
            'elem_grad',
            'hs_level',
            'hs_grad',
            'college_level',
            'college_grad',
            'tech_voc',
            'post_grad',
        ]

        for field_name in education_fields:
            if getattr(self.instance, f'edu_{field_name}', False):
                self.initial['highest_educational_attainment'] = field_name
                break

        apply_tailwind_widgets(self)

    def save(self, commit=True):
        instance = super().save(commit=False)

        attainment = self.cleaned_data.get(
            'highest_educational_attainment'
        )

        education_fields = [
            'edu_no_formal',
            'edu_elem_level',
            'edu_elem_grad',
            'edu_hs_level',
            'edu_hs_grad',
            'edu_college_level',
            'edu_college_grad',
            'edu_tech_voc',
            'edu_post_grad',
        ]

        for field in education_fields:
            setattr(instance, field, False)

        if attainment:
            setattr(instance, f'edu_{attainment}', True)

        if commit:
            instance.save()

        return instance

    class Meta:
        model = ApplicantProfile

        fields = [
            'school_status_yes',
            'school_status_no',

            'school_university',
            'course_program',
            'year_graduated_attended',

            'award_1',
            'award_2',
            'award_3',
        ]

        widgets = {
            'year_graduated_attended': forms.DateInput(
                attrs={'type': 'month'}
            ),
        }


class ApplicantTrainingForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile

        fields = [
            'training_title_1',
            'training_hours_1',
            'training_institution_1',
            'training_date_1',

            'training_title_2',
            'training_hours_2',
            'training_institution_2',
            'training_date_2',
        ]

        widgets = {
            'training_hours_1': forms.NumberInput(
                attrs={'min': '0'}
            ),

            'training_hours_2': forms.NumberInput(
                attrs={'min': '0'}
            ),

            'training_date_1': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'training_date_2': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }



class ApplicantPreferredJobForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile

        fields = [
            'pref_local',
            'pref_overseas',

            'pref_occupation_1',
            'pref_occupation_2',
            'pref_occupation_3',

            'pref_location_local',
            'pref_location_overseas',

            'pref_salary',
        ]



class ApplicantWorkExperienceForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantWorkExperience

        fields = [
            'company',
            'address',
            'position',
            'dates',
            'status',
        ]


ApplicantWorkExperienceFormSet = forms.inlineformset_factory(
    ApplicantProfile,
    ApplicantWorkExperience,
    form=ApplicantWorkExperienceForm,
    extra=1,
    can_delete=True
)


# ============================================================
# STEP 7
# SKILLS
# ============================================================

class ApplicantSkillsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile

        fields = [
            'skill_computer',
            'skill_driving',
            'skill_customer_service',
            'skill_bookkeeping',
            'skill_carpentry',
            'skill_welding',
            'other_skills',
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


class ApplicantDocumentsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile

        fields = [
            'certification_agree',
            'resume_file',
            'supporting_doc',
        ]


class ProfilePictureForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile

        fields = [
            'applicant_id_picture'
        ]
from django import forms
from AdminSide.models import ApplicantProfile, ApplicantSkills, ApplicantWorkExperience, User
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from PIL import Image, UnidentifiedImageError


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


def validate_proof_document(uploaded_file):
    if uploaded_file.size > 5 * 1024 * 1024:
        raise ValidationError('Supporting documents must be 5MB or smaller.')

    extension = uploaded_file.name.rsplit('.', 1)[-1].lower()
    if extension not in {'pdf', 'jpg', 'jpeg', 'png'}:
        raise ValidationError('Upload a PDF, JPG, JPEG, or PNG document.')
    if extension == 'pdf':
        if uploaded_file.read(5) != b'%PDF-':
            raise ValidationError('Upload a valid PDF document.')
        uploaded_file.seek(0)
        return uploaded_file

    try:
        with Image.open(uploaded_file) as image:
            if image.format not in {'JPEG', 'PNG'}:
                raise ValidationError('Upload a valid JPG or PNG image.')
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationError('Upload a valid JPG or PNG image.') from exc
    finally:
        uploaded_file.seek(0)
    return uploaded_file


class ApplicantProofDocumentFormMixin:
    proof_document_fields = ()
    proof_required_for_fields = ()
    proof_required_message = ''

    def clean(self):
        cleaned_data = super().clean()
        uploaded_fields = set()
        for field_name in self.proof_document_fields:
            uploaded_file = self.files.get(self.add_prefix(field_name))
            if uploaded_file:
                uploaded_fields.add(field_name)
                try:
                    validate_proof_document(uploaded_file)
                except ValidationError as error:
                    self.add_error(field_name, error)

        profile = getattr(self.instance, 'applicant', self.instance)
        if (
            profile.status in {'approved', 'reverify_pending'}
            and set(self.changed_data).intersection(self.proof_required_for_fields)
            and not uploaded_fields
        ):
            self.add_error(None, self.proof_required_message)
        return cleaned_data


class ApplicantPersonalInfoForm(forms.ModelForm):
    sex_male = forms.BooleanField(required=False)
    sex_female = forms.BooleanField(required=False)
    civil_single = forms.BooleanField(required=False)
    civil_married = forms.BooleanField(required=False)
    civil_widowed = forms.BooleanField(required=False)
    emp_employed = forms.BooleanField(required=False)
    emp_unemployed = forms.BooleanField(required=False)
    emp_retired = forms.BooleanField(required=False)
    emp_new_entrant = forms.BooleanField(required=False)
    emp_terminated_local = forms.BooleanField(required=False)
    emp_finished_contract = forms.BooleanField(required=False)
    emp_terminated_abroad = forms.BooleanField(required=False)
    emp_resigned = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

        if self.instance.sex == 'M':
            self.initial['sex_male'] = True
        elif self.instance.sex == 'F':
            self.initial['sex_female'] = True

        if self.instance.civil_status == 'single':
            self.initial['civil_single'] = True
        elif self.instance.civil_status == 'married':
            self.initial['civil_married'] = True
        elif self.instance.civil_status == 'widowed':
            self.initial['civil_widowed'] = True

        if self.instance.employment_status == 'employed':
            self.initial['emp_employed'] = True
        elif self.instance.employment_status == 'unemployed':
            self.initial['emp_unemployed'] = True
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

    def clean(self):
        cleaned_data = super().clean()

        sex_choices = (
            cleaned_data.get('sex_male'),
            cleaned_data.get('sex_female'),
        )
        if sum(bool(choice) for choice in sex_choices) != 1:
            raise forms.ValidationError('Select exactly one sex option.')

        civil_status_choices = (
            cleaned_data.get('civil_single'),
            cleaned_data.get('civil_married'),
            cleaned_data.get('civil_widowed'),
            cleaned_data.get('civil_divorced'),
        )
        if sum(bool(choice) for choice in civil_status_choices) != 1:
            raise forms.ValidationError('Select exactly one civil status option.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('sex_male'):
            instance.sex = 'M'
        elif self.cleaned_data.get('sex_female'):
            instance.sex = 'F'

        if self.cleaned_data.get('civil_single'):
            instance.civil_status = 'single'
        elif self.cleaned_data.get('civil_married'):
            instance.civil_status = 'married'
        elif self.cleaned_data.get('civil_widowed'):
            instance.civil_status = 'widowed'

        if self.cleaned_data.get('emp_employed'):
            instance.employment_status = 'employed'
            instance.unemployment_reason = None
        elif self.cleaned_data.get('emp_unemployed'):
            instance.employment_status = 'unemployed'
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

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')

        if dob:
            today = timezone.localdate()

            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )

            if age < 18:
                raise ValidationError(
                    'Applicant must be at least 18 years old.'
                )

        return dob


    class Meta:
        model = ApplicantProfile
        fields = [
            'first_name', 'middle_name', 'last_name', 'suffix',
            'date_of_birth', 'place_of_birth', 'nationality',
            'weight', 'height', 'actively_looking', 'looking_duration',
            'willing_to_work_immediately', 'when_willing_to_work',
            'is_4ps_beneficiary', 'household_id_no', 'is_ofw', 'returning_to_ph_to_work',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'height': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'cm'}),
            'weight': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'kg'}),
        }


class ApplicantAddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in (
            'phone_number',
            'barangay',
            'municipality',
            'province'
        ):
            self.fields[field_name].required = True

        apply_tailwind_widgets(self)

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')

        if phone and not phone.isdigit():
            raise ValidationError(
                'Phone number must contain numbers only.'
            )

        return phone

    def clean_mobile_number_secondary(self):
        mobile = self.cleaned_data.get('mobile_number_secondary')

        if mobile and not mobile.isdigit():
            raise ValidationError(
                'Secondary mobile number must contain numbers only.'
            )

        return mobile

    def clean_landline_number(self):
        landline = self.cleaned_data.get('landline_number')

        if landline and not landline.isdigit():
            raise ValidationError(
                'Landline number must contain numbers only.'
            )

        return landline

    class Meta:
        model = ApplicantProfile
        fields = ['house_street', 'barangay', 'municipality', 'province', 'region', 'zip_code', 'phone_number', 'mobile_number_secondary', 'landline_number', 'email_address'] 


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
            'no_formal', 'elem_level', 'elem_grad', 'hs_level',
            'hs_grad', 'college_level', 'college_grad', 'tech_voc', 'post_grad',
        ]
        for field_name in education_fields:
            if getattr(self.instance, f'edu_{field_name}', False):
                self.initial['highest_educational_attainment'] = field_name
                break
        apply_tailwind_widgets(self)

    def save(self, commit=True):
        instance = super().save(commit=False)
        attainment = self.cleaned_data.get('highest_educational_attainment')
        education_fields = [
            'edu_no_formal', 'edu_elem_level', 'edu_elem_grad',
            'edu_hs_level', 'edu_hs_grad', 'edu_college_level',
            'edu_college_grad', 'edu_tech_voc', 'edu_post_grad',
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
            'school_status_yes', 'school_status_no',
            'school_university', 'course_program', 'year_graduated_attended',
            'award_1', 'award_2', 'award_3',
        ]
        widgets = {
            'year_graduated_attended': forms.DateInput(attrs={'type': 'month'}),
        }


class ApplicantTrainingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'training_title_1', 'training_hours_1', 'training_institution_1', 'training_date_1',
            'training_title_2', 'training_hours_2', 'training_institution_2', 'training_date_2',
        ]
        widgets = {
            'training_hours_1': forms.NumberInput(attrs={'min': '0'}),
            'training_hours_2': forms.NumberInput(attrs={'min': '0'}),
            'training_date_1': forms.DateInput(attrs={'type': 'date'}),
            'training_date_2': forms.DateInput(attrs={'type': 'date'}),
        }


class ApplicantPreferredJobForm(forms.ModelForm):
    pref_salary = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Select expected salary range'),
            ('Below 10,000', 'Below ₱10,000'),
            ('10,000 - 15,000', '₱10,000 - ₱15,000'),
            ('15,001 - 20,000', '₱15,001 - ₱20,000'),
            ('20,001 - 30,000', '₱20,001 - ₱30,000'),
            ('30,001 - 50,000', '₱30,001 - ₱50,000'),
            ('50,001 - 80,000', '₱50,001 - ₱80,000'),
            ('80,001 and above', '₱80,001 and above'),
        ]
    )
    
    pref_location_local_1 = forms.CharField(required=False)
    pref_location_local_2 = forms.CharField(required=False)
    pref_location_local_3 = forms.CharField(required=False)
    
    pref_location_overseas_1 = forms.CharField(required=False)
    pref_location_overseas_2 = forms.CharField(required=False)
    pref_location_overseas_3 = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'pref_local', 'pref_overseas',
            'pref_occupation_1', 'pref_occupation_2', 'pref_occupation_3',
            'pref_salary',
        ]


class ApplicantWorkExperienceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantWorkExperience
        fields = ['company', 'address', 'position', 'dates', 'status']


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
    skill_innovation = forms.BooleanField(required=False)
    skill_team_work = forms.BooleanField(required=False)
    skill_multitasking = forms.BooleanField(required=False)
    skill_work_ethics = forms.BooleanField(required=False)
    skill_self_motivation = forms.BooleanField(required=False)
    skill_creative_problem_solving = forms.BooleanField(required=False)
    skill_problem_solving = forms.BooleanField(required=False)
    skill_critical_thinking = forms.BooleanField(required=False)
    skill_decision_making = forms.BooleanField(required=False)
    skill_stress_tolerance = forms.BooleanField(required=False)
    skill_planning_organizing = forms.BooleanField(required=False)
    skill_social_perceptiveness = forms.BooleanField(required=False)
    skill_english_functional = forms.BooleanField(required=False)
    skill_english_comprehension = forms.BooleanField(required=False)
    skill_math_functional = forms.BooleanField(required=False)

    skill_carpentry = forms.BooleanField(required=False)
    skill_masonry = forms.BooleanField(required=False)
    skill_welding = forms.BooleanField(required=False)
    skill_auto_mechanic = forms.BooleanField(required=False)
    skill_plumbing = forms.BooleanField(required=False)
    skill_driving = forms.BooleanField(required=False)
    skill_gardening = forms.BooleanField(required=False)
    skill_tailoring = forms.BooleanField(required=False)
    skill_photography = forms.BooleanField(required=False)
    skill_hairdressing = forms.BooleanField(required=False)
    skill_cooking = forms.BooleanField(required=False)
    skill_baking = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantProfile
        fields = [
            'skill_innovation', 'skill_team_work', 'skill_multitasking', 'skill_work_ethics', 
            'skill_self_motivation', 'skill_creative_problem_solving', 'skill_problem_solving', 
            'skill_critical_thinking', 'skill_decision_making', 'skill_stress_tolerance', 
            'skill_planning_organizing', 'skill_social_perceptiveness', 'skill_english_functional', 
            'skill_english_comprehension', 'skill_math_functional',
            'skill_carpentry', 'skill_masonry', 'skill_welding', 'skill_auto_mechanic', 
            'skill_plumbing', 'skill_driving', 'skill_gardening', 'skill_tailoring', 
            'skill_photography', 'skill_hairdressing', 'skill_cooking', 'skill_baking',
            'other_skills',
            'technical_certification_document',
        ]


class ApplicantSkillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = ApplicantSkills
        fields = ['skill_name']


ApplicantSkillFormSet = forms.modelformset_factory(
    ApplicantSkills,
    form=ApplicantSkillForm,
    extra=1,
    can_delete=True
)


class ApplicantDocumentsForm(forms.ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = ['valid_id_type','applicant_id_picture_front', 'applicant_id_picture_back', 'certification_agree', 'resume_file', 'supporting_doc']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)
        
        


class ProfilePictureForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_widgets(self)

    class Meta:
        model = User
        fields = ['profile_picture']


class UpdateEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']


class UpdatePasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})


class UpdateUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        


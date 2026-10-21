from django import forms
from AdminSide.models import EmployerProfile, Jobs,User
from django.core.exceptions import ValidationError
from AdminSide.models import EmployerProfile, Jobs, JobSkills, User


class EmployerProfileForm(forms.ModelForm):

    def clean_tin_number(self):
        tin = self.cleaned_data.get('tin_number')

        if tin and not tin.isdigit():
            raise ValidationError(
                'TIN number must contain numbers only.'
            )

        return tin

    def clean_telephone_number(self):
        telephone = self.cleaned_data.get('telephone_number')

        if telephone and not telephone.isdigit():
            raise ValidationError(
                'Telephone number must contain numbers only.'
            )

        return telephone

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')

        if mobile and not mobile.isdigit():
            raise ValidationError(
                'Mobile number must contain numbers only.'
            )

        return mobile

    class Meta:
        model = EmployerProfile
        fields = [
            'business_name', 'trade_name', 'acronym', 'office_type',
            'tin_number', 'employer_type', 'total_workforce', 'line_of_business',
            'street_address', 'barangay', 'municipality', 'province',
            'owner_name', 'designation', 'contact_person', 'contact_position',
            'telephone_number', 'mobile_number', 'email',
            'certificate_of_registration', 'dti_sec_registration', 'business_permit',
            'public_doc_type', 'public_verification_document',
        ]



class JobsForm(forms.ModelForm):

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')

        if salary is not None and salary < 0:
            raise ValidationError(
                'Salary cannot be negative.'
            )

        return salary

    def clean_vacancy(self):
        vacancy = self.cleaned_data.get('vacancy')

        if vacancy is not None and vacancy < 1:
            raise ValidationError(
                'Vacancy must be at least 1.'
            )

        return vacancy

    def clean_work_experience_months(self):
        months = self.cleaned_data.get('work_experience_months')

        if months is not None and months < 0:
            raise ValidationError(
                'Work experience months cannot be negative.'
            )

        return months

    def clean_application_quota(self):
        quota = self.cleaned_data.get('application_quota')

        if quota is not None and quota < 1:
            raise ValidationError(
                'Application quota must be at least 1.'
            )

        return quota

    def clean_job_posting_expiry(self):
        expiry = self.cleaned_data.get('job_posting_expiry')

        if expiry:
            from django.utils import timezone

            if expiry < timezone.localdate():
                raise ValidationError(
                    'Job posting expiry cannot be in the past.'
                )

        return expiry

    class Meta:
        model = Jobs
        fields = [
            'job_title', 'job_description', 'nature_of_work', 'place_of_work',
            'salary', 'vacancy', 'work_experience_months', 'other_qualifications',
            'accepts_pwd', 'pwd_disabilities', 'accepts_ofw',
            'educational_level', 'course_or_strand', 'required_license',
            'required_eligibility', 'required_certification', 'languages_spoken',
            'application_quota', 'job_posting_expiry',
            # 21st Century Skills Required
            'skill_innovation', 'skill_team_work', 'skill_multitasking',
            'skill_work_ethics', 'skill_self_motivation', 'skill_creative_problem_solving',
            'skill_problem_solving', 'skill_critical_thinking', 'skill_decision_making',
            'skill_stress_tolerance', 'skill_planning_organizing', 'skill_social_perceptiveness',
            'skill_english_functional', 'skill_english_comprehension', 'skill_math_functional',
            # Technical Skills Required
            'skill_carpentry', 'skill_masonry', 'skill_welding',
            'skill_auto_mechanic', 'skill_plumbing', 'skill_driving',
            'skill_gardening', 'skill_tailoring', 'skill_photography',
            'skill_hairdressing', 'skill_cooking', 'skill_baking',
        ]


class JobSkillForm(forms.ModelForm):
    class Meta:
        model = JobSkills
        fields = ['skill_name']
        widgets = {
            'skill_name': forms.TextInput(attrs={
                'class': 'w-full border border-stone-200 bg-white text-stone-900 rounded-xl px-4 py-3 text-sm focus:border-stone-500 focus:outline-none transition',
                'placeholder': 'Enter specific skill or competency...'
            })
        }


JobSkillFormSet = forms.inlineformset_factory(
    Jobs,
    JobSkills,
    form=JobSkillForm,
    extra=1,
    can_delete=True
)


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture']
from django import forms
from AdminSide.models import EmployerProfile, Jobs, JobSkills, User


class EmployerProfileForm(forms.ModelForm):
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
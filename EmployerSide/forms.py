from django import forms
from AdminSide.models import EmployerProfile, Jobs


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
        ]

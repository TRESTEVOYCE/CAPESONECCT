from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin','Admin'),
        ('applicant','Applicant'),
        ('employer','Employer'),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='applicant')
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)


    def __str__(self):
        return f"{self.email} ({self.username}) - {self.role}"


class EmployerProfile(models.Model):

    COMPANY_TYPE_CHOICES = (
        ('private', 'Private'),
        ('government', 'Government'),
        ('non_profit', 'Non-Profit'),
        ('other', 'Other'),
    )

    VARIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )


    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length = 100)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, null=True, blank=True)
    business_permit = models.FileField(upload_to='business_permits/', null=True, blank=True)
    email = models.EmailField(unique=True) 
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    company_address = models.CharField(max_length=255, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VARIFICATION_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.user.email}"
    

class Jobs(models.Model):

    JOB_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=100)
    job_description = models.TextField()
    job_requirements = models.TextField()
    job_location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    vacancy = models.PositiveIntegerField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='jobs')
    time_posted = models.DateTimeField(auto_now_add=True)
    job_posting_expiry = models.DateTimeField()
    job_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_title} - {self.employer.company_name}"
    
class ApplicantProfile(models.Model):

    CIVIL_STATUS_CHOICES = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    )

    EDUCATIONAL_ATTACHMENT_CHOICES = (
        ('elementary', 'Elementary'),
        ('high_school', 'High School'),
        ('college', 'College'),
        ('university', 'University'),
        ('vocational', 'Vocational'),
        ('other', 'Other'),
    )

    APPLICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )




    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='applicant_profile')
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, null=True, blank=True)
    sex = models.CharField(max_length=10, null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    barangay = models.CharField(max_length=100, null=True, blank=True)
    municipality = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    curriculum_vitae = models.FileField(upload_to='curriculum_vitae/', null=True, blank=True)
    applicant_id_picture = models.ImageField(upload_to='applicant_id_pictures/', null=True, blank=True)
    education_level = models.CharField(max_length=100, choices=EDUCATIONAL_ATTACHMENT_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')
    skills = models.ManyToManyField('ApplicantSkills', blank=True, related_name='applicants')
    preferred_job = models.ManyToManyField(Jobs, blank=True, related_name='preferred_applicants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"
    
class ApplicantSkills(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)


class AppliedJobs(models.Model):

    APPLICATION_STATUS = (
        ('pending','Pending'),
        ('reviewed','Reviewed'),
        ('for interview','For Interview'),
        ('hired','Hired'),
        ('rejected','Rejected'),

    )
    uuid = models.UUIDField(default = uuid.uuid4, editable=False)
    applicant = models.ForeignKey(ApplicantProfile, on_delete=models.CASCADE, related_name='applied_jobs')
    applied_job = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name='applied_applicants')
    application_date = models.DateTimeField(auto_now_add=True)
    is_hired = models.BooleanField(default = False)
    status = models.CharField(max_length = 20, choices = APPLICATION_STATUS, default = 'pending')

class OfferedJobs(models.Model):

    APPLICATION_STATUS = (
        ('pending','Pending'),
        ('reviewed','Reviewed'),
        ('for interview','For Interview'),
        ('hired','Hired'),
        ('rejected','Rejected'),

    )

    uuid = models.UUIDField(default = uuid.uuid4, editable = False)
    applicant = models.ForeignKey(ApplicantProfile, on_delete = models.CASCADE, related_name = 'offered_jobs')
    offered_job = models.ForeignKey(Jobs, on_delete = models.CASCADE, related_name = 'offered_to_applicants')
    referred_by = models.CharField(max_length = 100, null = True, blank = True)
    date_offered = models.DateTimeField(auto_now_add = True)
    status = models.CharField(max_length = 20, choices = APPLICATION_STATUS, default = 'pending')
    remarks = models.TextField(null = True, blank = True)


    

from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin','Admin'),
        ('applicant','Applicant'),
        ('employer','Employer'),
        ('peso','PESO'),
        ('mswdo','MSWDO'),
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
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES)
    business_permit = models.FileField(upload_to='business_permits/' )
    email = models.EmailField(unique=True) 
    phone_number = models.CharField(max_length=20)
    company_address = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100)
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
    
class ApplicantSkills(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    skill_name = models.CharField(max_length=100)
    
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
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField()
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES)
    sex = models.CharField(max_length=10)
    contact_number = models.CharField(max_length=20)
    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    region = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    skills = models.ManyToManyField(ApplicantSkills, blank=True, related_name='applicants')
    resume = models.FileField(upload_to='resumes/')
    curriculum_vitae = models.FileField(upload_to='curriculum_vitae/')
    applicant_id_picture = models.ImageField(upload_to='applicant_id_pictures/')
    education_level = models.CharField(max_length=100, choices=EDUCATIONAL_ATTACHMENT_CHOICES)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')
    preferred_job = models.ManyToManyField(Jobs, blank=True, related_name='preferred_applicants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"


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


    def __str__(self):
        return f"{self.applicant} {self.offered_job}"
    

class SpecialProgramBeneficiaries(models.Model):

    SPECIAL_PROGRAM_CHOICES = (
        ('TUPAD','TUPAD'),
        ('Government_Internship_Program','government internship program'),
        ('Special_Program_For_Employment_Of_Students','special program for employment of students'),
        ('DisplacedInformalLaborProgram','DisplacedInformalLaborProgram'),

    )

    uuid = models.UUIDField(default=uuid.uuid4, editable =False)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    college_program = models.CharField(max_length=100)
    school_name = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100,)
    municipality = models.CharField(max_length=100,)
    province = models.CharField(max_length=100,)
    region = models.CharField(max_length=100,)
    zip_code = models.CharField(max_length=10,)
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2,)
    start_date = models.DateField()
    end_date = models.DateField()
    type_of_program = models.CharField(max_length=50,choices=SPECIAL_PROGRAM_CHOICES)
    is_done = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"
    
    

class PESOActivities(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable =False)
    activity_name = models.CharField(max_length=100)
    activity_description = models.TextField()
    number_of_participants = models.PositiveIntegerField()
    activity_date = models.DateField()
    activity_time = models.TimeField()
    activity_location = models.CharField(max_length=255)
    organizer = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_activities')

    def __str__(self):
        return f"{self.activity_name} - {self.activity_date}"
    
class AuditLog(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable =False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"
    
    
    




    

from datetime import date
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
    
    SECTOR_CHOICES = (
        ('BPO / IT', 'BPO / IT Services'),
        ('Finance', 'Finance and Insurance'),
        ('Administrative', 'Administrative & Support Services'),
        ('Hospitality', 'Hospitality / Tourism / Food Service'),
        ('Wholesale & Retail', 'Wholesale & Retail Trade (Sales)'),
        ('Logistics', 'Transportation and Storage'),
        ('Manufacturing', 'Manufacturing / Production'),
        ('Construction', 'Construction and Trades (SMAW, Engineering)'),
        ('Power & Energy', 'Electricity, Gas, and Water Supply'),
        ('Healthcare', 'Healthcare and Social Work'),
        ('Education', 'Education / Academic Institutions'),
        ('Public Sector', 'Government / Public Administration'),
        ('Agriculture', 'Agriculture, Forestry, and Fishing'),
    )

    STATUS_CHOICES = (
            ('Active', 'Active'),
            ('Pending', 'Pending'),
            ('Filled', 'Filled'),
            ('Closed', 'Closed'),
        )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    job_id_number = models.PositiveIntegerField(unique=True, null=True, blank=True)
    job_title = models.CharField(max_length=100)
    job_description = models.TextField()
    job_requirements = models.TextField()
    job_location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    vacancy = models.PositiveIntegerField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    time_posted = models.DateTimeField(auto_now_add=True)
    job_posting_expiry = models.DateTimeField()
    job_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def formatted_job_id(self):
        if self.job_id_number:
            return f"JP-{self.job_id_number:04d}"
        return "JP-NEW"

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
    
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='applicant_profile')
    applicant_sequence = models.IntegerField(unique=True, editable=False, null=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100) 
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES)
    phone_number = models.CharField(max_length=20)
    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    curriculum_vitae = models.FileField(upload_to='curriculum_vitae/', blank=True, null=True)
    applicant_id_picture = models.ImageField(upload_to='applicant_id_pictures/', blank=True, null=True)
    
    education_level = models.CharField(max_length=100, choices=EDUCATIONAL_ATTACHMENT_CHOICES)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')

    skills = models.ManyToManyField(ApplicantSkills, blank=True, related_name='applicants')
    preferred_job = models.ManyToManyField(Jobs, blank=True, related_name='preferred_applicants')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def formatted_id(self):
        """Returns the systematic string ID format padded with leading zeros (e.g., AP-0001)."""
        if self.applicant_sequence:
            # :04d ensures the number is always 4 digits wide, padding with zeros if necessary
            return f"AP-{self.applicant_sequence:04d}"
        return "AP-PENDING"

    def save(self, *args, **kwargs):
        """Overrides saving mechanisms to start sequencing at 1 instead of 1241."""
        if not self.applicant_sequence:
            max_id = ApplicantProfile.objects.aggregate(models.Max('applicant_sequence'))['applicant_sequence__max']
            # System initializes sequence values beginning at 1 instead of 1241
            self.applicant_sequence = (max_id + 1) if max_id else 1
        super().save(*args, **kwargs)

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

class Beneficiaries(models.Model):
    """
    Abstract base model containing fields shared by all program beneficiaries.
    Prevents database schema redundancy.
    """
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    # I edited the uuid because our primary key is the ID id is our reference to our app and uuid for API *Steve*
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=20)
    
    # Address details matching local configuration requirements
    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    
    # Employment tracking indicators requested by the Monitoring Report
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_done = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SpecialProgramForEmploymentOfStudents(Beneficiaries):
    """
    Maps to Report Section 2.1 (SPES Tracking).
    Includes educational subdivisions required by the dashboard breakdown.
    """
    SPES_EDUCATION_CHOICES = (
        ('elementary', 'Elementary'),
        ('juniors_hs', 'Junior High School'),
        ('senior_hs', 'Senior High School'),
        ('college', 'College'),
        ('tech_voc', 'Tech-Voc'),
    )
    
    education_level = models.CharField(max_length=20, choices=SPES_EDUCATION_CHOICES)
    is_out_of_school_youth = models.BooleanField(default=False) # Report field 2.1.1.2
    has_graduated = models.BooleanField(default=False)          # Report field 2.1.2
    has_nc_certification = models.BooleanField(default=False)   # Report field 2.1.3
    is_absorbed_by_employer = models.BooleanField(default=False)# Report field 2.1.4
    
    school_name = models.CharField(max_length=100, blank=True, null=True)
    college_program = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"[SPES] {self.first_name} {self.last_name}"

class GovernmentInternshipProgram(Beneficiaries):
    """
    Maps to Report Section 2.2 (GIP Tracking).
    """
    GIP_EDUCATION_CHOICES = (
        ('als', 'Alternative Learning System'),
        ('juniors_hs', 'Junior High School'),
        ('senior_hs', 'Senior High School'),
        ('tech_voc', 'Tech-Voc'),
        ('college', 'College'),
    )
    
    education_level = models.CharField(max_length=20, choices=GIP_EDUCATION_CHOICES)
    has_nc_certification = models.BooleanField(default=False)   # Report field 2.2.2
    is_absorbed_by_agency = models.BooleanField(default=False)  # Report field 2.2.3

    def __str__(self):
        return f"[GIP] {self.first_name} {self.last_name}"

class TupadBeneficiary(Beneficiaries):
    """
    Maps to Report Section 4.2 (TUPAD Emergency Employment Projects).
    """
    PROJECT_DURATION_CHOICES = (
        ('short', 'Short-term (10-30 days)'), # Report field 4.2.1.1
        ('long', 'Long-term (31-90 days)'),   # Report field 4.2.1.2
    )
    
    project_type = models.CharField(max_length=10, choices=PROJECT_DURATION_CHOICES, default='short')
    project_name = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"[TUPAD] {self.first_name} {self.last_name}"

class DisplacedInformalLaborProgram(Beneficiaries):
    """
    Maps to Report Section 4.1 (DILP Individual/Group Formation Projects).
    """
    DILP_PROJECT_CHOICES = (
        ('individual', 'Individual Project'),
        ('group', 'Group Project'),
    )
    
    CLASSIFICATION_CHOICES = (
        ('formation', 'Formation Project'),
        ('enhancement', 'Enhancement Project'),
        ('restoration', 'Restoration Project'),
    )
    
    project_category = models.CharField(max_length=15, choices=DILP_PROJECT_CHOICES, default='individual')
    project_classification = models.CharField(max_length=15, choices=CLASSIFICATION_CHOICES, default='formation')

    def __str__(self):
        return f"[DILP] {self.first_name} {self.last_name}"

class CareerGuidanceBeneficiary(Beneficiaries):
    """
    Tracks individuals receiving Career Guidance, Employment Coaching, 
    and Labor Market Information (LMI) services under PESO DOLE guidelines.
    Inherits core demographic, contact, and address fields from Beneficiaries.
    """
    PARTICIPANT_TYPE_CHOICES = (
        ('juniors_hs', 'Junior High School Student'),
        ('senior_hs', 'Senior High School Student'),
        ('college', 'College / University Student'),
        ('tech_voc', 'Tech-Voc Student'),
        ('osy', 'Out-of-School Youth (OSY)'),
        ('jobseeker', 'Unemployed / Jobseeker'),
    )

    ACTIVITY_TYPE_CHOICES = (
        ('orientation', 'Career Guidance & Advocacy Orientation'),
        ('coaching', 'Career / Employment Coaching Session'),
        ('lmi_briefing', 'Labor Market Information (LMI) Briefing'),
        ('pre_employment', 'Pre-Employment Seminar for Local Applicants (PESFA)'),
    )

    CURRICULUM_EXIT_CHOICES = (
        ('higher_ed', 'Higher Education'),
        ('employment', 'Employment / Job Seeking'),
        ('entrepreneurship', 'Entrepreneurship / Business'),
        ('skills_dev', 'Middle-Level Skills Development / Tech-Voc'),
        ('undecided', 'Undecided / Assessment Ongoing'),
    )

    participant_category = models.CharField(
        max_length=20, 
        choices=PARTICIPANT_TYPE_CHOICES, 
        default='senior_hs',
        help_text="Classification of the participant receiving guidance."
    )
    
    activity_type = models.CharField(
        max_length=20, 
        choices=ACTIVITY_TYPE_CHOICES, 
        default='orientation'
    )
    
    school_or_institution = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        help_text="Name of the school, university, or venue where the guidance session took place."
    )
    
    preferred_curriculum_exit = models.CharField(
        max_length=20, 
        choices=CURRICULUM_EXIT_CHOICES, 
        default='employment',
        help_text="Intended track or career exit chosen by the beneficiary after counseling."
    )
    
    conducted_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when the career guidance or coaching was provided."
    )
    
    has_received_lmi_materials = models.BooleanField(
        default=True,
        help_text="True if provided with official DOLE LMI flyers, career guidebooks, or digital kits."
    )

    class Meta:
        verbose_name = "Career Guidance Beneficiary"
        verbose_name_plural = "Career Guidance Beneficiaries"
        db_table = "peso_career_guidance_beneficiaries"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Career Guidance ({self.get_activity_type_display()})"

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

from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from JobMatchingEngine.database import *

class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('applicant', 'Applicant'),
        ('employer', 'Employer'),
        ('peso', 'PESO'),
        ('mswdo', 'MSWDO'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='applicant')
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.email} ({self.username}) - {self.role}"

class EmployerProfile(models.Model):
    OFFICE_TYPE_CHOICES = (
        ('main', 'Main Office'),
        ('branch', 'Branch'),
    )

    EMPLOYER_TYPE_CHOICES = (
        # Public
        ('nga', 'National Government Agency'),
        ('lgu', 'Local Government Unit'),
        ('gocc', 'Government-Owned and Controlled Corporation'),
        ('suc', 'State/Local University or College'),
        # Private
        ('direct_hire', 'Direct Hire'),
        ('local_agency', 'Local Recruitment Agency'),
        ('overseas_agency', 'Overseas Recruitment Agency'),
        ('do_174', 'D.O. 174 Contractor/Subcontractor'),
    )

    WORKFORCE_CHOICES = (
        ('micro', 'Micro (1-9)'),
        ('small', 'Small (10-99)'),
        ('medium', 'Medium (100-199)'),
        ('large', 'Large (200 and up)'),
    )

    VERIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='employer_profile'
    )

    # Establishment Details
    business_name = models.CharField(max_length=150)
    trade_name = models.CharField(max_length=150, blank=True, null=True)
    acronym = models.CharField(max_length=50, blank=True, null=True)
    office_type = models.CharField(max_length=10, choices=OFFICE_TYPE_CHOICES, default='main')
    tin_number = models.CharField(max_length=30, blank=True, null=True)
    employer_type = models.CharField(max_length=30, choices=EMPLOYER_TYPE_CHOICES, default='direct_hire')
    total_workforce = models.CharField(max_length=10, choices=WORKFORCE_CHOICES, default='micro')
    line_of_business = models.CharField(max_length=150, blank=True, null=True)

    # Address Breakdown
    street_address = models.CharField(max_length=255, blank=True, null=True)
    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)

    # Contact Details
    owner_name = models.CharField(max_length=150, blank=True, null=True)
    contact_person = models.CharField(max_length=100)
    contact_position = models.CharField(max_length=100, blank=True, null=True)
    telephone_number = models.CharField(max_length=20, blank=True, null=True)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    business_permit = models.FileField(upload_to='business_permits/', blank=True, null=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} - {self.email}"

class Jobs(models.Model):
    NATURE_OF_WORK_CHOICES = (
        ('permanent', 'Permanent'),
        ('contractual', 'Contractual'),
        ('project_based', 'Project-based'),
        ('internship', 'Internship / OJT'),
        ('part_time', 'Part-time'),
        ('wfh', 'Work from home / online job'),
    )

    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Filled', 'Filled'),
        ('Closed', 'Closed'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    employer = models.ForeignKey(
        EmployerProfile, 
        on_delete=models.CASCADE, 
        related_name='jobs', 
        limit_choices_to={'verification_status': 'verified'}
    )

    job_title = models.CharField(max_length=150)
    job_description = models.TextField()
    nature_of_work = models.CharField(max_length=20, choices=NATURE_OF_WORK_CHOICES, default='permanent')
    place_of_work = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    vacancy = models.PositiveIntegerField(default=1)

    work_experience_months = models.PositiveIntegerField(default=0, help_text="Experience in months")
    other_qualifications = models.TextField(blank=True, null=True)
    
    accepts_pwd = models.BooleanField(default=False)
    pwd_disabilities = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="e.g., Visual, Hearing, Speech, Physical, Mental"
    )
    accepts_ofw = models.BooleanField(default=False)

    educational_level = models.CharField(max_length=100, blank=True, null=True)
    course_or_strand = models.CharField(max_length=150, blank=True, null=True)
    required_license = models.CharField(max_length=150, blank=True, null=True)
    required_eligibility = models.CharField(max_length=150, blank=True, null=True)
    required_certification = models.CharField(max_length=150, blank=True, null=True)
    languages_spoken = models.CharField(max_length=255, blank=True, null=True)

    # Added default to prevent validation errors on missing POST fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    application_quota = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum allowed applicants before automatic closure.")
    
    posting_date = models.DateField(auto_now_add=True)
    job_posting_expiry = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def formatted_job_id(self):
        return f"JP-{self.id:04d}"

    def check_and_close(self):
        """
        Evaluates quota or expiry and automatically updates status to 'Closed'.
        """
        today = timezone.localdate()
        total_applications = self.applied_applicants.count()
        quota_reached = self.application_quota is not None and total_applications >= self.application_quota
        expired = self.job_posting_expiry and self.job_posting_expiry <= today

        if (quota_reached or expired) and self.status == 'Active':
            self.status = 'Closed'
            self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.job_title} - {self.employer.business_name}"

    # for the embedding vector storage in ChromaDB
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.status == 'Active':
            upsert_job_vector(self) # Pass the whole object!
        else:
            delete_job_vector(self.uuid)

    def delete(self, *args, **kwargs):
        delete_job_vector(self.uuid)
        super().delete(*args, **kwargs)

        
class ApplicantSkills(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
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

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='applicant_profile'
    )

    applicant_sequence = models.IntegerField(
        unique=True,
        editable=False,
        null=True
    )

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField()

    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES
    )

    civil_status = models.CharField(
        max_length=20,
        choices=CIVIL_STATUS_CHOICES
    )

    phone_number = models.CharField(max_length=20)

    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True
    )

    curriculum_vitae = models.FileField(
        upload_to='curriculum_vitae/',
        blank=True,
        null=True
    )

    applicant_id_picture = models.ImageField(
        upload_to='applicant_id_pictures/',
        blank=True,
        null=True
    )

    education_level = models.CharField(
        max_length=100,
        choices=EDUCATIONAL_ATTACHMENT_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default='pending'
    )

    skills = models.ManyToManyField(
        ApplicantSkills,
        blank=True,
        related_name='applicants'
    )

    preferred_job = models.ManyToManyField(
        Jobs,
        blank=True,
        related_name='preferred_applicants'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    @property
    def formatted_id(self):
        if self.applicant_sequence:
            return f"AP-{self.applicant_sequence:04d}"
        return "AP-PENDING"

    def save(self, *args, **kwargs):
        if not self.applicant_sequence:
            max_id = ApplicantProfile.objects.aggregate(
                models.Max('applicant_sequence')
            )['applicant_sequence__max']

            self.applicant_sequence = (max_id + 1) if max_id else 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"


class AppliedJobs(models.Model):

    APPLICATION_STATUS = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('for interview', 'For Interview'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    applicant = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name='applied_jobs'
    )

    applied_job = models.ForeignKey(
        Jobs,
        on_delete=models.CASCADE,
        related_name='applied_applicants'
    )

    application_date = models.DateTimeField(auto_now_add=True)
    is_hired = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default='pending'
    )


class OfferedJobs(models.Model):

    APPLICATION_STATUS = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('for interview', 'For Interview'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    applicant = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name='offered_jobs'
    )

    offered_job = models.ForeignKey(
        Jobs,
        on_delete=models.CASCADE,
        related_name='offered_to_applicants'
    )

    referred_by = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    date_offered = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default='pending'
    )

    remarks = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.applicant} {self.offered_job}"


# ============================================================
# BENEFICIARY PROGRAMS
# ============================================================

class Beneficiaries(models.Model):
    """
    Abstract base model containing fields shared by all
    program beneficiaries.
    """

    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    last_name = models.CharField(max_length=100)

    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES
    )

    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=20)

    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    daily_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    start_date = models.DateField()
    end_date = models.DateField()
    is_done = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SpecialProgramForEmploymentOfStudents(Beneficiaries):

    SPES_EDUCATION_CHOICES = (
        ('elementary', 'Elementary'),
        ('juniors_hs', 'Junior High School'),
        ('senior_hs', 'Senior High School'),
        ('college', 'College'),
        ('tech_voc', 'Tech-Voc'),
    )

    education_level = models.CharField(
        max_length=20,
        choices=SPES_EDUCATION_CHOICES
    )

    is_out_of_school_youth = models.BooleanField(default=False)
    has_graduated = models.BooleanField(default=False)
    has_nc_certification = models.BooleanField(default=False)
    is_absorbed_by_employer = models.BooleanField(default=False)

    school_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    college_program = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"[SPES] {self.first_name} {self.last_name}"


class GovernmentInternshipProgram(Beneficiaries):

    GIP_EDUCATION_CHOICES = (
        ('als', 'Alternative Learning System'),
        ('juniors_hs', 'Junior High School'),
        ('senior_hs', 'Senior High School'),
        ('tech_voc', 'Tech-Voc'),
        ('college', 'College'),
    )

    education_level = models.CharField(
        max_length=20,
        choices=GIP_EDUCATION_CHOICES
    )

    has_nc_certification = models.BooleanField(default=False)
    is_absorbed_by_agency = models.BooleanField(default=False)

    def __str__(self):
        return f"[GIP] {self.first_name} {self.last_name}"


class TupadBeneficiary(Beneficiaries):

    PROJECT_DURATION_CHOICES = (
        ('short', 'Short-term (10-30 days)'),
        ('long', 'Long-term (31-90 days)'),
    )

    project_type = models.CharField(
        max_length=10,
        choices=PROJECT_DURATION_CHOICES,
        default='short'
    )

    project_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"[TUPAD] {self.first_name} {self.last_name}"


class DisplacedInformalLaborProgram(Beneficiaries):

    DILP_PROJECT_CHOICES = (
        ('individual', 'Individual Project'),
        ('group', 'Group Project'),
    )

    CLASSIFICATION_CHOICES = (
        ('formation', 'Formation Project'),
        ('enhancement', 'Enhancement Project'),
        ('restoration', 'Restoration Project'),
    )

    project_category = models.CharField(
        max_length=15,
        choices=DILP_PROJECT_CHOICES,
        default='individual'
    )

    project_classification = models.CharField(
        max_length=15,
        choices=CLASSIFICATION_CHOICES,
        default='formation'
    )

    def __str__(self):
        return f"[DILP] {self.first_name} {self.last_name}"


class CareerGuidanceBeneficiary(Beneficiaries):

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
        return (
            f"{self.first_name} {self.last_name} - "
            f"Career Guidance ({self.get_activity_type_display()})"
        )


class PESOActivities(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    activity_name = models.CharField(max_length=100)
    activity_description = models.TextField()
    number_of_participants = models.PositiveIntegerField()
    activity_date = models.DateField()
    activity_time = models.TimeField()
    activity_location = models.CharField(max_length=255)
    organizer = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    added_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='added_activities'
    )

    def __str__(self):
        return f"{self.activity_name} - {self.activity_date}"


class AuditLog(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )

    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"
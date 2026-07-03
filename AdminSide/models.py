from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin','Admin'),
        ('applicant','Applicant'),
        ('employer','Employer'),
    )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='applicant')
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.email} ({self.username}) - {self.role}"

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




    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"
    
  


 

# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import AppliedJobs, EmployerProfile, Jobs
from .utils import send_notification, notify_admins

@receiver(post_save, sender=EmployerProfile)
def notify_admin_on_employer_registration(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            title="New Employer Registration",
            message=f"Employer '{instance.business_name}' has registered and requires verification.",
            notification_type='NEW_EMPLOYER',
            sender=instance.user,
            target_url=reverse(
                'AdminSide:employer_verification',
                kwargs={'uuid': instance.uuid},
            )
        )

@receiver(post_save, sender=Jobs)
def notify_admin_on_new_job_post(sender, instance, created, **kwargs):
    if created:
        notify_admins(
            title="New Job Post Submitted",
            message=f"'{instance.employer.business_name}' posted a new job: {instance.job_title}.",
            notification_type='NEW_JOB_POST',
            sender=instance.employer.user,
            target_url=reverse(
                'AdminSide:job_detail',
                kwargs={'job_uuid': instance.uuid},
            )
        )

@receiver(post_save, sender=AppliedJobs)
def notify_employer_on_new_applicant(sender, instance, created, **kwargs):
    if created and instance.applicant and instance.applied_job and instance.employer:
        applicant_name = f"{instance.applicant.first_name} {instance.applicant.last_name}"
        send_notification(
            recipient=instance.employer.user,
            sender=instance.applicant.user,
            title="New Job Applicant",
            message=f"{applicant_name} has applied for your job posting: {instance.applied_job.job_title}.",
            notification_type='NEW_APPLICANT',
            target_url="/employer/applicants/"
        )

@receiver(post_save, sender=AppliedJobs)
def notify_applicant_on_status_update(sender, instance, created, **kwargs):
    if not created:
        send_notification(
            recipient=instance.applicant.user,
            sender=instance.employer.user if instance.employer else None,
            title="Application Status Update",
            message=f"Your status for '{instance.applied_job.job_title}' has been updated to: {instance.get_status_display()}.",
            notification_type='APPLICATION_STATUS',
            target_url=f"/applicant/applications/{instance.uuid}/"
        )
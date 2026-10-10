import re

from django.db import migrations


EMPLOYER_TARGET = re.compile(r'^/admin/employers/([0-9a-fA-F-]+)/?$')
JOB_TARGET = re.compile(r'^/admin/jobs/([0-9a-fA-F-]+)/?$')


def repair_notification_target_urls(apps, schema_editor):
    Notification = apps.get_model('AdminSide', 'Notification')
    database = schema_editor.connection.alias

    for notification in Notification.objects.using(database).exclude(target_url__isnull=True).iterator():
        employer_match = EMPLOYER_TARGET.fullmatch(notification.target_url)
        if employer_match:
            notification.target_url = f'/admin-side/employers/{employer_match.group(1)}/verify/'
        else:
            job_match = JOB_TARGET.fullmatch(notification.target_url)
            if not job_match:
                continue
            notification.target_url = f'/admin-side/jobs/{job_match.group(1)}/'

        notification.save(using=database, update_fields=['target_url'])


def reverse_repaired_notification_target_urls(apps, schema_editor):
    Notification = apps.get_model('AdminSide', 'Notification')
    database = schema_editor.connection.alias

    for notification in Notification.objects.using(database).exclude(target_url__isnull=True).iterator():
        employer_match = re.fullmatch(
            r'^/admin-side/employers/([0-9a-fA-F-]+)/verify/?$',
            notification.target_url,
        )
        if employer_match:
            notification.target_url = f'/admin/employers/{employer_match.group(1)}/'
        else:
            job_match = re.fullmatch(
                r'^/admin-side/jobs/([0-9a-fA-F-]+)/?$',
                notification.target_url,
            )
            if not job_match:
                continue
            notification.target_url = f'/admin/jobs/{job_match.group(1)}/'

        notification.save(using=database, update_fields=['target_url'])


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0006_alter_applicantprofile_civil_status_default'),
    ]

    operations = [
        migrations.RunPython(
            repair_notification_target_urls,
            reverse_repaired_notification_target_urls,
        ),
    ]

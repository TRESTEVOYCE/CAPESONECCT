from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0003_cloudinary_upload_folders'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('VERIFICATION_APPROVED', 'Verification Approved'),
                    ('VERIFICATION_REJECTED', 'Verification Rejected'),
                    ('APPLICATION_STATUS', 'Application Status Update'),
                    ('NEW_REGISTRATION', 'New Registration Pending Verification'),
                    ('RESUBMISSION', 'Account Re-submitted for Verification'),
                    ('NEW_APPLICANT', 'New Applicant'),
                    ('NEW_EMPLOYER', 'New Employer'),
                    ('NEW_JOB_POST', 'New Job Post'),
                    ('APPEAL_REVERIFICATION', 'Appeal for Reverification'),
                ],
                max_length=50,
            ),
        ),
    ]

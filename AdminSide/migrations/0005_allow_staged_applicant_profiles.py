from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0004_notification_event_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicantprofile',
            name='civil_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('single', 'Single'),
                    ('married', 'Married'),
                    ('divorced', 'Divorced'),
                    ('widowed', 'Widowed'),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='education_level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('elementary', 'Elementary'),
                    ('high_school', 'High School'),
                    ('college', 'College'),
                    ('university', 'University'),
                    ('vocational', 'Vocational'),
                    ('other', 'Other'),
                ],
                max_length=100,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='barangay',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='municipality',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='province',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

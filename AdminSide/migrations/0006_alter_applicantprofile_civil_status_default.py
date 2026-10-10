from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0005_allow_staged_applicant_profiles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicantprofile',
            name='civil_status',
            field=models.CharField(
                blank=True,
                choices=[('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')],
                default='single',
                max_length=20,
                null=True,
            ),
        ),
    ]

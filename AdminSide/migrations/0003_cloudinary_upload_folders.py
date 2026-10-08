import cloudinary_storage.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0002_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicantprofile',
            name='applicant_id_picture',
            field=models.ImageField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.MediaCloudinaryStorage(),
                upload_to='applicant_docs/id_pictures/',
            ),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='curriculum_vitae',
            field=models.FileField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='applicant_docs/curriculum_vitae/',
            ),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='resume',
            field=models.FileField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='applicant_docs/resumes/',
            ),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='resume_file',
            field=models.FileField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='applicant_docs/resumes/',
            ),
        ),
        migrations.AlterField(
            model_name='applicantprofile',
            name='supporting_doc',
            field=models.FileField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='applicant_docs/supporting_docs/',
            ),
        ),
        migrations.AlterField(
            model_name='employerprofile',
            name='business_permit',
            field=models.FileField(
                blank=True,
                help_text='Photocopy of Latest Business Permit',
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='employer_docs/private_sector/business_permits/',
            ),
        ),
        migrations.AlterField(
            model_name='employerprofile',
            name='certificate_of_registration',
            field=models.FileField(
                blank=True,
                help_text='Photocopy of COR 2303',
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='employer_docs/private_sector/cor_2303/',
            ),
        ),
        migrations.AlterField(
            model_name='employerprofile',
            name='dti_sec_registration',
            field=models.FileField(
                blank=True,
                help_text='Photocopy of DTI or SEC Registration',
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='employer_docs/private_sector/dti_sec/',
            ),
        ),
        migrations.AlterField(
            model_name='employerprofile',
            name='public_verification_document',
            field=models.FileField(
                blank=True,
                help_text='Uploaded verification document for public agency',
                null=True,
                storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(),
                upload_to='employer_docs/public_sector/verification_documents/',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.MediaCloudinaryStorage(),
                upload_to='profile_pictures/',
            ),
        ),
    ]

import cloudinary_storage.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0008_alter_user_managers'),
    ]

    operations = [
        migrations.RenameField(
            model_name='applicantprofile',
            old_name='applicant_id_picture',
            new_name='applicant_id_picture_front',
        ),
        migrations.AddField(
            model_name='applicantprofile',
            name='applicant_id_picture_back',
            field=models.ImageField(
                blank=True,
                null=True,
                storage=cloudinary_storage.storage.MediaCloudinaryStorage(),
                upload_to='applicant_docs/id_pictures/',
            ),
        ),
    ]

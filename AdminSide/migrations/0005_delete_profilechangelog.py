from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0002_alter_profilechangelog_options_and_more'),
        ('AdminSide', '0004_remove_applicantprofile_technical_certification_document_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProfileChangeLog',
        ),
    ]

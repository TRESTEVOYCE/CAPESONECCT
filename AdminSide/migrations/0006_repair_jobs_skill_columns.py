from django.db import migrations


def add_missing_job_skill_columns(apps, schema_editor):
    Jobs = apps.get_model('AdminSide', 'Jobs')
    table_name = Jobs._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    for field in Jobs._meta.local_fields:
        if field.name.startswith('skill_') and field.column not in existing_columns:
            schema_editor.add_field(Jobs, field)


class Migration(migrations.Migration):

    dependencies = [
        ('AdminSide', '0005_delete_profilechangelog'),
    ]

    operations = [
        migrations.RunPython(
            add_missing_job_skill_columns,
            migrations.RunPython.noop,
        ),
    ]

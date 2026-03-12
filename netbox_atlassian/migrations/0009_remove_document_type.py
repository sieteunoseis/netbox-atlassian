from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0008_cab_single_table"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="documenttemplate",
            name="document_type",
        ),
        migrations.AlterModelOptions(
            name="documenttemplate",
            options={
                "ordering": ["name"],
                "verbose_name": "Document Template",
                "verbose_name_plural": "Document Templates",
            },
        ),
    ]

import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0002_rename_model"),
        ("extras", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=200, unique=True)),
                (
                    "document_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("mop", "MOP"),
                            ("sow", "SOW"),
                            ("cab", "CAB"),
                        ],
                        verbose_name="Document Type",
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("content", models.TextField()),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "verbose_name": "Document Template",
                "verbose_name_plural": "Document Templates",
                "ordering": ["document_type", "name"],
            },
        ),
    ]

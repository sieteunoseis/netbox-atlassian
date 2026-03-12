"""Add confluence_parent_page_id and confluence_space_key to DocumentTemplate."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0011_fix_checkbox_syntax"),
    ]

    operations = [
        migrations.AddField(
            model_name="documenttemplate",
            name="confluence_parent_page_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="If set, generated documents can be posted as child pages under this Confluence page.",
                max_length=20,
                verbose_name="Confluence Parent Page ID",
            ),
        ),
        migrations.AddField(
            model_name="documenttemplate",
            name="confluence_space_key",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Confluence space key (e.g. 'Netv'). Required when parent page ID is set.",
                max_length=50,
                verbose_name="Confluence Space Key",
            ),
        ),
    ]

"""Replace [placeholder] with (placeholder) in all sample templates to avoid Confluence link interpretation."""

import re

from django.db import migrations


def fix_brackets(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    for t in DocumentTemplate.objects.filter(
        name__in=["Standard Network Change MOP", "Standard Statement of Work", "Standard CAB Request"]
    ):
        # Replace [text] placeholders with (text) but preserve * [ ] checkbox syntax
        fixed = re.sub(r"\[(?! \])", "(", t.content)
        fixed = re.sub(r"(?<!\* \( )\]", ")", fixed)
        # Restore any * ( ) that should be * [ ] checkboxes
        fixed = fixed.replace("* ( )", "* [ ]")
        t.content = fixed
        t.save()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0006_conditional_device_fields"),
    ]

    operations = [
        migrations.RunPython(fix_brackets, reverse_code=migrations.RunPython.noop),
    ]

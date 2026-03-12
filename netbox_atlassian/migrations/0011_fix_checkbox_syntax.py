"""Fix broken checkbox syntax: [ ) -> [ ] caused by migration 0007 bracket replacement."""

from django.db import migrations


def fix_checkboxes(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    for t in DocumentTemplate.objects.all():
        if "[ )" in t.content:
            t.content = t.content.replace("[ )", "[ ]")
            t.save()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0010_additional_templates"),
    ]

    operations = [
        migrations.RunPython(fix_checkboxes, reverse_code=migrations.RunPython.noop),
    ]

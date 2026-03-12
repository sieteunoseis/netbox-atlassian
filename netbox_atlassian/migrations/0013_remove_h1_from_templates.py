"""Remove h1. title lines from templates — Confluence uses the page title instead."""

import re

from django.db import migrations


def remove_h1_lines(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    for t in DocumentTemplate.objects.all():
        # Remove lines that start with "h1. " (and any trailing blank lines)
        fixed = re.sub(r"^h1\..*\n*", "", t.content, count=1)
        if fixed != t.content:
            t.content = fixed
            t.save()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0012_confluence_parent_page"),
    ]

    operations = [
        migrations.RunPython(remove_h1_lines, reverse_code=migrations.RunPython.noop),
    ]

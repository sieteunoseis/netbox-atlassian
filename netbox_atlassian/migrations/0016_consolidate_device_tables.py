"""Consolidate per-device tables into a single table in MOP templates."""

import re

from django.db import migrations

# Old pattern: per-device h3 + detail table + interfaces table
OLD_DEVICES_PATTERN = re.compile(
    r"h2\. (?:\d+\. )?Affected Devices\s*\n"
    r"(.*?)"
    r"(?=\n----|\nh2\.)",
    re.DOTALL,
)

NEW_DEVICES_SECTION = """\
h2. 3. Affected Devices

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}
"""


def consolidate_device_tables(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")

    # Only update templates that have per-device h3 headings in the Affected Devices section
    for t in DocumentTemplate.objects.all():
        match = OLD_DEVICES_PATTERN.search(t.content)
        if not match:
            continue
        section_body = match.group(1)
        # Check if this section uses per-device h3 headings (the old pattern)
        if "h3. {{ device.name }}" not in section_body and "h3. {{device.name}}" not in section_body:
            continue

        # Replace the entire Affected Devices section
        new_content = OLD_DEVICES_PATTERN.sub(NEW_DEVICES_SECTION, t.content, count=1)
        if new_content != t.content:
            t.content = new_content
            t.save()


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0015_update_cab_template"),
    ]

    operations = [
        migrations.RunPython(
            consolidate_device_tables, reverse_code=migrations.RunPython.noop
        ),
    ]

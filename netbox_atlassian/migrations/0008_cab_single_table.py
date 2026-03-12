"""Update CAB template: collapse per-device tables into one summary table."""

from django.db import migrations

OLD_SYSTEMS = """\
h2. 3. Affected Systems

{% for device in devices %}
|| Field || Value ||
| Device | {{ device.name }} |
| Site | {{ device.site.name }} |
| Role | {{ device.role.name }} |
{% if device.device_type %}| Model | {{ device.device_type.manufacturer.name }} {{ device.device_type.model }} |
{% endif %}| Primary IP | {{ device.primary_ip4|default:"N/A" }} |

{% endfor %}"""

NEW_SYSTEMS = """\
h2. 3. Affected Systems

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}"""


def fix_cab_table(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    try:
        t = DocumentTemplate.objects.get(name="Standard CAB Request")
        t.content = t.content.replace(OLD_SYSTEMS, NEW_SYSTEMS)
        t.save()
    except DocumentTemplate.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0007_fix_bracket_placeholders"),
    ]

    operations = [
        migrations.RunPython(fix_cab_table, reverse_code=migrations.RunPython.noop),
    ]

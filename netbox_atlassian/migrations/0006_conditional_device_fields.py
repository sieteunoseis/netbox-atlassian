"""Update MOP sample template to use {% if %} guards on optional fields (serial, rack, etc.)."""

from django.db import migrations

OLD_DEVICE_TABLE = """\
|| Field || Value ||
| Site | {{ device.site.name }} |
| Role | {{ device.role.name }} |
| Manufacturer | {{ device.device_type.manufacturer.name }} |
| Model | {{ device.device_type.model }} |
| Serial Number | {{ device.serial|default:"N/A" }} |
| Asset Tag | {{ device.asset_tag|default:"N/A" }} |
| Primary IP | {{ device.primary_ip4|default:"N/A" }} |
| Rack | {{ device.rack|default:"N/A" }} |"""

NEW_DEVICE_TABLE = """\
|| Field || Value ||
| Site | {{ device.site.name }} |
| Role | {{ device.role.name }} |
{% if device.device_type %}| Manufacturer | {{ device.device_type.manufacturer.name }} |
| Model | {{ device.device_type.model }} |
{% endif %}{% if device.cluster %}| Cluster | {{ device.cluster.name }} |
{% endif %}{% if device.serial %}| Serial Number | {{ device.serial }} |
{% endif %}{% if device.asset_tag %}| Asset Tag | {{ device.asset_tag }} |
{% endif %}| Primary IP | {{ device.primary_ip4|default:"N/A" }} |
{% if device.rack %}| Rack | {{ device.rack }} |
{% endif %}"""


def apply_conditional_fields(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    try:
        t = DocumentTemplate.objects.get(name="Standard Network Change MOP")
        t.content = t.content.replace(OLD_DEVICE_TABLE, NEW_DEVICE_TABLE)
        t.save()
    except DocumentTemplate.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0005_fix_contacts_dedup"),
    ]

    operations = [
        migrations.RunPython(apply_conditional_fields, reverse_code=migrations.RunPython.noop),
    ]

"""Add filtered interfaces and connected devices sections to Standard Network Change MOP."""

from django.db import migrations

OLD_SECTION = """\
h2. 3. Affected Devices

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}

----"""

NEW_SECTION = """\
h2. 3. Affected Devices

|| Device || Site || Role || Model || Primary IP ||
{% for device in devices %}| {{ device.name }} | {{ device.site.name }} | {{ device.role.name }} | {% if device.device_type %}{{ device.device_type.manufacturer.name }} {{ device.device_type.model }}{% endif %} | {{ device.primary_ip4|default:"N/A" }} |
{% endfor %}
{% for device in devices %}{% if device.active_interfaces %}
h3. {{ device.name }} — Interfaces

|| Interface || Description || IP Address(es) ||
{% for iface in device.active_interfaces %}| {{ iface.name }} | {{ iface.description|default:"" }} | {% for ip in iface.ip_addresses.all %}{{ ip.address }} {% endfor %} |
{% endfor %}{% endif %}{% if device.connected_devices %}
h3. {{ device.name }} — Connected Devices

|| Local Interface || Remote Device || Remote Interface ||
{% for conn in device.connected_devices %}{% for link in conn.connections %}| {{ link.local_interface }} | {{ conn.device.name }} | {{ link.remote_interface }} |
{% endfor %}{% endfor %}{% endif %}{% endfor %}

----"""


def update_template(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    try:
        t = DocumentTemplate.objects.get(name="MOP - Standard Network Change")
        if OLD_SECTION in t.content:
            t.content = t.content.replace(OLD_SECTION, NEW_SECTION)
            t.save()
    except DocumentTemplate.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0016_consolidate_device_tables"),
    ]

    operations = [
        migrations.RunPython(update_template, reverse_code=migrations.RunPython.noop),
    ]

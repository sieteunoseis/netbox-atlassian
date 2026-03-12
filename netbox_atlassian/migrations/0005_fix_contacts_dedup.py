"""Fix MOP sample template to use unique_contacts instead of per-device contact loop."""

from django.db import migrations

OLD_CONTACTS_BLOCK = """\
|| Role || Name || Contact || Responsibility ||
{% for device in devices %}{% for c in device.contacts.all %}| {{ c.role.name|default:"[Role]" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} | [Responsibility] |
{% endfor %}{% endfor %}"""

NEW_CONTACTS_BLOCK = """\
|| Role || Name || Contact || Responsibility ||
{% for c in unique_contacts %}| {{ c.role.name|default:"[Role]" }} | {{ c.contact.name }} | {{ c.contact.phone|default:"N/A" }} | [Responsibility] |
{% endfor %}"""


def fix_mop_template(apps, schema_editor):
    DocumentTemplate = apps.get_model("netbox_atlassian", "DocumentTemplate")
    try:
        t = DocumentTemplate.objects.get(name="Standard Network Change MOP")
        t.content = t.content.replace(OLD_CONTACTS_BLOCK, NEW_CONTACTS_BLOCK)
        t.save()
    except DocumentTemplate.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0004_sample_templates"),
    ]

    operations = [
        migrations.RunPython(fix_mop_template, reverse_code=migrations.RunPython.noop),
    ]

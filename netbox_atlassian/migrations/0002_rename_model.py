from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_atlassian", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="AtlassianPermission",
            new_name="Atlassian",
        ),
    ]

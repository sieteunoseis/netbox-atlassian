from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AtlassianPermission",
            fields=[],
            options={
                "managed": False,
                "default_permissions": (),
                "permissions": (
                    ("configure_atlassian", "Can configure Atlassian plugin settings"),
                ),
            },
        ),
    ]

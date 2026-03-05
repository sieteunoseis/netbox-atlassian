from django.db import models


class Atlassian(models.Model):
    """Unmanaged model to register custom permissions for the Atlassian plugin."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("configure_atlassian", "Can configure Atlassian plugin settings"),
        )

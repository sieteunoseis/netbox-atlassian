from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel


class Atlassian(models.Model):
    """Unmanaged model to register custom permissions for the Atlassian plugin."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("configure_atlassian", "Can configure Atlassian plugin settings"),
        )


class DocumentTypeChoices(models.TextChoices):
    MOP = "mop", "MOP"
    SOW = "sow", "SOW"
    CAB = "cab", "CAB"


class DocumentTemplate(NetBoxModel):
    """A reusable document template (MOP, SOW, CAB) rendered with NetBox device data."""

    name = models.CharField(max_length=200, unique=True)
    document_type = models.CharField(
        max_length=20,
        choices=DocumentTypeChoices.choices,
        verbose_name="Document Type",
    )
    description = models.TextField(blank=True)
    content = models.TextField(
        help_text=(
            "Template using Django template syntax. "
            "Device variables: {{ device.name }}, {{ device.site.name }}, {{ device.serial }}, "
            "{{ device.role.name }}, {{ device.primary_ip4 }}, {{ device.contacts.all }}. "
            "Loop: {% for device in devices %}...{% endfor %}. "
            "Extra variables passed at generation time are also available."
        )
    )

    class Meta:
        ordering = ["document_type", "name"]
        verbose_name = "Document Template"
        verbose_name_plural = "Document Templates"

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_atlassian:template_detail", kwargs={"pk": self.pk})

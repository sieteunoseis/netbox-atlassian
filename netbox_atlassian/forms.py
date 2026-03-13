"""
Forms for NetBox Atlassian Plugin
"""

from dcim.models import Device
from django import forms
from extras.models import Tag
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import DynamicModelMultipleChoiceField
from virtualization.models import VirtualMachine

from .models import DocumentTemplate


class AtlassianSettingsForm(forms.Form):
    """Form for displaying and validating Atlassian settings."""

    # Jira settings
    jira_url = forms.URLField(
        required=False,
        label="Jira URL",
        help_text="On-premise Jira server URL (e.g., https://jira.example.com)",
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://jira.example.com"}),
    )
    jira_username = forms.CharField(
        required=False,
        label="Jira Username",
        help_text="Username for Jira authentication",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    jira_password = forms.CharField(
        required=False,
        label="Jira Password/Token",
        help_text="Password or API token for Jira authentication",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    jira_verify_ssl = forms.BooleanField(
        required=False,
        initial=True,
        label="Verify Jira SSL",
        help_text="Verify SSL certificate for Jira connection",
    )

    # Confluence settings
    confluence_url = forms.URLField(
        required=False,
        label="Confluence URL",
        help_text="On-premise Confluence server URL (e.g., https://confluence.example.com)",
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://confluence.example.com"}),
    )
    confluence_username = forms.CharField(
        required=False,
        label="Confluence Username",
        help_text="Username for Confluence authentication",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    confluence_password = forms.CharField(
        required=False,
        label="Confluence Password/Token",
        help_text="Password or API token for Confluence authentication",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    confluence_verify_ssl = forms.BooleanField(
        required=False,
        initial=True,
        label="Verify Confluence SSL",
        help_text="Verify SSL certificate for Confluence connection",
    )

    # Search settings
    jira_max_results = forms.IntegerField(
        required=False,
        initial=10,
        min_value=1,
        max_value=100,
        label="Jira Max Results",
        help_text="Maximum number of Jira issues to display",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    confluence_max_results = forms.IntegerField(
        required=False,
        initial=10,
        min_value=1,
        max_value=100,
        label="Confluence Max Results",
        help_text="Maximum number of Confluence pages to display",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    # General settings
    timeout = forms.IntegerField(
        required=False,
        initial=30,
        min_value=5,
        max_value=120,
        label="Timeout",
        help_text="API timeout in seconds",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    cache_timeout = forms.IntegerField(
        required=False,
        initial=300,
        min_value=0,
        max_value=3600,
        label="Cache Timeout",
        help_text="Cache timeout in seconds (0 to disable caching)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class DocumentTemplateForm(NetBoxModelForm):
    """Form for creating and editing document templates."""

    content = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control font-monospace", "rows": 25}),
        help_text=(
            "Template using Django syntax. Device variables: {{ device.name }}, {{ device.site.name }}, "
            "{{ device.serial }}, {{ device.role.name }}, {{ device.primary_ip4 }}, "
            "{{ device.device_type.manufacturer.name }}, {{ device.device_type.model }}. "
            "Contacts: {% for c in device.contacts.all %}{{ c.contact.name }}{% endfor %}. "
            "Interfaces: {% for iface in device.interfaces.all %}{{ iface.name }}{% endfor %}. "
            "Loop devices: {% for device in devices %}...{% endfor %}. "
            "Extra vars (from generate form): {{ title }}, {{ change_request }}, {{ change_window }}, etc."
        ),
    )

    confluence_parent_page_id = forms.CharField(
        required=False,
        label="Parent Page ID",
        help_text="Confluence page ID for the parent page. Generated documents will be created as child pages. Enables the 'Post to Confluence' button.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Page ID"}),
    )
    confluence_space_key = forms.CharField(
        required=False,
        label="Space Key",
        help_text="Confluence space key. Required when parent page ID is set.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Space key"}),
    )

    class Meta:
        model = DocumentTemplate
        fields = ("name", "description", "content", "confluence_space_key", "confluence_parent_page_id", "tags")


class DocumentGenerateForm(forms.Form):
    """Form for selecting devices/VMs and extra variables to generate a document."""

    tag = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        label="Filter by Tag",
        help_text="Select a tag to filter available devices and VMs",
    )
    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Devices",
        help_text="Select one or more NetBox devices to populate the template",
        query_params={"tag_id": "$tag"},
    )
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        label="Virtual Machines",
        help_text="Select one or more virtual machines to include",
        query_params={"tag_id": "$tag"},
    )
    extra_vars = forms.CharField(
        required=False,
        label="Extra Variables",
        help_text=(
            "Additional template variables, one per line in key=value format. "
            "Example: change_request=ITSUP-1234, mop_author=John Smith, change_window=24FEB2026 2200"
        ),
        widget=forms.Textarea(attrs={"rows": 6, "style": "resize:none;", "placeholder": "change_request=ITSUP-1234\nmop_author=John Smith\nchange_window=24FEB2026 2200\napproved_by=Jane Doe\nexpected_duration=30 minutes\nimpact_level=Medium\nrollback_time=15 minutes"}),
    )

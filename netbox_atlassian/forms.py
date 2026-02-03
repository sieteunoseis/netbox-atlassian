"""
Forms for NetBox Atlassian Plugin
"""

from django import forms


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

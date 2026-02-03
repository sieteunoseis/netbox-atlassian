"""
NetBox Atlassian Plugin

Display Jira issues and Confluence pages related to devices in NetBox.
Searches by configurable fields (hostname, serial, role, etc.) with OR logic.
"""

from netbox.plugins import PluginConfig

__version__ = "0.2.1"


class AtlassianConfig(PluginConfig):
    """Plugin configuration for NetBox Atlassian integration."""

    name = "netbox_atlassian"
    verbose_name = "Atlassian"
    description = "Display Jira issues and Confluence pages related to devices"
    version = __version__
    author = "sieteunoseis"
    author_email = "sieteunoseis@github.com"
    base_url = "atlassian"
    min_version = "4.0.0"

    # Required settings - plugin won't load without these
    required_settings = []

    # Default configuration values
    default_settings = {
        # Jira settings (on-prem)
        "jira_url": "",  # e.g., "https://jira.example.com"
        "jira_username": "",
        "jira_password": "",  # or API token
        "jira_token": "",  # Personal Access Token (PAT) - preferred for on-prem
        "jira_verify_ssl": True,
        # Confluence settings (on-prem)
        "confluence_url": "",  # e.g., "https://confluence.example.com"
        "confluence_username": "",
        "confluence_password": "",  # or API token
        "confluence_token": "",  # Personal Access Token (PAT) - preferred for on-prem
        "confluence_verify_ssl": True,
        # Cloud settings (for future use)
        "use_cloud": False,
        "cloud_api_token": "",
        "cloud_email": "",
        # Search configuration
        # Fields to search - values are device attribute paths
        # Searches use OR logic - matches any field
        "search_fields": [
            {"name": "Hostname", "attribute": "name", "enabled": True},
            {"name": "Serial", "attribute": "serial", "enabled": True},
            {"name": "Asset Tag", "attribute": "asset_tag", "enabled": False},
            {"name": "Role", "attribute": "role.name", "enabled": False},
            {"name": "Primary IP", "attribute": "primary_ip4.address", "enabled": False},
        ],
        # Jira search settings
        "jira_max_results": 10,
        "jira_projects": [],  # Empty = search all projects
        "jira_issue_types": [],  # Empty = all types
        # Confluence search settings
        "confluence_max_results": 10,
        "confluence_spaces": [],  # Empty = search all spaces
        # General settings
        "timeout": 30,
        "cache_timeout": 300,  # Cache results for 5 minutes
        # Enable legacy SSL renegotiation for older servers (required for OHSU wiki)
        "enable_legacy_ssl": False,
        # Device type filtering (like catalyst-center)
        # Empty list = show tab for all devices
        "device_types": [],  # e.g., ["cisco", "juniper"]
    }


config = AtlassianConfig

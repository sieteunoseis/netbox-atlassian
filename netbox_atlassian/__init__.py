"""
NetBox Atlassian Plugin

Display Jira issues and Confluence pages related to devices in NetBox.
Searches by configurable fields (hostname, serial, role, etc.) with OR logic.
"""

import logging

from netbox.plugins import PluginConfig

__version__ = "0.2.8"

logger = logging.getLogger(__name__)


class AtlassianConfig(PluginConfig):
    """Plugin configuration for NetBox Atlassian integration."""

    name = "netbox_atlassian"
    verbose_name = "NetBox Atlassian"
    description = "Display Jira issues and Confluence pages related to devices"
    version = __version__
    author = "Jeremy Worden"
    author_email = "jeremy.worden@gmail.com"
    base_url = "atlassian"
    min_version = "4.0.0"
    max_version = "5.99"

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
        # Endpoint search fields (for netbox-endpoints plugin)
        # Searches use OR logic - matches any field
        "endpoint_search_fields": [
            {"name": "Name", "attribute": "name", "enabled": True},
            {"name": "MAC Address", "attribute": "mac_address", "enabled": True},
            {"name": "Serial", "attribute": "serial", "enabled": True},
            {"name": "Asset Tag", "attribute": "asset_tag", "enabled": False},
        ],
        # Jira search settings
        "jira_max_results": 10,
        "jira_projects": [],  # Empty = search all projects
        "jira_issue_types": [],  # Empty = all types
        # Search mode: "title_only", "strict", "full_text"
        # - title_only: Only search/match in issue summary/key
        # - strict: Search all content but only show results with verified title/summary match
        # - full_text: Show all results including body-only matches
        "jira_search_mode": "strict",
        # Confluence search settings
        "confluence_max_results": 10,
        "confluence_spaces": [],  # Empty = search all spaces
        # Search mode: "title_only", "strict", "full_text"
        # - title_only: Only search in page titles (CQL: title ~)
        # - strict: Search all content but only show results with verified title/breadcrumb match
        # - full_text: Show all results including body-only matches
        "confluence_search_mode": "strict",
        # Match mode: "exact" or "partial"
        # - exact: Require whole word match (e.g., "ABC123" won't match "ABC1234")
        # - partial: Allow substring match (e.g., "ABC" matches "ABC123")
        "match_mode": "exact",
        # General settings
        "timeout": 30,
        "cache_timeout": 300,  # Cache results for 5 minutes
        # Enable legacy SSL renegotiation for older servers (required for OHSU wiki)
        "enable_legacy_ssl": False,
        # Device type filtering (like catalyst-center)
        # Empty list = show tab for all devices
        "device_types": [],  # e.g., ["cisco", "juniper"]
    }

    def ready(self):
        """Register endpoint view if netbox_endpoints is available."""
        super().ready()
        self._register_endpoint_views()

    def _register_endpoint_views(self):
        """Register Atlassian tab for Endpoints if plugin is installed."""
        import sys

        # Quick check if netbox_endpoints is available
        if "netbox_endpoints" not in sys.modules:
            try:
                import importlib.util

                if importlib.util.find_spec("netbox_endpoints") is None:
                    logger.debug("netbox_endpoints not installed, skipping endpoint view registration")
                    return
            except Exception:
                logger.debug("netbox_endpoints not available, skipping endpoint view registration")
                return

        try:
            from django.shortcuts import render
            from netbox.views import generic
            from netbox_endpoints.models import Endpoint
            from utilities.views import ViewTab, register_model_view

            from .views import should_show_atlassian_tab_endpoint

            @register_model_view(Endpoint, name="atlassian", path="atlassian")
            class EndpointAtlassianView(generic.ObjectView):
                """Display Jira issues and Confluence pages for an Endpoint."""

                queryset = Endpoint.objects.all()
                template_name = "netbox_atlassian/endpoint_tab.html"

                tab = ViewTab(
                    label="Atlassian",
                    weight=9000,
                    permission="netbox_endpoints.view_endpoint",
                    hide_if_empty=False,
                    visible=should_show_atlassian_tab_endpoint,
                )

                def get(self, request, pk):
                    endpoint = Endpoint.objects.get(pk=pk)
                    return render(
                        request,
                        self.template_name,
                        {
                            "object": endpoint,
                            "tab": self.tab,
                            "loading": True,
                        },
                    )

            logger.info("Registered Atlassian tab for Endpoint model")
        except ImportError:
            logger.debug("netbox_endpoints not installed, skipping endpoint view registration")
        except Exception as e:
            logger.warning(f"Could not register endpoint views: {e}")


config = AtlassianConfig

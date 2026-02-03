"""
Views for NetBox Atlassian Plugin

Registers custom tabs on Device detail views to show Jira issues and Confluence pages.
Provides settings configuration UI.
"""

import re

from dcim.models import Device
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from virtualization.models import VirtualMachine

from .atlassian_client import get_client
from .forms import AtlassianSettingsForm


def get_device_attribute(device, attribute_path: str):
    """
    Get a device attribute by dot-separated path.

    Args:
        device: Device instance
        attribute_path: Dot-separated attribute path (e.g., "role.name", "primary_ip4.address")

    Returns:
        Attribute value or None if not found
    """
    try:
        value = device
        for part in attribute_path.split("."):
            value = getattr(value, part, None)
            if value is None:
                return None
        # Convert to string for IP addresses
        if hasattr(value, "ip"):
            return str(value.ip)
        return str(value) if value else None
    except Exception:
        return None


def get_search_terms(device) -> list[str]:
    """
    Get search terms from device based on configured search fields.

    Returns list of non-empty values from enabled search fields.
    For comma-separated values (like multiple serial numbers), splits into individual terms.
    """
    config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
    search_fields = config.get("search_fields", [])

    terms = []
    for field in search_fields:
        if not field.get("enabled", True):
            continue

        attribute = field.get("attribute", "")
        if not attribute:
            continue

        value = get_device_attribute(device, attribute)
        if value and value.strip():
            # Split comma-separated values (e.g., multiple serial numbers)
            if "," in value:
                for part in value.split(","):
                    part = part.strip()
                    if part and part not in terms:
                        terms.append(part)
            else:
                if value.strip() not in terms:
                    terms.append(value.strip())

    return terms


def should_show_atlassian_tab(device) -> bool:
    """
    Determine if the Atlassian tab should be visible for this device.

    Shows tab if:
    - Device has at least one searchable field value
    - Device type matches configured filters (if any)
    """
    config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
    device_types = config.get("device_types", [])

    # Check device type filter if configured
    if device_types and device.device_type:
        manufacturer_slug = device.device_type.manufacturer.slug.lower() if device.device_type.manufacturer else ""
        manufacturer_name = device.device_type.manufacturer.name.lower() if device.device_type.manufacturer else ""

        matches = False
        for pattern in device_types:
            try:
                if re.search(pattern.lower(), manufacturer_slug) or re.search(pattern.lower(), manufacturer_name):
                    matches = True
                    break
            except re.error:
                if pattern.lower() in manufacturer_slug or pattern.lower() in manufacturer_name:
                    matches = True
                    break

        if not matches:
            return False

    # Check if we have any search terms
    terms = get_search_terms(device)
    return len(terms) > 0


@register_model_view(Device, name="atlassian", path="atlassian")
class DeviceAtlassianView(generic.ObjectView):
    """Display Jira issues and Confluence pages for a Device with async loading."""

    queryset = Device.objects.all()
    template_name = "netbox_atlassian/device_tab.html"

    tab = ViewTab(
        label="Atlassian",
        weight=9100,
        permission="dcim.view_device",
        hide_if_empty=False,
    )

    def get(self, request, pk):
        """Render initial tab with loading spinner - content loads via htmx."""
        device = Device.objects.get(pk=pk)
        return render(
            request,
            self.template_name,
            {
                "object": device,
                "tab": self.tab,
                "loading": True,
            },
        )


class DeviceAtlassianContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX endpoint that returns Atlassian content for async loading."""

    permission_required = "dcim.view_device"

    def get(self, request, pk):
        """Fetch Atlassian data and return HTML content."""
        device = Device.objects.get(pk=pk)

        config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
        client = get_client()

        # Get search terms from device
        search_terms = get_search_terms(device)

        # Get configured search fields for display
        search_fields = config.get("search_fields", [])
        enabled_fields = [f for f in search_fields if f.get("enabled", True)]

        # Search Jira and Confluence
        jira_results = {"issues": [], "total": 0, "error": None}
        confluence_results = {"pages": [], "total": 0, "error": None}

        if search_terms:
            jira_max = config.get("jira_max_results", 10)
            confluence_max = config.get("confluence_max_results", 10)

            jira_results = client.search_jira(search_terms, max_results=jira_max)
            confluence_results = client.search_confluence(search_terms, max_results=confluence_max)

        # Get URLs for external links
        jira_url = config.get("jira_url", "").rstrip("/")
        confluence_url = config.get("confluence_url", "").rstrip("/")

        return HttpResponse(
            render_to_string(
                "netbox_atlassian/tab_content.html",
                {
                    "object": device,
                    "search_terms": search_terms,
                    "enabled_fields": enabled_fields,
                    "jira_results": jira_results,
                    "confluence_results": confluence_results,
                    "jira_url": jira_url,
                    "confluence_url": confluence_url,
                    "jira_configured": bool(jira_url),
                    "confluence_configured": bool(confluence_url),
                },
                request=request,
            )
        )


@register_model_view(VirtualMachine, name="atlassian", path="atlassian")
class VirtualMachineAtlassianView(generic.ObjectView):
    """Display Jira issues and Confluence pages for a VirtualMachine with async loading."""

    queryset = VirtualMachine.objects.all()
    template_name = "netbox_atlassian/vm_tab.html"

    tab = ViewTab(
        label="Atlassian",
        weight=9100,
        permission="virtualization.view_virtualmachine",
        hide_if_empty=False,
    )

    def get(self, request, pk):
        """Render initial tab with loading spinner - content loads via htmx."""
        vm = VirtualMachine.objects.get(pk=pk)
        return render(
            request,
            self.template_name,
            {
                "object": vm,
                "tab": self.tab,
                "loading": True,
            },
        )


class VMAtlassianContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX endpoint that returns Atlassian content for VM async loading."""

    permission_required = "virtualization.view_virtualmachine"

    def get(self, request, pk):
        """Fetch Atlassian data and return HTML content."""
        vm = VirtualMachine.objects.get(pk=pk)

        config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
        client = get_client()

        # For VMs, search by name and primary IP
        search_terms = []
        if vm.name:
            search_terms.append(vm.name)
        if vm.primary_ip4:
            search_terms.append(str(vm.primary_ip4.address.ip))

        # Get configured search fields for display
        enabled_fields = [{"name": "Name", "attribute": "name", "enabled": True}]
        if vm.primary_ip4:
            enabled_fields.append({"name": "Primary IP", "attribute": "primary_ip4", "enabled": True})

        # Search Jira and Confluence
        jira_results = {"issues": [], "total": 0, "error": None}
        confluence_results = {"pages": [], "total": 0, "error": None}

        if search_terms:
            jira_max = config.get("jira_max_results", 10)
            confluence_max = config.get("confluence_max_results", 10)

            jira_results = client.search_jira(search_terms, max_results=jira_max)
            confluence_results = client.search_confluence(search_terms, max_results=confluence_max)

        # Get URLs for external links
        jira_url = config.get("jira_url", "").rstrip("/")
        confluence_url = config.get("confluence_url", "").rstrip("/")

        return HttpResponse(
            render_to_string(
                "netbox_atlassian/tab_content.html",
                {
                    "object": vm,
                    "search_terms": search_terms,
                    "enabled_fields": enabled_fields,
                    "jira_results": jira_results,
                    "confluence_results": confluence_results,
                    "jira_url": jira_url,
                    "confluence_url": confluence_url,
                    "jira_configured": bool(jira_url),
                    "confluence_configured": bool(confluence_url),
                },
                request=request,
            )
        )


class AtlassianSettingsView(View):
    """View for configuring Atlassian plugin settings."""

    template_name = "netbox_atlassian/settings.html"

    def get_current_config(self):
        """Get current plugin configuration."""
        return settings.PLUGINS_CONFIG.get("netbox_atlassian", {})

    def get(self, request):
        """Display the settings form."""
        config = self.get_current_config()
        form = AtlassianSettingsForm(initial=config)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "config": config,
            },
        )

    def post(self, request):
        """Handle settings form submission."""
        form = AtlassianSettingsForm(request.POST)

        if form.is_valid():
            messages.warning(
                request,
                "Settings must be configured in NetBox's configuration.py file. "
                "See the README for configuration instructions.",
            )
        else:
            messages.error(request, "Invalid settings provided.")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "config": self.get_current_config(),
            },
        )


class TestJiraConnectionView(View):
    """Test connection to Jira API."""

    def post(self, request):
        """Test the Jira connection and return result."""
        client = get_client()
        success, message = client.test_jira_connection()

        if success:
            return JsonResponse({"success": True, "message": message})
        return JsonResponse({"success": False, "error": message}, status=400)


class TestConfluenceConnectionView(View):
    """Test connection to Confluence API."""

    def post(self, request):
        """Test the Confluence connection and return result."""
        client = get_client()
        success, message = client.test_confluence_connection()

        if success:
            return JsonResponse({"success": True, "message": message})
        return JsonResponse({"success": False, "error": message}, status=400)

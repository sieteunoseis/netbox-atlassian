"""
Views for NetBox Atlassian Plugin

Registers custom tabs on Device detail views to show Jira issues and Confluence pages.
Provides settings configuration UI.
Provides Document Library for generating MOP/SOW/CAB documents from NetBox device data.
"""

import datetime
import re

from dcim.models import Device
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, Template
from django.template.loader import render_to_string
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from virtualization.models import VirtualMachine

from .atlassian_client import get_client
from .forms import AtlassianSettingsForm, DocumentGenerateForm, DocumentTemplateForm
from .models import DocumentTemplate

# Check if netbox_endpoints plugin is installed
try:
    from netbox_endpoints.models import Endpoint

    ENDPOINTS_PLUGIN_INSTALLED = True
except ImportError:
    ENDPOINTS_PLUGIN_INSTALLED = False


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
    terms_with_fields = get_search_terms_with_fields(device)
    return list(terms_with_fields.keys())


def get_search_terms_with_fields(device) -> dict[str, str]:
    """
    Get search terms from device with their source field names.

    Returns dict mapping term -> field_name (e.g., {"server01": "Hostname", "ABC123": "Serial"})
    For comma-separated values, each part maps to the same field name.
    """
    config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
    search_fields = config.get("search_fields", [])

    terms = {}  # term -> field_name
    for field in search_fields:
        if not field.get("enabled", True):
            continue

        attribute = field.get("attribute", "")
        field_name = field.get("name", attribute)
        if not attribute:
            continue

        value = get_device_attribute(device, attribute)
        if value and value.strip():
            # Split comma-separated values (e.g., multiple serial numbers)
            if "," in value:
                for part in value.split(","):
                    part = part.strip()
                    if part and part not in terms:
                        terms[part] = field_name
            else:
                if value.strip() not in terms:
                    terms[value.strip()] = field_name

    return terms


def get_tag_slugs(obj) -> list[str]:
    """
    Get tag slugs from a device, VM, or endpoint for label-based search.

    Excludes generic tags (environment, role) configured in tag_search_exclude.
    """
    config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
    if not config.get("search_by_tags", True):
        return []

    exclude = set(config.get("tag_search_exclude", []))

    try:
        return [tag.slug for tag in obj.tags.all() if tag.slug not in exclude]
    except Exception:
        return []


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
        weight=9000,
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

        # Get search terms with their source field names
        terms_with_fields = get_search_terms_with_fields(device)
        search_terms = list(terms_with_fields.keys())

        # Get tag slugs for label-based search
        tag_slugs = get_tag_slugs(device)

        # Get configured search fields for display
        search_fields = config.get("search_fields", [])
        enabled_fields = [f for f in search_fields if f.get("enabled", True)]

        # Search Jira and Confluence
        jira_results = {"issues": [], "total": 0, "error": None}
        confluence_results = {"pages": [], "total": 0, "error": None}

        if search_terms or tag_slugs:
            jira_max = config.get("jira_max_results", 10)
            confluence_max = config.get("confluence_max_results", 10)

            jira_results = client.search_jira(search_terms, terms_with_fields, max_results=jira_max, tag_slugs=tag_slugs)
            confluence_results = client.search_confluence(search_terms, terms_with_fields, max_results=confluence_max, tag_slugs=tag_slugs)

        # Get URLs for external links
        jira_url = config.get("jira_url", "").rstrip("/")
        confluence_url = config.get("confluence_url", "").rstrip("/")

        return HttpResponse(
            render_to_string(
                "netbox_atlassian/tab_content.html",
                {
                    "object": device,
                    "search_terms": search_terms,
                    "tag_slugs": tag_slugs,
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
        weight=9000,
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

        # For VMs, search by name and primary IP with field mapping
        terms_with_fields = {}
        if vm.name:
            terms_with_fields[vm.name] = "Name"
        if vm.primary_ip4:
            terms_with_fields[str(vm.primary_ip4.address.ip)] = "Primary IP"

        search_terms = list(terms_with_fields.keys())

        # Get tag slugs for label-based search
        tag_slugs = get_tag_slugs(vm)

        # Get configured search fields for display
        enabled_fields = [{"name": "Name", "attribute": "name", "enabled": True}]
        if vm.primary_ip4:
            enabled_fields.append({"name": "Primary IP", "attribute": "primary_ip4", "enabled": True})

        # Search Jira and Confluence
        jira_results = {"issues": [], "total": 0, "error": None}
        confluence_results = {"pages": [], "total": 0, "error": None}

        if search_terms or tag_slugs:
            jira_max = config.get("jira_max_results", 10)
            confluence_max = config.get("confluence_max_results", 10)

            jira_results = client.search_jira(search_terms, terms_with_fields, max_results=jira_max, tag_slugs=tag_slugs)
            confluence_results = client.search_confluence(search_terms, terms_with_fields, max_results=confluence_max, tag_slugs=tag_slugs)

        # Get URLs for external links
        jira_url = config.get("jira_url", "").rstrip("/")
        confluence_url = config.get("confluence_url", "").rstrip("/")

        return HttpResponse(
            render_to_string(
                "netbox_atlassian/tab_content.html",
                {
                    "object": vm,
                    "search_terms": search_terms,
                    "tag_slugs": tag_slugs,
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


class AtlassianSettingsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for configuring Atlassian plugin settings."""

    permission_required = "netbox_atlassian.configure_atlassian"
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


# Endpoint-specific functions for netbox_endpoints plugin
def get_endpoint_attribute(endpoint, attribute_path: str):
    """
    Get an endpoint attribute by dot-separated path.

    Args:
        endpoint: Endpoint instance
        attribute_path: Dot-separated attribute path (e.g., "name", "mac_address")

    Returns:
        Attribute value or None if not found
    """
    try:
        value = endpoint
        for part in attribute_path.split("."):
            value = getattr(value, part, None)
            if value is None:
                return None
        # Convert to string for IP addresses and MAC
        if hasattr(value, "ip"):
            return str(value.ip)
        return str(value) if value else None
    except Exception:
        return None


def get_endpoint_search_terms(endpoint) -> list[str]:
    """
    Get search terms from endpoint based on configured endpoint_search_fields.

    Returns list of non-empty values from enabled search fields.
    """
    terms_with_fields = get_endpoint_search_terms_with_fields(endpoint)
    return list(terms_with_fields.keys())


def get_endpoint_search_terms_with_fields(endpoint) -> dict[str, str]:
    """
    Get search terms from endpoint with their source field names.

    Returns dict mapping term -> field_name.
    """
    config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
    search_fields = config.get(
        "endpoint_search_fields",
        [
            {"name": "Name", "attribute": "name", "enabled": True},
            {"name": "MAC Address", "attribute": "mac_address", "enabled": True},
            {"name": "Serial", "attribute": "serial", "enabled": True},
        ],
    )

    terms = {}  # term -> field_name
    for field in search_fields:
        if not field.get("enabled", True):
            continue

        attribute = field.get("attribute", "")
        field_name = field.get("name", attribute)
        if not attribute:
            continue

        value = get_endpoint_attribute(endpoint, attribute)
        if value and value.strip():
            # Split comma-separated values
            if "," in value:
                for part in value.split(","):
                    part = part.strip()
                    if part and part not in terms:
                        terms[part] = field_name
            else:
                if value.strip() not in terms:
                    terms[value.strip()] = field_name

    return terms


def should_show_atlassian_tab_endpoint(endpoint) -> bool:
    """
    Determine if the Atlassian tab should be visible for this endpoint.

    Shows tab if endpoint has at least one searchable field value.
    """
    if not ENDPOINTS_PLUGIN_INSTALLED:
        return False

    terms = get_endpoint_search_terms(endpoint)
    return len(terms) > 0


# Endpoint views - only available if netbox_endpoints is installed
if ENDPOINTS_PLUGIN_INSTALLED:

    class EndpointAtlassianContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
        """HTMX endpoint that returns Atlassian content for Endpoint async loading."""

        permission_required = "netbox_endpoints.view_endpoint"

        def get(self, request, pk):
            """Fetch Atlassian data and return HTML content."""
            endpoint = Endpoint.objects.get(pk=pk)

            config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})
            client = get_client()

            # Get search terms with their source field names
            terms_with_fields = get_endpoint_search_terms_with_fields(endpoint)
            search_terms = list(terms_with_fields.keys())

            # Get tag slugs for label-based search
            tag_slugs = get_tag_slugs(endpoint)

            # Get configured search fields for display
            search_fields = config.get(
                "endpoint_search_fields",
                [
                    {"name": "Name", "attribute": "name", "enabled": True},
                    {"name": "MAC Address", "attribute": "mac_address", "enabled": True},
                    {"name": "Serial", "attribute": "serial", "enabled": True},
                ],
            )
            enabled_fields = [f for f in search_fields if f.get("enabled", True)]

            # Search Jira and Confluence
            jira_results = {"issues": [], "total": 0, "error": None}
            confluence_results = {"pages": [], "total": 0, "error": None}

            if search_terms or tag_slugs:
                jira_max = config.get("jira_max_results", 10)
                confluence_max = config.get("confluence_max_results", 10)

                jira_results = client.search_jira(search_terms, terms_with_fields, max_results=jira_max, tag_slugs=tag_slugs)
                confluence_results = client.search_confluence(
                    search_terms, terms_with_fields, max_results=confluence_max, tag_slugs=tag_slugs
                )

            # Get URLs for external links
            jira_url = config.get("jira_url", "").rstrip("/")
            confluence_url = config.get("confluence_url", "").rstrip("/")

            return HttpResponse(
                render_to_string(
                    "netbox_atlassian/tab_content.html",
                    {
                        "object": endpoint,
                        "search_terms": search_terms,
                        "tag_slugs": tag_slugs,
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


# ---------------------------------------------------------------------------
# Document Library Views
# ---------------------------------------------------------------------------

DOCUMENT_TYPE_ICONS = {
    "mop": "mdi-clipboard-list-outline",
    "sow": "mdi-file-document-outline",
    "cab": "mdi-calendar-check-outline",
}

DOCUMENT_TYPE_COLORS = {
    "mop": "primary",
    "sow": "success",
    "cab": "warning",
}


class DocumentTemplateListView(LoginRequiredMixin, View):
    """Browse all document templates grouped by type."""

    def get(self, request):
        templates = DocumentTemplate.objects.all()

        grouped = {}
        for t in templates:
            grouped.setdefault(t.document_type, []).append(t)

        type_labels = dict(DocumentTemplate.document_type.field.choices)

        groups = []
        for dtype in ["mop", "sow", "cab"]:
            if dtype in grouped:
                groups.append(
                    {
                        "type": dtype,
                        "label": type_labels.get(dtype, dtype.upper()),
                        "icon": DOCUMENT_TYPE_ICONS.get(dtype, "mdi-file-outline"),
                        "color": DOCUMENT_TYPE_COLORS.get(dtype, "secondary"),
                        "templates": grouped[dtype],
                    }
                )

        return render(
            request,
            "netbox_atlassian/template_list.html",
            {
                "groups": groups,
                "total": templates.count(),
            },
        )


class DocumentTemplateDetailView(LoginRequiredMixin, View):
    """Show a single document template with option to generate."""

    def get(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        return render(
            request,
            "netbox_atlassian/template_detail.html",
            {
                "object": template,
                "icon": DOCUMENT_TYPE_ICONS.get(template.document_type, "mdi-file-outline"),
                "color": DOCUMENT_TYPE_COLORS.get(template.document_type, "secondary"),
            },
        )


class DocumentTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Create a new document template."""

    permission_required = "netbox_atlassian.add_documenttemplate"

    def get(self, request):
        form = DocumentTemplateForm()
        return render(
            request,
            "netbox_atlassian/template_edit.html",
            {"form": form, "object": None},
        )

    def post(self, request):
        form = DocumentTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Template '{template.name}' created.")
            return redirect(template.get_absolute_url())
        return render(
            request,
            "netbox_atlassian/template_edit.html",
            {"form": form, "object": None},
        )


class DocumentTemplateEditView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Edit an existing document template."""

    permission_required = "netbox_atlassian.change_documenttemplate"

    def get(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        form = DocumentTemplateForm(instance=template)
        return render(
            request,
            "netbox_atlassian/template_edit.html",
            {"form": form, "object": template},
        )

    def post(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        form = DocumentTemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()
            messages.success(request, f"Template '{template.name}' updated.")
            return redirect(template.get_absolute_url())
        return render(
            request,
            "netbox_atlassian/template_edit.html",
            {"form": form, "object": template},
        )


class DocumentTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Delete a document template."""

    permission_required = "netbox_atlassian.delete_documenttemplate"

    def get(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        return render(
            request,
            "netbox_atlassian/template_delete.html",
            {"object": template},
        )

    def post(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        name = template.name
        template.delete()
        messages.success(request, f"Template '{name}' deleted.")
        return redirect("plugins:netbox_atlassian:template_list")


def _parse_extra_vars(raw: str) -> dict:
    """Parse key=value lines from the extra_vars textarea into a dict."""
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


class DocumentGenerateView(LoginRequiredMixin, View):
    """Select devices and extra variables, then render a template."""

    def get(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        form = DocumentGenerateForm()
        return render(
            request,
            "netbox_atlassian/template_generate.html",
            {
                "object": template,
                "form": form,
                "rendered": None,
                "icon": DOCUMENT_TYPE_ICONS.get(template.document_type, "mdi-file-outline"),
                "color": DOCUMENT_TYPE_COLORS.get(template.document_type, "secondary"),
            },
        )

    def post(self, request, pk):
        template = get_object_or_404(DocumentTemplate, pk=pk)
        form = DocumentGenerateForm(request.POST)
        rendered = None
        error = None

        if form.is_valid():
            device_ids = form.cleaned_data.get("devices") or []
            vm_ids = form.cleaned_data.get("virtual_machines") or []
            extra_vars = _parse_extra_vars(form.cleaned_data.get("extra_vars") or "")

            devices = list(Device.objects.filter(pk__in=[d.pk for d in device_ids]).prefetch_related(
                "site", "role", "device_type__manufacturer", "interfaces__ip_addresses", "contacts__contact", "contacts__role"
            ))
            vms = list(VirtualMachine.objects.filter(pk__in=[v.pk for v in vm_ids]).prefetch_related(
                "site", "role", "cluster", "interfaces__ip_addresses", "contacts__contact", "contacts__role"
            ))

            # Combined list — templates use {% for device in devices %} for both
            all_objects = devices + vms

            # Deduplicate contacts across all selected objects by contact ID
            seen_contact_ids = set()
            unique_contacts = []
            for obj in all_objects:
                for assignment in obj.contacts.all():
                    if assignment.contact_id not in seen_contact_ids:
                        seen_contact_ids.add(assignment.contact_id)
                        unique_contacts.append(assignment)

            context = {
                "devices": all_objects,
                "device": all_objects[0] if all_objects else None,
                "unique_contacts": unique_contacts,
                "date": datetime.date.today().strftime("%d%b%Y").upper(),
                "generated_by": request.user.get_full_name() or request.user.username,
            }
            context.update(extra_vars)

            try:
                django_template = Template("{% autoescape off %}" + template.content + "{% endautoescape %}")
                rendered = django_template.render(Context(context))
            except Exception as e:
                error = str(e)

        return render(
            request,
            "netbox_atlassian/template_generate.html",
            {
                "object": template,
                "form": form,
                "rendered": rendered,
                "error": error,
                "icon": DOCUMENT_TYPE_ICONS.get(template.document_type, "mdi-file-outline"),
                "color": DOCUMENT_TYPE_COLORS.get(template.document_type, "secondary"),
            },
        )

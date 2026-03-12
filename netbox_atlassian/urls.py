"""
URL patterns for NetBox Atlassian Plugin
"""

from django.urls import path

from .views import (
    ENDPOINTS_PLUGIN_INSTALLED,
    AtlassianSettingsView,
    DeviceAtlassianContentView,
    DocumentGenerateView,
    DocumentTemplateCreateView,
    DocumentTemplateDeleteView,
    DocumentTemplateDetailView,
    DocumentTemplateEditView,
    DocumentTemplateListView,
    TestConfluenceConnectionView,
    TestJiraConnectionView,
    VMAtlassianContentView,
)

urlpatterns = [
    # Settings
    path("settings/", AtlassianSettingsView.as_view(), name="settings"),
    path("test-jira/", TestJiraConnectionView.as_view(), name="test_jira"),
    path("test-confluence/", TestConfluenceConnectionView.as_view(), name="test_confluence"),
    # Device/VM HTMX content
    path("device/<int:pk>/content/", DeviceAtlassianContentView.as_view(), name="device_content"),
    path("vm/<int:pk>/content/", VMAtlassianContentView.as_view(), name="vm_content"),
    # Document Library
    path("library/", DocumentTemplateListView.as_view(), name="template_list"),
    path("library/add/", DocumentTemplateCreateView.as_view(), name="template_add"),
    path("library/<int:pk>/", DocumentTemplateDetailView.as_view(), name="template_detail"),
    path("library/<int:pk>/edit/", DocumentTemplateEditView.as_view(), name="template_edit"),
    path("library/<int:pk>/delete/", DocumentTemplateDeleteView.as_view(), name="template_delete"),
    path("library/<int:pk>/generate/", DocumentGenerateView.as_view(), name="template_generate"),
]

# Add endpoint URLs if netbox_endpoints is installed
if ENDPOINTS_PLUGIN_INSTALLED:
    from .views import EndpointAtlassianContentView

    urlpatterns.append(
        path("endpoint/<int:pk>/content/", EndpointAtlassianContentView.as_view(), name="endpoint_content"),
    )

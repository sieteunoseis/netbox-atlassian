"""
URL patterns for NetBox Atlassian Plugin
"""

from django.urls import path

from .views import (
    AtlassianSettingsView,
    DeviceAtlassianContentView,
    TestConfluenceConnectionView,
    TestJiraConnectionView,
    VMAtlassianContentView,
)

urlpatterns = [
    path("settings/", AtlassianSettingsView.as_view(), name="settings"),
    path("test-jira/", TestJiraConnectionView.as_view(), name="test_jira"),
    path("test-confluence/", TestConfluenceConnectionView.as_view(), name="test_confluence"),
    path("device/<int:pk>/content/", DeviceAtlassianContentView.as_view(), name="device_content"),
    path("vm/<int:pk>/content/", VMAtlassianContentView.as_view(), name="vm_content"),
]

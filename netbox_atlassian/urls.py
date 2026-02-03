"""
URL patterns for NetBox Atlassian Plugin
"""

from django.urls import path

from .views import (
    AtlassianSettingsView,
    TestConfluenceConnectionView,
    TestJiraConnectionView,
)

urlpatterns = [
    path("settings/", AtlassianSettingsView.as_view(), name="settings"),
    path("test-jira/", TestJiraConnectionView.as_view(), name="test_jira"),
    path("test-confluence/", TestConfluenceConnectionView.as_view(), name="test_confluence"),
]

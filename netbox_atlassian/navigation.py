"""
Navigation menu items for NetBox Atlassian Plugin
"""

from django.conf import settings
from netbox.plugins import PluginMenu, PluginMenuItem

_menu = PluginMenu(
    label="Atlassian",
    groups=(
        (
            "Document Library",
            (
                PluginMenuItem(
                    link="plugins:netbox_atlassian:template_list",
                    link_text="Browse Templates",
                    permissions=["netbox_atlassian.view_documenttemplate"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_atlassian:template_add",
                    link_text="Add Template",
                    permissions=["netbox_atlassian.add_documenttemplate"],
                ),
            ),
        ),
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_atlassian:settings",
                    link_text="Configuration",
                    permissions=["netbox_atlassian.configure_atlassian"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-jira",
)


# top_level_menu=False puts this plugin's items under the shared "Plugins" menu
# (grouped by plugin name) instead of its own top-level sidebar menu.
if settings.PLUGINS_CONFIG.get("netbox_atlassian", {}).get("top_level_menu", True):
    menu = _menu
else:
    menu_items = tuple(item for group in _menu.groups for item in group.items)

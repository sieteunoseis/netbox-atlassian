"""
Navigation menu items for NetBox Atlassian Plugin
"""

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Atlassian",
    groups=(
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_atlassian:settings",
                    link_text="Configuration",
                    permissions=["dcim.view_device"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-jira",
)

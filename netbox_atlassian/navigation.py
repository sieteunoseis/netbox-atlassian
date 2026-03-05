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
                    permissions=["netbox_atlassian.configure_atlassian"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-jira",
)

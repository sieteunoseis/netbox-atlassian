"""
Navigation menu items for NetBox Atlassian Plugin
"""

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
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

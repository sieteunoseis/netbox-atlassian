# Document Library Template Examples

These `.confluence` files are example templates for the Document Library feature. They use [Django template syntax](https://docs.djangoproject.com/en/5.0/ref/templates/language/) and output [Confluence wiki markup](https://confluence.atlassian.com/doc/confluence-wiki-markup-251003035.html).

## Available Templates

| File | Description |
|------|-------------|
| `mop-network-change.confluence` | Standard MOP for network device changes |
| `mop-upgrade-with-phases.confluence` | Multi-phase upgrade MOP with closeout sections |
| `mop-maintenance-reset.confluence` | Quick maintenance reset/reboot schedule |
| `mop-firmware-upgrade.confluence` | Firmware upgrade procedure per device |
| `mop-decommission.confluence` | Device/system decommission plan |
| `sow-project.confluence` | Statement of work for project scoping |
| `cab-change-request.confluence` | Change Advisory Board request with risk assessment |
| `rca-root-cause-analysis.confluence` | Root cause analysis for incidents |
| `lessons-learned.confluence` | Lessons learned review for projects and incidents |

## How to Use

1. Go to **Atlassian > Document Library > Add Template** in NetBox
2. Copy the content of any `.confluence` file into the template editor
3. Give it a name, description, and tags
4. Save and use **Generate** to populate it with real device data

## Template Variables

### Auto-populated
- `{{ devices }}` — list of selected devices and VMs
- `{{ device }}` — first selected device (for single-device templates)
- `{{ unique_contacts }}` — all deduplicated contacts across all selected devices
- `{{ team_contacts }}` — internal team only (excludes roles listed in `vendor_contact_roles` setting)
- `{{ vendor_contacts }}` — contacts whose role slug is in `vendor_contact_roles` setting
- `{{ management_contacts }}` — contacts from groups listed in `management_contact_groups` setting (included regardless of device assignments)
- `{{ date }}` — current date (e.g., `12MAR2026`)
- `{{ generated_by }}` — current NetBox user

### Extra Variables (key=value)
Pass any additional variables in the Generate form. Common examples:
- `change_request=CHG-123456`
- `mop_author=Jane Smith`
- `change_window=15MAR2026 0200`
- `approved_by=John Doe`
- `expected_duration=2 hours`

### Device Fields
- `{{ device.name }}`, `{{ device.site.name }}`, `{{ device.role.name }}`
- `{{ device.serial }}`, `{{ device.asset_tag }}`, `{{ device.primary_ip4 }}`
- `{{ device.device_type.manufacturer.name }}`, `{{ device.device_type.model }}`
- `{{ device.rack }}`, `{{ device.cluster.name }}`

### Loops
```
{% for device in devices %}...{% endfor %}
{% for iface in device.interfaces.all %}...{% endfor %}
{% for c in team_contacts %}{{ c.contact.name }} — {{ c.contact.title }}{% endfor %}
{% for vc in vendor_contacts %}{{ vc.contact.name }} — {{ vc.contact.phone }}{% endfor %}
{% for m in management_contacts %}{{ m.name }} — {{ m.title }}{% endfor %}
{% for c in unique_contacts %}{{ c.contact.name }}{% endfor %}
```

### Management Contacts
Note: `management_contacts` are `Contact` objects (not `ContactAssignment`), so fields are accessed directly:
```
{% for m in management_contacts %}{{ m.name }} — {{ m.title }} — {{ m.phone }} — {{ m.email }}{% endfor %}
```

### Conditional Fields (for VM compatibility)
```
{% if device.device_type %}...{% endif %}
{% if device.serial %}...{% endif %}
{% if device.rack %}...{% endif %}
```

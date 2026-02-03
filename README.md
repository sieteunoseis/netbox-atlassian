# NetBox Atlassian Plugin

![NetBox Version](https://img.shields.io/badge/NetBox-4.0+-blue)
![Python Version](https://img.shields.io/badge/Python-3.10+-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI](https://img.shields.io/pypi/v/netbox-atlassian)](https://pypi.org/project/netbox-atlassian/)

Display Jira issues and Confluence pages related to devices in NetBox.

## Features

- **Device Tab** - Shows Jira issues and Confluence pages mentioning device attributes
- **VM Tab** - Same functionality for Virtual Machines
- **Configurable Search Fields** - Search by hostname, serial, asset tag, role, IP, etc.
- **OR Search Logic** - Finds content matching any configured field
- **On-Premise Support** - Works with Jira Server/Data Center and Confluence Server/Data Center (tested)
- **Cloud Ready** - Prepared for Atlassian Cloud (not yet tested)
- **Legacy SSL Support** - Works with older servers requiring legacy SSL renegotiation
- **PAT Authentication** - Supports Personal Access Tokens for Confluence
- **Caching** - Results cached to reduce API calls
- **Project/Space Filtering** - Limit searches to specific Jira projects or Confluence spaces

## Requirements

- NetBox 4.0+
- Python 3.10+
- Access to Jira and/or Confluence REST APIs

## Installation

```bash
pip install netbox-atlassian
```

Add to `configuration.py`:

```python
PLUGINS = [
    "netbox_atlassian",
]
```

## Configuration

```python
PLUGINS_CONFIG = {
    "netbox_atlassian": {
        # Jira settings (on-prem)
        "jira_url": "https://jira.example.com",
        "jira_username": "api_user",
        "jira_password": "api_token_or_password",
        "jira_verify_ssl": True,
        "jira_projects": [],  # Empty = all projects

        # Confluence settings (on-prem)
        "confluence_url": "https://confluence.example.com",
        "confluence_token": "personal-access-token",  # PAT (preferred)
        # OR use username/password:
        # "confluence_username": "api_user",
        # "confluence_password": "api_password",
        "confluence_verify_ssl": True,
        "confluence_spaces": [],  # Empty = all spaces

        # Search configuration
        "search_fields": [
            {"name": "Hostname", "attribute": "name", "enabled": True},
            {"name": "Serial", "attribute": "serial", "enabled": True},
            {"name": "Asset Tag", "attribute": "asset_tag", "enabled": False},
            {"name": "Role", "attribute": "role.name", "enabled": False},
            {"name": "Primary IP", "attribute": "primary_ip4.address", "enabled": False},
        ],

        # Results limits
        "jira_max_results": 10,
        "confluence_max_results": 10,

        # General
        "timeout": 30,
        "cache_timeout": 300,
        "device_types": [],  # Filter by manufacturer (empty = all)
        "enable_legacy_ssl": False,  # Enable for older servers
    }
}
```

## Search Fields

The `search_fields` configuration defines which device attributes are searched. Searches use **OR logic** - content matching any enabled field will be returned.

| Field | Attribute Path | Description |
|-------|---------------|-------------|
| Hostname | `name` | Device name |
| Serial | `serial` | Serial number |
| Asset Tag | `asset_tag` | Asset tag |
| Role | `role.name` | Device role name |
| Primary IP | `primary_ip4.address` | Primary IPv4 address |
| Site | `site.name` | Site name |
| Tenant | `tenant.name` | Tenant name |

### Custom Fields

You can search custom fields using dot notation:

```python
{"name": "CMDB ID", "attribute": "custom_field_data.cmdb_id", "enabled": True}
```

## Screenshots

### Device Tab
Shows Jira issues and Confluence pages in a split view:
- Left: Jira issues with key, summary, status, and type
- Right: Confluence pages with title, space, and breadcrumb

### Settings Page
View current configuration and test connections to Jira/Confluence.

## API Endpoints

The plugin adds these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plugins/atlassian/settings/` | GET | View settings |
| `/plugins/atlassian/test-jira/` | POST | Test Jira connection |
| `/plugins/atlassian/test-confluence/` | POST | Test Confluence connection |

## Troubleshooting

### Connection Errors

1. Verify URLs are correct and accessible from NetBox server
2. Check username/password or API token
3. For on-prem, ensure `verify_ssl` matches your certificate setup
4. Check firewall rules allow outbound HTTPS

### SSL Renegotiation Errors

If you see "unsafe legacy renegotiation disabled" errors, enable legacy SSL:

```python
"enable_legacy_ssl": True,
```

This is required for some older Confluence/Jira servers.

### No Results

1. Verify search fields are enabled in configuration
2. Check that Jira/Confluence content contains the device attributes
3. Review project/space filters if configured
4. Check API user has read permissions

### Slow Performance

1. Increase `cache_timeout` to reduce API calls
2. Reduce `max_results` values
3. Use project/space filters to limit search scope

## Development

```bash
git clone https://github.com/sieteunoseis/netbox-atlassian.git
cd netbox-atlassian
pip install -e ".[dev]"

# Run linting
black netbox_atlassian/
isort netbox_atlassian/
flake8 netbox_atlassian/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

Apache 2.0

## Author

sieteunoseis

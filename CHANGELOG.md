# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-11-17

### Added
- `tab_weight` setting (default `9000`) to control where this plugin's tab sits on object pages, so tab order can be set in config instead of code
- `top_level_menu` setting (default `True`); set `False` to list this plugin's menu items under the shared "Plugins" menu instead of its own top-level sidebar menu

### Changed
- Plugin display name shortened to "Atlassian" (was "NetBox Atlassian") so it matches the sidebar menu label

## [0.5.9] - 2026-05-05

### Fixed

- Fix `ProgrammingError: relation "netbox_atlassian_atlassian" does not exist` on NetBox 4.5+ when navigating to `/core/system/`. The unmanaged permission-anchor model is now flagged with `_netbox_private = True`, and a data migration sets `ObjectType.public = False` so NetBox's object-count loop excludes it.

## [0.2.1] - 2026-02-03

### Changed
- Improved badge readability with consistent `bg-info text-white` styling
- Search term badges now match card title badge colors
- Status badges use `text-white` for better contrast in dark/light modes

## [0.2.0] - 2026-02-03

### Added
- Jira Personal Access Token (PAT) authentication support
- `jira_token` configuration option for PAT-based auth

### Changed
- Jira now supports both PAT (Bearer token) and basic auth like Confluence

## [0.1.0] - 2026-02-03

### Added
- Initial release
- Device tab showing Jira issues and Confluence pages
- Virtual Machine tab support
- Configurable search fields (hostname, serial, asset tag, role, primary IP)
- OR-based search logic across multiple fields
- Support for on-premise Jira (basic auth)
- Support for on-premise Confluence (PAT or basic auth)
- Legacy SSL renegotiation support for older servers
- Caching support with configurable timeout
- Settings page for connection testing

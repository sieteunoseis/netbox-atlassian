"""
Atlassian API Client for Jira and Confluence

Supports both on-premise and cloud deployments.
"""

import logging
import ssl
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

logger = logging.getLogger(__name__)


class LegacySSLAdapter(HTTPAdapter):
    """
    HTTP Adapter that enables legacy SSL renegotiation.

    Required for older servers (like OHSU Confluence) that don't support
    secure renegotiation.
    """

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        # Enable legacy renegotiation for older servers
        ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class AtlassianClient:
    """Client for Jira and Confluence REST APIs."""

    def __init__(self):
        """Initialize the Atlassian client from plugin settings."""
        self.config = settings.PLUGINS_CONFIG.get("netbox_atlassian", {})

        # Jira settings
        self.jira_url = self.config.get("jira_url", "").rstrip("/")
        self.jira_username = self.config.get("jira_username", "")
        self.jira_password = self.config.get("jira_password", "")
        self.jira_token = self.config.get("jira_token", "")  # Personal Access Token
        self.jira_verify_ssl = self.config.get("jira_verify_ssl", True)

        # Confluence settings
        self.confluence_url = self.config.get("confluence_url", "").rstrip("/")
        self.confluence_username = self.config.get("confluence_username", "")
        self.confluence_password = self.config.get("confluence_password", "")
        self.confluence_token = self.config.get("confluence_token", "")  # Personal Access Token
        self.confluence_verify_ssl = self.config.get("confluence_verify_ssl", True)

        # Cloud settings
        self.use_cloud = self.config.get("use_cloud", False)
        self.cloud_api_token = self.config.get("cloud_api_token", "")
        self.cloud_email = self.config.get("cloud_email", "")

        # General settings
        self.timeout = self.config.get("timeout", 30)
        self.cache_timeout = self.config.get("cache_timeout", 300)

        # Legacy SSL support (for servers requiring legacy renegotiation)
        self.enable_legacy_ssl = self.config.get("enable_legacy_ssl", False)

        # Create session with legacy SSL if needed
        self._session = None

    def _get_session(self) -> requests.Session:
        """Get or create a requests session with optional legacy SSL support."""
        if self._session is None:
            self._session = requests.Session()
            if self.enable_legacy_ssl:
                adapter = LegacySSLAdapter()
                self._session.mount("https://", adapter)
        return self._session

    def _get_jira_auth(self):
        """Get authentication for Jira API."""
        if self.use_cloud:
            return (self.cloud_email, self.cloud_api_token)
        return (self.jira_username, self.jira_password)

    def _get_confluence_auth(self):
        """Get authentication for Confluence API."""
        if self.use_cloud:
            return (self.cloud_email, self.cloud_api_token)
        return (self.confluence_username, self.confluence_password)

    def _jira_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make a request to Jira REST API."""
        if not self.jira_url:
            return None

        url = f"{self.jira_url}/rest/api/2/{endpoint}"
        session = self._get_session()

        try:
            # Use PAT (Bearer token) if available, otherwise basic auth
            if self.jira_token:
                headers = {"Authorization": f"Bearer {self.jira_token}"}
                response = session.get(
                    url,
                    headers=headers,
                    params=params,
                    verify=self.jira_verify_ssl,
                    timeout=self.timeout,
                )
            else:
                response = session.get(
                    url,
                    auth=self._get_jira_auth(),
                    params=params,
                    verify=self.jira_verify_ssl,
                    timeout=self.timeout,
                )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API error: {e}")
            return None

    def _confluence_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make a request to Confluence REST API."""
        if not self.confluence_url:
            return None

        url = f"{self.confluence_url}/rest/api/{endpoint}"
        session = self._get_session()

        try:
            # Use PAT (Bearer token) if available, otherwise basic auth
            if self.confluence_token:
                headers = {"Authorization": f"Bearer {self.confluence_token}"}
                response = session.get(
                    url,
                    headers=headers,
                    params=params,
                    verify=self.confluence_verify_ssl,
                    timeout=self.timeout,
                )
            else:
                response = session.get(
                    url,
                    auth=self._get_confluence_auth(),
                    params=params,
                    verify=self.confluence_verify_ssl,
                    timeout=self.timeout,
                )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Confluence API error: {e}")
            return None

    def search_jira(self, search_terms: list[str], max_results: int = 10) -> dict:
        """
        Search Jira for issues containing any of the search terms.

        Args:
            search_terms: List of terms to search (OR logic)
            max_results: Maximum number of results to return

        Returns:
            dict with 'issues' list and 'total' count
        """
        if not self.jira_url or not search_terms:
            return {"issues": [], "total": 0, "error": None}

        # Build JQL query with OR logic
        # Search in summary, description, and comments
        text_queries = []
        for term in search_terms:
            if term:
                # Escape special JQL characters
                escaped = term.replace('"', '\\"')
                text_queries.append(f'text ~ "{escaped}"')

        if not text_queries:
            return {"issues": [], "total": 0, "error": None}

        jql = " OR ".join(text_queries)

        # Add project filter if configured
        projects = self.config.get("jira_projects", [])
        if projects:
            project_jql = " OR ".join([f'project = "{p}"' for p in projects])
            jql = f"({jql}) AND ({project_jql})"

        # Add issue type filter if configured
        issue_types = self.config.get("jira_issue_types", [])
        if issue_types:
            type_jql = " OR ".join([f'issuetype = "{t}"' for t in issue_types])
            jql = f"({jql}) AND ({type_jql})"

        # Order by updated date descending
        jql += " ORDER BY updated DESC"

        cache_key = f"atlassian_jira_{hash(jql)}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,status,issuetype,priority,assignee,created,updated,project",
        }

        result = self._jira_request("search", params)

        if result is None:
            return {"issues": [], "total": 0, "error": "Failed to connect to Jira"}

        issues = []
        for issue in result.get("issues", []):
            fields = issue.get("fields", {})
            issues.append(
                {
                    "key": issue.get("key"),
                    "summary": fields.get("summary", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "status_category": fields.get("status", {}).get("statusCategory", {}).get("key", ""),
                    "type": fields.get("issuetype", {}).get("name", ""),
                    "type_icon": fields.get("issuetype", {}).get("iconUrl", ""),
                    "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
                    "priority_icon": fields.get("priority", {}).get("iconUrl", "") if fields.get("priority") else "",
                    "assignee": (
                        fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "Unassigned"
                    ),
                    "created": fields.get("created", ""),
                    "updated": fields.get("updated", ""),
                    "project": fields.get("project", {}).get("name", ""),
                    "project_key": fields.get("project", {}).get("key", ""),
                    "url": f"{self.jira_url}/browse/{issue.get('key')}",
                }
            )

        response = {
            "issues": issues,
            "total": result.get("total", 0),
            "error": None,
            "cached": False,
        }

        cache.set(cache_key, response, self.cache_timeout)
        return response

    def search_confluence(self, search_terms: list[str], max_results: int = 10) -> dict:
        """
        Search Confluence for pages containing any of the search terms.

        Args:
            search_terms: List of terms to search (OR logic)
            max_results: Maximum number of results to return

        Returns:
            dict with 'pages' list and 'total' count
        """
        if not self.confluence_url or not search_terms:
            return {"pages": [], "total": 0, "error": None}

        # Build CQL query with OR logic
        text_queries = []
        for term in search_terms:
            if term:
                # Escape special CQL characters
                escaped = term.replace('"', '\\"')
                text_queries.append(f'text ~ "{escaped}"')

        if not text_queries:
            return {"pages": [], "total": 0, "error": None}

        cql = " OR ".join(text_queries)

        # Filter to pages only (not attachments, comments, etc.)
        cql = f"({cql}) AND type = page"

        # Add space filter if configured
        spaces = self.config.get("confluence_spaces", [])
        if spaces:
            space_cql = " OR ".join([f'space = "{s}"' for s in spaces])
            cql = f"({cql}) AND ({space_cql})"

        cache_key = f"atlassian_confluence_{hash(cql)}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        params = {
            "cql": cql,
            "limit": max_results,
            "expand": "space,version,ancestors",
        }

        result = self._confluence_request("content/search", params)

        if result is None:
            return {"pages": [], "total": 0, "error": "Failed to connect to Confluence"}

        pages = []
        for page in result.get("results", []):
            space = page.get("space", {})
            version = page.get("version", {})

            # Build breadcrumb from ancestors
            ancestors = page.get("ancestors", [])
            breadcrumb = " > ".join([a.get("title", "") for a in ancestors])

            pages.append(
                {
                    "id": page.get("id"),
                    "title": page.get("title", ""),
                    "space_key": space.get("key", ""),
                    "space_name": space.get("name", ""),
                    "last_modified": version.get("when", ""),
                    "last_modified_by": version.get("by", {}).get("displayName", ""),
                    "breadcrumb": breadcrumb,
                    "url": f"{self.confluence_url}{page.get('_links', {}).get('webui', '')}",
                }
            )

        response = {
            "pages": pages,
            "total": result.get("totalSize", result.get("size", 0)),
            "error": None,
            "cached": False,
        }

        cache.set(cache_key, response, self.cache_timeout)
        return response

    def test_jira_connection(self) -> tuple[bool, str]:
        """Test Jira connection."""
        if not self.jira_url:
            return False, "Jira URL not configured"

        if not self.jira_token and not self.jira_username:
            return False, "Jira credentials not configured (need token or username/password)"

        result = self._jira_request("myself")
        if result:
            return True, f"Connected as {result.get('displayName', result.get('name', 'Unknown'))}"
        return False, "Failed to connect to Jira"

    def test_confluence_connection(self) -> tuple[bool, str]:
        """Test Confluence connection."""
        if not self.confluence_url:
            return False, "Confluence URL not configured"

        if not self.confluence_token and not self.confluence_username:
            return False, "Confluence credentials not configured (need token or username/password)"

        result = self._confluence_request("user/current")
        if result:
            return True, f"Connected as {result.get('displayName', result.get('username', 'Unknown'))}"
        return False, "Failed to connect to Confluence"


def get_client() -> AtlassianClient:
    """Get a configured Atlassian client instance."""
    return AtlassianClient()

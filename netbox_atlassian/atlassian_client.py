"""
Atlassian API Client for Jira and Confluence

Supports both on-premise and cloud deployments.
"""

import logging
import re
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

    def _find_matched_fields(
        self, search_terms: list[str], terms_with_fields: dict[str, str], text_fields: list[str]
    ) -> list[str]:
        """
        Find which search field names matched based on terms appearing in text fields.

        Args:
            search_terms: List of terms to check
            terms_with_fields: Dict mapping term -> field_name (e.g., {"server01": "Hostname"})
            text_fields: List of text values to search in

        Returns:
            List of matched field names (e.g., ["Hostname", "Serial"])
        """
        matched_fields = []
        # Combine all text fields into one searchable string (case-insensitive)
        combined_text = " ".join(str(f) for f in text_fields if f).lower()

        # Get match mode from config (exact or partial)
        match_mode = self.config.get("match_mode", "exact")

        for term in search_terms:
            if not term:
                continue

            term_lower = term.lower()

            if match_mode == "exact":
                # Use word boundary matching for exact terms
                # Escape special regex characters in the term
                escaped_term = re.escape(term_lower)
                # Match whole word only (word boundaries or start/end of string)
                pattern = rf"(?:^|[\s\-_,;:\.\/\(\)\[\]]){escaped_term}(?:$|[\s\-_,;:\.\/\(\)\[\]])"
                if re.search(pattern, combined_text):
                    field_name = terms_with_fields.get(term, term)
                    if field_name not in matched_fields:
                        matched_fields.append(field_name)
            else:
                # Partial/substring match (original behavior)
                if term_lower in combined_text:
                    field_name = terms_with_fields.get(term, term)
                    if field_name not in matched_fields:
                        matched_fields.append(field_name)

        return matched_fields

    def _find_matched_tags(
        self, tag_slugs: list[str], result_labels: list[str], prefix: str = ""
    ) -> list[str]:
        """
        Find which tag slugs matched based on result labels.

        Args:
            tag_slugs: List of tag slugs to check
            result_labels: List of labels from the Jira/Confluence result
            prefix: Label prefix (e.g., "tuce_" for Jira)

        Returns:
            List of matched tag descriptions (e.g., ["Tag: cucm", "Tag: voice-callcontrol"])
        """
        matched = []
        result_labels_lower = {l.lower() for l in result_labels}
        for slug in tag_slugs:
            expected_label = f"{prefix}{slug}".lower()
            if expected_label in result_labels_lower:
                matched.append(f"Tag: {slug}")
        return matched

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

    def search_jira(self, search_terms: list[str], terms_with_fields: dict[str, str], max_results: int = 10, tag_slugs: list[str] = None) -> dict:
        """
        Search Jira for issues containing any of the search terms.

        Args:
            search_terms: List of terms to search (OR logic)
            terms_with_fields: Dict mapping term -> field_name (e.g., {"server01": "Hostname"})
            max_results: Maximum number of results to return

        Returns:
            dict with 'issues' list and 'total' count
        """
        if not self.jira_url or (not search_terms and not tag_slugs):
            return {"issues": [], "total": 0, "error": None}

        # Get search mode from config
        search_mode = self.config.get("jira_search_mode", "strict")

        # Build JQL query with OR logic
        text_queries = []
        for term in search_terms:
            if term:
                # Escape special JQL characters
                escaped = term.replace('"', '\\"')
                if search_mode == "title_only":
                    # Only search in issue summary
                    text_queries.append(f'summary ~ "{escaped}"')
                else:
                    # Search in all content (summary, description, comments)
                    text_queries.append(f'text ~ "{escaped}"')

        # Build label query for tags
        label_queries = []
        jira_prefix = self.config.get("jira_tag_label_prefix", "tuce_")
        if tag_slugs:
            prefixed = [f"{jira_prefix}{s}" for s in tag_slugs]
            label_list = ", ".join([f'"{l}"' for l in prefixed])
            label_queries.append(f"labels in ({label_list})")

        if not text_queries and not label_queries:
            return {"issues": [], "total": 0, "error": None}

        jql = " OR ".join(text_queries + label_queries)

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
            "fields": "summary,status,issuetype,priority,assignee,created,updated,project,labels",
        }

        result = self._jira_request("search", params)

        if result is None:
            return {"issues": [], "total": 0, "error": "Failed to connect to Jira"}

        issues = []
        for issue in result.get("issues", []):
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            key = issue.get("key", "")

            # Find which search field names matched this issue (check summary and key)
            matched_fields = self._find_matched_fields(search_terms, terms_with_fields, [summary, key])

            # Check tag label matches
            if tag_slugs:
                issue_labels = fields.get("labels", [])
                tag_matches = self._find_matched_tags(tag_slugs, issue_labels, jira_prefix)
                matched_fields.extend(tag_matches)

            # Filter based on search mode
            if search_mode in ("title_only", "strict"):
                # Only include results where we can verify the match in summary/key or labels
                if not matched_fields:
                    continue
            # For "full_text" mode, include all results

            issues.append(
                {
                    "key": key,
                    "summary": summary,
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
                    "url": f"{self.jira_url}/browse/{key}",
                    "matched_terms": matched_fields,
                }
            )

        response = {
            "issues": issues,
            "total": len(issues),  # Use filtered count, not API total
            "error": None,
            "cached": False,
        }

        cache.set(cache_key, response, self.cache_timeout)
        return response

    def search_confluence(
        self, search_terms: list[str], terms_with_fields: dict[str, str], max_results: int = 10, tag_slugs: list[str] = None
    ) -> dict:
        """
        Search Confluence for pages containing any of the search terms.

        Args:
            search_terms: List of terms to search (OR logic)
            terms_with_fields: Dict mapping term -> field_name (e.g., {"server01": "Hostname"})
            max_results: Maximum number of results to return

        Returns:
            dict with 'pages' list and 'total' count
        """
        if not self.confluence_url or (not search_terms and not tag_slugs):
            return {"pages": [], "total": 0, "error": None}

        # Get search mode from config
        search_mode = self.config.get("confluence_search_mode", "strict")

        # Build CQL query with OR logic
        text_queries = []
        for term in search_terms:
            if term:
                # Escape special CQL characters
                escaped = term.replace('"', '\\"')
                if search_mode == "title_only":
                    # Only search in page titles
                    text_queries.append(f'title ~ "{escaped}"')
                else:
                    # Search in all content (text includes title, body, comments)
                    text_queries.append(f'text ~ "{escaped}"')

        # Build label query for tags
        label_queries = []
        confluence_prefix = self.config.get("confluence_tag_label_prefix", "")
        if tag_slugs:
            prefixed = [f"{confluence_prefix}{s}" for s in tag_slugs]
            label_list = ", ".join([f'"{l}"' for l in prefixed])
            label_queries.append(f"label in ({label_list})")

        if not text_queries and not label_queries:
            return {"pages": [], "total": 0, "error": None}

        cql = " OR ".join(text_queries + label_queries)

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
            "expand": "space,version,ancestors,metadata.labels",
        }

        result = self._confluence_request("content/search", params)

        if result is None:
            return {"pages": [], "total": 0, "error": "Failed to connect to Confluence"}

        pages = []
        for page in result.get("results", []):
            space = page.get("space", {})
            version = page.get("version", {})
            title = page.get("title", "")

            # Build breadcrumb from ancestors
            ancestors = page.get("ancestors", [])
            breadcrumb = " > ".join([a.get("title", "") for a in ancestors])

            # Find which search field names matched this page (check title and breadcrumb)
            matched_fields = self._find_matched_fields(search_terms, terms_with_fields, [title, breadcrumb])

            # Check tag label matches
            if tag_slugs:
                page_labels = [
                    l.get("name", "") for l in
                    page.get("metadata", {}).get("labels", {}).get("results", [])
                ]
                tag_matches = self._find_matched_tags(tag_slugs, page_labels, confluence_prefix)
                matched_fields.extend(tag_matches)

            # Filter based on search mode
            if search_mode in ("title_only", "strict"):
                # Only include results where we can verify the match in title/breadcrumb or labels
                if not matched_fields:
                    continue
            # For "full_text" mode, include all results

            pages.append(
                {
                    "id": page.get("id"),
                    "title": title,
                    "space_key": space.get("key", ""),
                    "space_name": space.get("name", ""),
                    "last_modified": version.get("when", ""),
                    "last_modified_by": version.get("by", {}).get("displayName", ""),
                    "breadcrumb": breadcrumb,
                    "url": f"{self.confluence_url}{page.get('_links', {}).get('webui', '')}",
                    "matched_terms": matched_fields,
                }
            )

        response = {
            "pages": pages,
            "total": len(pages),  # Use filtered count, not API total
            "error": None,
            "cached": False,
        }

        cache.set(cache_key, response, self.cache_timeout)
        return response

    def _convert_wiki_to_storage(self, session, wiki_body: str) -> str | None:
        """Convert wiki markup to Confluence storage format via the REST API."""
        url = f"{self.confluence_url}/rest/api/contentbody/convert/storage"
        headers = {"Content-Type": "application/json"}
        if self.confluence_token:
            headers["Authorization"] = f"Bearer {self.confluence_token}"
        try:
            kwargs = {
                "json": {"value": wiki_body, "representation": "wiki"},
                "headers": headers,
                "verify": self.confluence_verify_ssl,
                "timeout": self.timeout,
            }
            if not self.confluence_token:
                kwargs["auth"] = self._get_confluence_auth()
            resp = session.post(url, **kwargs)
            resp.raise_for_status()
            return resp.json().get("value")
        except Exception as e:
            logger.warning(f"Wiki-to-storage conversion failed, falling back to wiki: {e}")
            return None

    @staticmethod
    def _convert_checkboxes_to_tasks(storage: str) -> str:
        """Replace <li>[ ] text</li> and <li>☑ text</li> with <ac:task> elements."""
        import re
        import uuid

        _DONE_PLACEHOLDER = "\u200b\u2611\u200b"  # matches the placeholder set during wiki prep
        # Pattern matches [ ] (unchecked) or the placeholder (checked)
        _CB_PATTERN = re.compile(
            rf"<li>\s*(?:\[( )\]|({re.escape(_DONE_PLACEHOLDER)}))\s*(.*?)</li>",
            re.DOTALL,
        )
        _CB_DETECT = re.compile(rf"<li>\s*(?:\[ \]|{re.escape(_DONE_PLACEHOLDER)})")

        task_id_counter = [1]

        def _replace_task_list(match):
            """Convert a <ul> block that contains checkbox items into an <ac:task-list>."""
            ul_content = match.group(1)
            # Check if any list item has a checkbox pattern
            if not _CB_DETECT.search(ul_content):
                return match.group(0)  # No checkboxes, return unchanged

            tasks = []
            for li_match in _CB_PATTERN.finditer(ul_content):
                checked = li_match.group(2) is not None  # placeholder = done
                body_text = li_match.group(3).strip()
                status = "complete" if checked else "incomplete"
                task_id = task_id_counter[0]
                task_uuid = str(uuid.uuid4())
                task_id_counter[0] += 1
                tasks.append(
                    f"<ac:task>\n"
                    f"<ac:task-id>{task_id}</ac:task-id>\n"
                    f"<ac:task-uuid>{task_uuid}</ac:task-uuid>\n"
                    f"<ac:task-status>{status}</ac:task-status>\n"
                    f"<ac:task-body>{body_text}</ac:task-body>\n"
                    f"</ac:task>"
                )

            # Also keep any non-checkbox <li> items as regular list items
            non_checkbox_items = re.findall(
                rf"<li>(?!\s*(?:\[ \]|{re.escape(_DONE_PLACEHOLDER)}))(.*?)</li>",
                ul_content,
                re.DOTALL,
            )

            result = ""
            if tasks:
                result += "<ac:task-list>\n" + "\n".join(tasks) + "\n</ac:task-list>"
            if non_checkbox_items:
                items = "".join(f"<li>{item}</li>" for item in non_checkbox_items)
                result += f"<ul>{items}</ul>"
            return result

        return re.sub(r"<ul>(.*?)</ul>", _replace_task_list, storage, flags=re.DOTALL)

    def create_confluence_page(
        self, space_key: str, title: str, body: str, parent_id: str
    ) -> dict:
        """
        Create a new Confluence page as a child of the given parent.

        Args:
            space_key: Confluence space key (e.g. 'Netv')
            title: Page title
            body: Page content in Confluence wiki markup (storage format: wiki)
            parent_id: Parent page ID

        Returns:
            dict with 'success', 'url', and 'error' keys
        """
        if not self.confluence_url:
            return {"success": False, "url": None, "error": "Confluence URL not configured"}

        session = self._get_session()

        # Step 1: Escape [x] before wiki conversion (Confluence treats it as a link)
        import re as _re
        _DONE_PLACEHOLDER = "\u200b\u2611\u200b"  # zero-width space + ballot box + zero-width space
        wiki_body = _re.sub(r"(\* )\[x\] ", rf"\1{_DONE_PLACEHOLDER} ", body)

        # Step 2: Convert wiki markup to storage format via Confluence API
        storage_body = self._convert_wiki_to_storage(session, wiki_body)
        if storage_body is None:
            # Fallback: post as wiki if conversion fails
            body_payload = {"wiki": {"value": body, "representation": "wiki"}}
        else:
            # Step 3: Convert [ ] and placeholder checkbox bullets into proper <ac:task> elements
            storage_body = self._convert_checkboxes_to_tasks(storage_body)
            body_payload = {"storage": {"value": storage_body, "representation": "storage"}}

        url = f"{self.confluence_url}/rest/api/content"

        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "ancestors": [{"id": str(parent_id)}],
            "body": body_payload,
        }

        headers = {"Content-Type": "application/json"}
        if self.confluence_token:
            headers["Authorization"] = f"Bearer {self.confluence_token}"

        try:
            if self.confluence_token:
                response = session.post(
                    url,
                    json=payload,
                    headers=headers,
                    verify=self.confluence_verify_ssl,
                    timeout=self.timeout,
                )
            else:
                response = session.post(
                    url,
                    json=payload,
                    headers=headers,
                    auth=self._get_confluence_auth(),
                    verify=self.confluence_verify_ssl,
                    timeout=self.timeout,
                )
            response.raise_for_status()
            data = response.json()
            page_url = f"{self.confluence_url}{data.get('_links', {}).get('webui', '')}"
            return {"success": True, "url": page_url, "error": None, "page_id": data.get("id")}
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", error_msg)
            except Exception:
                pass
            logger.error(f"Confluence create page error: {error_msg}")
            return {"success": False, "url": None, "error": error_msg}
        except requests.exceptions.RequestException as e:
            logger.error(f"Confluence create page error: {e}")
            return {"success": False, "url": None, "error": str(e)}

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

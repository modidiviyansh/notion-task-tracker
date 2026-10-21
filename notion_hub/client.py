"""
Core Notion API Client for Antigravity developer workflows.
Zero-dependency, resilient HTTP client targeting Notion API v2022-06-28.
"""
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional
from .converter import markdown_to_blocks, blocks_to_markdown

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def _find_and_load_env():
    """Find and load .env file if available."""
    cur = Path.cwd()
    for _ in range(4):
        env_file = cur / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass
            break
        if cur.parent == cur:
            break
        cur = cur.parent

_find_and_load_env()

class NotionError(Exception):
    def __init__(self, status_code: int, message: str, raw_response: Any = None):
        self.status_code = status_code
        self.message = message
        self.raw_response = raw_response
        super().__init__(f"Notion API Error [{status_code}]: {message}")

class NotionClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise ValueError(
                "Notion token not found! Set the NOTION_TOKEN environment variable or put it in .env"
            )

    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{NOTION_BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{NOTION_BASE_URL}/{endpoint}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "Antigravity-NotionHub/1.0"
        }

        retries = 3
        for attempt in range(retries):
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    resp_text = response.read().decode("utf-8")
                    return json.loads(resp_text) if resp_text else {}
            except urllib.error.HTTPError as e:
                try:
                    error_body = json.loads(e.read().decode("utf-8"))
                    msg = error_body.get("message", e.reason)
                except Exception:
                    msg = e.reason
                raise NotionError(e.code, msg)
            except (urllib.error.URLError, ConnectionResetError, TimeoutError) as e:
                if attempt == retries - 1:
                    reason = getattr(e, "reason", str(e))
                    raise NotionError(0, f"Network connection failed: {reason}")
                import time
                time.sleep(1)

    # ================= USER / AUTH =================
    def get_me(self) -> Dict[str, Any]:
        """Verify token and get bot & workspace details."""
        return self._request("GET", "/users/me")

    # ================= SEARCH =================
    def search(self, query: str = "", filter_type: Optional[str] = None, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Search pages or databases.
        filter_type can be 'page' or 'database'.
        """
        payload: Dict[str, Any] = {"page_size": page_size}
        if query:
            payload["query"] = query
        if filter_type:
            payload["filter"] = {"value": filter_type, "property": "object"}
        
        res = self._request("POST", "/search", payload)
        return res.get("results", [])

    def list_databases(self) -> List[Dict[str, Any]]:
        """List all accessible databases."""
        return self.search(filter_type="database")

    def list_pages(self) -> List[Dict[str, Any]]:
        """List all accessible pages."""
        return self.search(filter_type="page")

    # ================= PAGES & BLOCKS =================
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve page metadata and properties."""
        clean_id = page_id.replace("-", "")
        return self._request("GET", f"/pages/{clean_id}")

    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """Retrieve all block children of a page, handling pagination."""
        clean_id = page_id.replace("-", "")
        all_blocks = []
        start_cursor = None

        while True:
            endpoint = f"/blocks/{clean_id}/children?page_size=100"
            if start_cursor:
                endpoint += f"&start_cursor={start_cursor}"
            
            res = self._request("GET", endpoint)
            all_blocks.extend(res.get("results", []))

            if not res.get("has_more"):
                break
            start_cursor = res.get("next_cursor")

        return all_blocks

    def get_page_markdown(self, page_id: str) -> str:
        """Fetch all blocks for a page and return them as a Markdown string."""
        blocks = self.get_page_blocks(page_id)
        for b in blocks:
            if b.get("type") == "table" and b.get("has_children") and not b.get("children"):
                b["children"] = self.get_page_blocks(b["id"])
        return blocks_to_markdown(blocks)

    def create_page(
        self,
        parent_id: str,
        title: str,
        content_markdown: str = "",
        is_database_parent: bool = False,
        properties: Optional[Dict[str, Any]] = None,
        icon_emoji: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new page either under an existing page or inside a database.
        Automatically parses markdown into Notion blocks.
        """
        clean_parent = parent_id.replace("-", "") if parent_id else ""
        payload: Dict[str, Any] = {}

        if is_database_parent:
            payload["parent"] = {"database_id": clean_parent}
            props = properties or {}
            # Ensure a title property is provided
            has_title_prop = any(isinstance(v, dict) and "title" in v for v in props.values())
            if not has_title_prop and "Name" not in props and "title" not in props:
                props["Name"] = {"title": [{"text": {"content": title}}]}
            payload["properties"] = props
        elif not parent_id or clean_parent.lower() == "workspace":
            payload["parent"] = {"type": "workspace", "workspace": True}
            payload["properties"] = {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        else:
            payload["parent"] = {"page_id": clean_parent}
            payload["properties"] = {
                "title": [{"type": "text", "text": {"content": title}}]
            }

        if icon_emoji:
            payload["icon"] = {"type": "emoji", "emoji": icon_emoji}

        if content_markdown:
            # Notion allows max 100 blocks on page creation
            blocks = markdown_to_blocks(content_markdown)
            initial_blocks = blocks[:100]
            if initial_blocks:
                payload["children"] = initial_blocks

        res = self._request("POST", "/pages", payload)
        new_page_id = res.get("id")

        # If there are remaining blocks (>100), append them in batches
        if content_markdown and len(blocks) > 100 and new_page_id:
            remaining = blocks[100:]
            for i in range(0, len(remaining), 100):
                batch = remaining[i:i + 100]
                self._request("PATCH", f"/blocks/{new_page_id.replace('-', '')}/children", {"children": batch})

        return res

    def append_markdown(self, page_id: str, content_markdown: str) -> List[Dict[str, Any]]:
        """Append markdown content to an existing page."""
        clean_id = page_id.replace("-", "")
        blocks = markdown_to_blocks(content_markdown)
        if not blocks:
            return []

        results = []
        for i in range(0, len(blocks), 100):
            batch = blocks[i:i + 100]
            res = self._request("PATCH", f"/blocks/{clean_id}/children", {"children": batch})
            results.extend(res.get("results", []))
        return results

    def clear_page_blocks(self, page_id: str, keep_types: Optional[List[str]] = None) -> int:
        """
        Delete all blocks on a page except those whose type is in keep_types (e.g. ['child_database']).
        Returns the number of deleted blocks.
        """
        keep = set(keep_types or ["child_database"])
        blocks = self.get_page_blocks(page_id)
        deleted = 0
        for b in blocks:
            btype = b.get("type", "")
            if btype not in keep:
                bid = b.get("id")
                if bid:
                    try:
                        self._request("DELETE", f"/blocks/{bid.replace('-', '')}")
                        deleted += 1
                    except Exception:
                        pass
        return deleted

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update properties on an existing page."""
        clean_id = page_id.replace("-", "")
        return self._request("PATCH", f"/pages/{clean_id}", {"properties": properties})

    def archive_page(self, page_id: str) -> Dict[str, Any]:
        """Archive (soft-delete) a page."""
        clean_id = page_id.replace("-", "")
        return self._request("PATCH", f"/pages/{clean_id}", {"archived": True})

    # ================= DATABASES & TASKS =================
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Retrieve database schema and details."""
        clean_id = database_id.replace("-", "")
        return self._request("GET", f"/databases/{clean_id}")

    def query_database(
        self,
        database_id: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Query entries in a database."""
        clean_id = database_id.replace("-", "")
        payload: Dict[str, Any] = {"page_size": page_size}
        if filter_dict:
            payload["filter"] = filter_dict
        if sorts:
            payload["sorts"] = sorts

        res = self._request("POST", f"/databases/{clean_id}/query", payload)
        return res.get("results", [])

    def create_task(
        self,
        database_id: str,
        title: str,
        done: bool = False,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        extra_props: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a task in a tasks/to-do database.
        Adapts dynamically to the database properties (Name, Done/Status, Due Date).
        """
        db = self.get_database(database_id)
        props_schema = db.get("properties", {})

        # Find title field name (usually 'Name' or 'Task')
        title_field = "Name"
        for k, v in props_schema.items():
            if v.get("type") == "title":
                title_field = k
                break

        properties: Dict[str, Any] = {
            title_field: {"title": [{"text": {"content": title}}]}
        }

        # Handle Done checkbox if present
        for k, v in props_schema.items():
            if v.get("type") == "checkbox" and "done" in k.lower():
                properties[k] = {"checkbox": done}
            elif v.get("type") == "date" and ("due" in k.lower() or "date" in k.lower()) and due_date:
                properties[k] = {"date": {"start": due_date}}
            elif v.get("type") == "select" and "status" in k.lower() and not done:
                # If there's a status select and it's not done
                properties[k] = {"select": {"name": "In Progress" if not done else "Done"}}

        if extra_props:
            properties.update(extra_props)

        content = notes if notes else ""
        return self.create_page(
            parent_id=database_id,
            title=title,
            content_markdown=content,
            is_database_parent=True,
            properties=properties
        )

    def update_task_status(
        self,
        page_id: str,
        done: Optional[bool] = None,
        status_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update task completion status or status select."""
        clean_id = page_id.replace("-", "")
        page = self.get_page(clean_id)
        parent = page.get("parent", {})

        properties: Dict[str, Any] = {}
        if parent.get("type") == "database_id":
            db = self.get_database(parent["database_id"])
            props_schema = db.get("properties", {})

            is_completing = (done is True) or (status_name in ("Done", "Complete"))
            is_uncompleting = (done is False) or (status_name and status_name not in ("Done", "Complete"))

            from datetime import datetime, timezone
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            for k, v in props_schema.items():
                k_lower = k.lower()
                # Checkbox sync
                if v.get("type") == "checkbox" and ("done" in k_lower or "complete" in k_lower):
                    if is_completing:
                        properties[k] = {"checkbox": True}
                    elif is_uncompleting:
                        properties[k] = {"checkbox": False}
                    elif done is not None:
                        properties[k] = {"checkbox": done}

                # Status / Select sync
                if v.get("type") == "select" and "status" in k_lower and status_name:
                    properties[k] = {"select": {"name": status_name}}
                elif v.get("type") == "status" and status_name:
                    properties[k] = {"status": {"name": status_name}}

                # Completed At auto-timestamp
                if v.get("type") == "date" and ("completed" in k_lower or "finished" in k_lower):
                    if is_completing:
                        properties[k] = {"date": {"start": today_str}}
                    elif is_uncompleting:
                        properties[k] = {"date": None}

        if not properties and done is not None:
            properties["Done"] = {"checkbox": done}

        return self._request("PATCH", f"/pages/{clean_id}", {"properties": properties})

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties_schema: Dict[str, Any],
        icon_emoji: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new database under a parent page."""
        clean_parent = parent_page_id.replace("-", "")
        payload: Dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": clean_parent},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties_schema
        }
        if icon_emoji:
            payload["icon"] = {"type": "emoji", "emoji": icon_emoji}

        return self._request("POST", "/databases", payload)

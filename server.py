import json
import os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from pydantic import Field

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_DATA_PATH = Path(__file__).parent / "data" / "gitlab.json"
_db: dict = json.loads(_DATA_PATH.read_text())


def _match(record: dict, field: str, value: str) -> bool:
    """Case-insensitive substring match on a field."""
    return value.lower() in str(record.get(field, "")).lower()


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="gitlab-mock",
    version="1.0.0",
    instructions=(
        "Mock GitLab MCP server for ImmersaLabs VR projects. Query issues, merge requests, "
        "pipelines, commits, milestones, and team members across all repositories."
    ),
)

# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@mcp.tool()
def get_projects(
    id: Optional[str] = Field(default=None, description="Filter by project ID, e.g. P1"),
    name: Optional[str] = Field(default=None, description="Filter by exact project name, e.g. vr-core-engine"),
    search: Optional[str] = Field(default=None, description="Partial match on project name or description"),
) -> list[dict]:
    """List GitLab projects. Optionally filter by ID, exact name, or free-text search on name/description."""
    results = _db["projects"]
    if id:
        results = [r for r in results if r["id"].upper() == id.upper()]
    if name:
        results = [r for r in results if r["name"].lower() == name.lower()]
    if search:
        results = [r for r in results if _match(r, "name", search) or _match(r, "description", search)]
    return results


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

@mcp.tool()
def get_issues(
    project_id: Optional[str] = Field(default=None, description="Filter by project ID, e.g. P1"),
    state: Optional[str] = Field(default=None, description="Filter by state: open | closed"),
    label: Optional[str] = Field(default=None, description="Filter by label (partial match), e.g. bug, P0, rendering"),
    assignee_username: Optional[str] = Field(default=None, description="Filter by assignee username, e.g. marcus.klein"),
    priority: Optional[str] = Field(default=None, description="Filter by priority label: P0 | P1 | P2"),
    search: Optional[str] = Field(default=None, description="Partial match on issue title"),
) -> list[dict]:
    """List issues. Optionally filter by project, state, label, assignee, priority, or title search."""
    results = _db["issues"]
    if project_id:
        results = [r for r in results if r["project_id"].upper() == project_id.upper()]
    if state:
        results = [r for r in results if _match(r, "state", state)]
    if label:
        results = [r for r in results if any(label.lower() in lbl.lower() for lbl in r.get("labels", []))]
    if assignee_username:
        results = [r for r in results if _match(r, "assignee_username", assignee_username)]
    if priority:
        results = [r for r in results if priority.upper() in [lbl.upper() for lbl in r.get("labels", [])]]
    if search:
        results = [r for r in results if _match(r, "title", search)]
    return results


# ---------------------------------------------------------------------------
# Merge Requests
# ---------------------------------------------------------------------------

@mcp.tool()
def get_merge_requests(
    project_id: Optional[str] = Field(default=None, description="Filter by project ID, e.g. P2"),
    state: Optional[str] = Field(default=None, description="Filter by state: opened | merged | closed"),
    assignee_username: Optional[str] = Field(default=None, description="Filter by assignee username"),
    author_username: Optional[str] = Field(default=None, description="Filter by author username"),
    draft: Optional[bool] = Field(default=None, description="If true, return only draft MRs; if false, return only non-draft MRs"),
) -> list[dict]:
    """List merge requests. Optionally filter by project, state, assignee, author, or draft status."""
    results = _db["merge_requests"]
    if project_id:
        results = [r for r in results if r["project_id"].upper() == project_id.upper()]
    if state:
        results = [r for r in results if _match(r, "state", state)]
    if assignee_username:
        results = [r for r in results if _match(r, "assignee_username", assignee_username)]
    if author_username:
        results = [r for r in results if _match(r, "author_username", author_username)]
    if draft is not None:
        results = [r for r in results if r.get("draft") == draft]
    return results


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------

@mcp.tool()
def get_pipelines(
    project_id: Optional[str] = Field(default=None, description="Filter by project ID, e.g. P3"),
    status: Optional[str] = Field(default=None, description="Filter by status: success | failed | running | canceled"),
    branch: Optional[str] = Field(default=None, description="Filter by branch name (partial match)"),
    triggered_by: Optional[str] = Field(default=None, description="Filter by user ID who triggered the pipeline, e.g. U2"),
) -> list[dict]:
    """List CI/CD pipelines. Optionally filter by project, status, branch, or triggering user."""
    results = _db["pipelines"]
    if project_id:
        results = [r for r in results if r["project_id"].upper() == project_id.upper()]
    if status:
        results = [r for r in results if _match(r, "status", status)]
    if branch:
        results = [r for r in results if _match(r, "branch", branch)]
    if triggered_by:
        results = [r for r in results if r.get("triggered_by", "").upper() == triggered_by.upper()]
    return results


# ---------------------------------------------------------------------------
# Commits
# ---------------------------------------------------------------------------

@mcp.tool()
def get_commits(
    project_id: Optional[str] = Field(default=None, description="Filter by project ID, e.g. P4"),
    branch: Optional[str] = Field(default=None, description="Filter by branch name (partial match)"),
    author: Optional[str] = Field(default=None, description="Filter by author username (partial match)"),
) -> list[dict]:
    """List recent commits. Optionally filter by project, branch, or author."""
    results = _db["commits"]
    if project_id:
        results = [r for r in results if r["project_id"].upper() == project_id.upper()]
    if branch:
        results = [r for r in results if _match(r, "branch", branch)]
    if author:
        results = [r for r in results if _match(r, "author", author)]
    return results


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@mcp.tool()
def get_users(
    username: Optional[str] = Field(default=None, description="Filter by username (partial match), e.g. yuki"),
    role: Optional[str] = Field(default=None, description="Filter by role: Owner | Maintainer | Developer"),
) -> list[dict]:
    """List team members. Optionally filter by username or role."""
    results = _db["users"]
    if username:
        results = [r for r in results if _match(r, "username", username)]
    if role:
        results = [r for r in results if _match(r, "role", role)]
    return results


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------

@mcp.tool()
def get_milestones(
    project_id: Optional[str] = Field(default=None, description="Filter by project ID, e.g. P1"),
    state: Optional[str] = Field(default=None, description="Filter by state: active | closed"),
) -> list[dict]:
    """List milestones. Optionally filter by project or state."""
    results = _db["milestones"]
    if project_id:
        results = [r for r in results if r["project_id"].upper() == project_id.upper()]
    if state:
        results = [r for r in results if _match(r, "state", state)]
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

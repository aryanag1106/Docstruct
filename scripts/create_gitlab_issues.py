#!/usr/bin/env python3
"""
Bulk-create GitLab milestones + issues (with assignee, time estimate, due date,
labels) from docs/issues.yaml. Built for code.swecha.org but works against any
GitLab instance's REST API.

Why this exists: Phase 1 requires "Issues w/ assignee + estimate + due date" in
the GitLab repo. Clicking through the UI for 20 issues is a waste of your
10am deadline. Run this once instead.

Usage:
    pip install requests PyYAML
    export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"   # GitLab > Settings > Access Tokens, scope: api
    python scripts/create_gitlab_issues.py \\
        --gitlab-url https://code.swecha.org \\
        --project-path yourgroup/formsetu \\
        --issues-file docs/issues.yaml

Add --dry-run first to see exactly what would be created/sent, with no token
required and no network calls.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import requests
except ImportError:  # pragma: no cover
    print("Missing dependency. Run: pip install requests PyYAML", file=sys.stderr)
    raise


def hours_to_gitlab_duration(hours: float) -> str:
    """Convert e.g. 1.5 -> '1h30m' for GitLab's time-tracking quick syntax."""
    whole_hours = int(hours)
    minutes = round((hours - whole_hours) * 60)
    parts = []
    if whole_hours:
        parts.append(f"{whole_hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return "".join(parts) or "0m"


class GitLabClient:
    def __init__(self, base_url: str, token: str | None, project_path: str, dry_run: bool):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.project_path = project_path
        self.dry_run = dry_run
        self.session = requests.Session()
        if token:
            self.session.headers["PRIVATE-TOKEN"] = token
        self._user_cache: dict[str, int] = {}
        self._project_id: int | None = None

    def _api(self, path: str) -> str:
        return f"{self.base_url}/api/v4{path}"

    def project_id(self) -> int:
        if self.dry_run:
            return -1
        if self._project_id is None:
            from urllib.parse import quote

            encoded = quote(self.project_path, safe="")
            resp = self.session.get(self._api(f"/projects/{encoded}"))
            resp.raise_for_status()
            self._project_id = resp.json()["id"]
        return self._project_id

    def user_id(self, username: str) -> int | None:
        if "replace_with" in username:
            print(f"  ! WARNING: '{username}' is a placeholder — issue will be created unassigned.")
            return None
        if self.dry_run:
            return -1
        if username not in self._user_cache:
            resp = self.session.get(self._api("/users"), params={"username": username})
            resp.raise_for_status()
            data = resp.json()
            if not data:
                print(f"  ! WARNING: GitLab user '{username}' not found — issue will be unassigned.")
                self._user_cache[username] = None
            else:
                self._user_cache[username] = data[0]["id"]
        return self._user_cache[username]

    def ensure_milestone(self, name: str, description: str, due_date: str) -> int | None:
        print(f"Milestone: {name} (due {due_date})")
        if self.dry_run:
            return -1
        pid = self.project_id()
        resp = self.session.get(self._api(f"/projects/{pid}/milestones"), params={"search": name})
        resp.raise_for_status()
        existing = [m for m in resp.json() if m["title"] == name]
        if existing:
            return existing[0]["id"]
        resp = self.session.post(
            self._api(f"/projects/{pid}/milestones"),
            data={"title": name, "description": description, "due_date": due_date},
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def create_issue(self, issue: dict[str, Any], milestone_id: int | None) -> int | None:
        title = issue["title"]
        print(f"Issue: {title}")
        assignee_id = self.user_id(issue["assignee_username"])
        labels = ",".join(issue.get("labels", []))
        if self.dry_run:
            print(
                f"    -> would POST issue title={title!r} assignee_id={assignee_id} "
                f"milestone_id={milestone_id} due_date={issue['due_date']} labels={labels} "
                f"estimate={hours_to_gitlab_duration(issue['estimate_hours'])}"
            )
            return -1

        pid = self.project_id()
        payload = {
            "title": title,
            "description": issue.get("description", ""),
            "due_date": issue["due_date"],
            "labels": labels,
        }
        if assignee_id:
            payload["assignee_ids"] = [assignee_id]
        if milestone_id:
            payload["milestone_id"] = milestone_id

        resp = self.session.post(self._api(f"/projects/{pid}/issues"), data=payload)
        resp.raise_for_status()
        issue_iid = resp.json()["iid"]

        # Time estimate is a separate Time Tracking API call.
        duration = hours_to_gitlab_duration(issue["estimate_hours"])
        est_resp = self.session.post(
            self._api(f"/projects/{pid}/issues/{issue_iid}/time_estimate"),
            params={"duration": duration},
        )
        est_resp.raise_for_status()
        return issue_iid


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--gitlab-url", default="https://code.swecha.org")
    parser.add_argument("--project-path", required=True, help="e.g. yourgroup/formsetu")
    parser.add_argument("--issues-file", default="docs/issues.yaml", type=Path)
    parser.add_argument("--token", default=None, help="defaults to $GITLAB_TOKEN")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen, make no API calls")
    args = parser.parse_args()

    import os

    token = args.token or os.environ.get("GITLAB_TOKEN")
    if not token and not args.dry_run:
        print("No token found. Set GITLAB_TOKEN or pass --token, or use --dry-run.", file=sys.stderr)
        return 1

    data = yaml.safe_load(args.issues_file.read_text())
    client = GitLabClient(args.gitlab_url, token, args.project_path, args.dry_run)

    milestone_ids: dict[str, int | None] = {}
    for m in data.get("milestones", []):
        milestone_ids[m["name"]] = client.ensure_milestone(m["name"], m.get("description", ""), m["due_date"])

    created = 0
    for issue in data.get("issues", []):
        milestone_id = milestone_ids.get(issue.get("milestone"))
        client.create_issue(issue, milestone_id)
        created += 1

    if args.dry_run:
        status_msg = "(dry run, nothing was actually created)"
    else:
        status_msg = f"{created} issues processed."
    print(f"\nDone. {status_msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

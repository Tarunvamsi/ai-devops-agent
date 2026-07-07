"""
Skill: search_github_commits

Fetches recent commits from a GitHub repo, optionally filtered to a
specific file path. This is a real GitHub REST API call — no library
needed beyond `requests`.

Why this matters for RCA: a build fails right after a commit touches
the exact file in the stack trace -> strong signal about the cause.
"""

import os
from typing import List, Optional

import requests

from models import CommitInfo

GITHUB_API = "https://api.github.com"


def search_github_commits(
    repo: str,
    path_filter: Optional[str] = None,
    max_commits: int = 5,
    branch: Optional[str] = None,
) -> List[CommitInfo]:
    """
    Skill: fetch recent commits from a GitHub repo.

    Args:
        repo: "owner/repo", e.g. "psf/requests"
        path_filter: only return commits that touched this file/path
                     (e.g. "app/auth.py"). None = no filter.
        max_commits: how many commits to return
        branch: branch name, defaults to the repo's default branch

    Returns:
        List[CommitInfo], most recent first
    """
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {"per_page": max_commits}
    if path_filter:
        params["path"] = path_filter
    if branch:
        params["sha"] = branch

    resp = requests.get(f"{GITHUB_API}/repos/{repo}/commits", headers=headers, params=params, timeout=10)
    resp.raise_for_status()

    commits = []
    for item in resp.json():
        commit_data = item["commit"]
        commits.append(
            CommitInfo(
                sha=item["sha"][:7],
                author=commit_data["author"]["name"],
                message=commit_data["message"].split("\n")[0],  # first line only
                date=commit_data["author"]["date"],
                url=item["html_url"],
            )
        )
    return commits


def format_commits_for_report(commits: List[CommitInfo]) -> str:
    """Human-readable block for inclusion in a report / next LLM prompt."""
    if not commits:
        return "No commits found."
    lines = []
    for c in commits:
        lines.append(f"- [{c.sha}] {c.message} ({c.author}, {c.date})")
    return "\n".join(lines)
"""
Module providing utility functions to interact with Git repositories.
"""

import subprocess
import sys
from typing import List, Tuple, TypedDict


class Commit(TypedDict):
    """Represents a Git commit."""

    hash: str
    subject: str
    body: str
    date: str


def run_git_command(args: List[str]) -> str:
    """Execute a git command and return its output."""
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        print(f"Output: {e.output}", file=sys.stderr)
        sys.exit(1)


def get_tags() -> List[Tuple[str, str]]:
    """Get all tags sorted by commit date (newest first)."""
    output = run_git_command(["tag", "--sort=-creatordate"])
    if not output:
        return []

    tags = []
    for tag in output.split("\n"):
        if tag:
            # Get the author date for this tag
            date_str = run_git_command(["log", "-1", "--format=%ai", tag])
            tags.append((tag, date_str))

    return tags


def get_commits_between(tag_from: str, tag_to: str = "HEAD") -> List[Commit]:
    """Get commits between two tags (or from tag to HEAD)."""
    revision_range = f"{tag_from}..{tag_to}"

    # Get commit hashes
    output = run_git_command(["log", "--format=%H", revision_range])
    if not output:
        return []

    commit_hashes = output.split("\n")
    commits: List[Commit] = []

    for commit_hash in commit_hashes:
        if not commit_hash:
            continue

        # Get commit subject, body, and date
        subject = run_git_command(["log", "-1", "--format=%s", commit_hash])
        body = run_git_command(["log", "-1", "--format=%b", commit_hash])
        date = run_git_command(["log", "-1", "--format=%ai", commit_hash])

        commits.append(
            {"hash": commit_hash, "subject": subject, "body": body, "date": date}
        )

    return commits


def is_working_tree_dirty() -> bool:
    """Check if the git working tree is not clean."""
    status = run_git_command(["status", "--porcelain"])
    return bool(status)

#!/usr/bin/env python3
"""
Changelog Generator for Factorio Mods
Parses git commit history between tags and generates a changelog.txt file
following Factorio's changelog format requirements.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

from format_json import format_json_prettier
from git_utils import (
    Commit,
    get_commits_between,
    get_tags,
    is_working_tree_dirty,
    run_git_command,
)

CATEGORY_MAP = {
    "major": "Major Features",
    "feat": "Features",
    "minor": "Minor Features",
    "graphics": "Graphics",
    "sounds": "Sounds",
    "perf": "Optimizations",
    "balance": "Balancing",
    "combat": "Combat Balancing",
    "circuits": "Circuit Network",
    "change": "Changes",
    "fix": "Bugfixes",
    "modding": "Modding",
    "scripting": "Scripting",
    "gui": "Gui",
    "control": "Control",
    "translations": "Translation",
    "debug": "Debug",
    "info": "Info",
    "ease": "Ease of use",
    "locale": "Locale",
}

# Prefixes to ignore (commits with these prefixes will be skipped)
IGNORED_PREFIXES = {"release"}


def parse_commit_line(line: str) -> Tuple[str, str] | None:
    """Parse a single commit line to extract category and description.
    Returns (category, description) if line matches pattern, None otherwise.
    """
    if not line or not line.strip():
        return None

    line = line.strip()
    # Remove leading dash and whitespace if present (for body lines)
    line = re.sub(r"^-\s*", "", line)

    # Match pattern like "prefix: description" or "prefix(scope): description"
    match = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?\s*:\s*(.+)$", line)

    if match:
        prefix = match.group(1).lower()

        # Skip ignored prefixes
        if prefix in IGNORED_PREFIXES:
            return None

        description = match.group(2).strip()

        # Map prefix to category
        category = CATEGORY_MAP.get(prefix, "Changes")
        return category, description

    return None


def categorize_commits(commits: List[Commit]) -> Dict[str, List[str]]:
    """Group commits by category."""
    categorized = defaultdict(list)

    for commit in commits:
        # Parse subject line
        result = parse_commit_line(commit["subject"])
        if result:
            category, description = result
            categorized[category].append(description)

        # Parse body lines
        if commit.get("body"):
            for line in commit["body"].split("\n"):
                result = parse_commit_line(line)
                if result:
                    category, description = result
                    categorized[category].append(description)

    return dict(categorized)


def format_changelog_entry(
    version: str, date: str, categories: Dict[str, List[str]]
) -> str:
    """Format a single changelog entry according to Factorio's requirements."""
    lines = []

    lines.append("-" * 99)

    # Version line (no indentation)
    lines.append(f"Version: {version}")

    # Date line (optional, no indentation)
    if date:
        # Parse and format date
        try:
            dt = datetime.fromisoformat(date.split()[0])
            formatted_date = dt.strftime("%d.%m.%Y")
            lines.append(f"Date: {formatted_date}")
        except (ValueError, IndexError):
            pass

    # Add an empty line before categories
    lines.append("")

    # Define category order (official categories first)
    category_order = CATEGORY_MAP.values()

    # Sort categories according to defined order
    sorted_categories = []
    for cat in category_order:
        if cat in categories:
            sorted_categories.append(cat)

    # Add any categories not in the predefined order
    for cat in categories:
        if cat not in sorted_categories:
            sorted_categories.append(cat)

    # Add categories and their entries
    for category in sorted_categories:
        entries = categories[category]

        # Category line: 2 spaces indent, ends with colon
        lines.append(f"  {category}:")

        # Entry lines: 4 spaces indent, starts with "- "
        for entry in entries:
            # Wrap long lines
            words = entry.split()
            current_line = []
            current_length = 0
            is_first_line = True

            for word in words:
                word_length = len(word) + 1  # +1 for space

                if not current_line:
                    # First word on the line
                    current_line.append(word)
                    if is_first_line:
                        current_length = 6 + len(word)  # "    - " + word
                    else:
                        current_length = 6 + len(word)  # "      " + word (continuation)
                elif current_length + word_length <= 80:
                    # Add word to current line
                    current_line.append(word)
                    current_length += word_length
                else:
                    # Write current line and start a new one
                    if is_first_line:
                        lines.append(f"    - {' '.join(current_line)}")
                        is_first_line = False
                    else:
                        lines.append(f"      {' '.join(current_line)}")
                    current_line = [word]
                    current_length = 6 + len(word)

            # Write the last line
            if current_line:
                if is_first_line:
                    lines.append(f"    - {' '.join(current_line)}")
                else:
                    lines.append(f"      {' '.join(current_line)}")

    return "\n".join(lines)


def generate_changelog(output_file: str = "changelog.txt"):
    """Generate the complete changelog file."""
    print("Generating changelog...")

    # Get all tags
    tags = get_tags()

    if not tags:
        print("No tags found in repository. Please create tags for your releases.")
        sys.exit(1)

    changelog_entries = []

    # Process each tag (starting from newest)
    for i, (tag, tag_date) in enumerate(tags):
        print(f"Processing {tag}...")

        # Get version number from tag (remove 'v' prefix if present)
        version = tag.lstrip("v")

        # Get commits since previous tag (or from beginning)
        if i < len(tags) - 1:
            previous_tag = tags[i + 1][0]
            commits = get_commits_between(previous_tag, tag)
        else:
            # First tag - get all commits up to this tag from beginning
            output = run_git_command(["log", "--format=%H", tag])
            if output:
                commit_hashes = output.split("\n")
                commits = []
                for commit_hash in commit_hashes:
                    if not commit_hash:
                        continue
                    subject = run_git_command(["log", "-1", "--format=%s", commit_hash])
                    body = run_git_command(["log", "-1", "--format=%b", commit_hash])
                    date = run_git_command(["log", "-1", "--format=%ai", commit_hash])
                    commits.append(
                        {
                            "hash": commit_hash,
                            "subject": subject,
                            "body": body,
                            "date": date,
                        }
                    )
            else:
                commits = []

        if commits:
            # Categorize commits
            categories = categorize_commits(commits)

            # Format changelog entry
            entry = format_changelog_entry(version, tag_date, categories)
            changelog_entries.append(entry)

    # Check for unreleased changes (commits after latest tag)
    if tags:
        latest_tag = tags[0][0]
        unreleased_commits = get_commits_between(latest_tag)

        if unreleased_commits:
            print("Found unreleased changes...")
            categories = categorize_commits(unreleased_commits)
            current_date = datetime.now().isoformat()
            entry = format_changelog_entry("Unreleased", current_date, categories)
            changelog_entries.insert(0, entry)

    # Write changelog file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(changelog_entries))
        # Ensure file ends with a newline
        if not changelog_entries[-1].endswith("\n"):
            f.write("\n")

    print(f"Changelog generated successfully: {output_file}")


def create_release_commit(changelog_file: str, info_json_path: str, tag_version: str):
    """Create a commit with changelog and info.json changes, then move the tag to this commit."""
    # Stage the files
    run_git_command(["add", changelog_file, info_json_path])

    # Create commit with release message
    commit_message = f"release: {tag_version}"
    run_git_command(["commit", "--message", commit_message])

    # Move the tag to the new commit (HEAD)
    run_git_command(["tag", "--force", tag_version])

    print(f"Created commit: {commit_message}")
    print(f"Moved tag {tag_version} to HEAD")


def update_info_json_version(info_json_path: str = "info.json"):
    """Update the version field in info.json with the latest tag version."""
    # Get the latest tag
    tags = get_tags()
    if not tags:
        print("No tags found in repository. Cannot update version.", file=sys.stderr)
        return False

    latest_tag = tags[0][0]
    # Remove 'v' prefix if present
    version = latest_tag.lstrip("v")

    try:
        # Read info.json
        with open(info_json_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        # Update version
        old_version = info.get("version", "unknown")
        info["version"] = version

        # Write back to file with prettier-style formatting
        with open(info_json_path, "w", encoding="utf-8") as f:
            formatted_json = format_json_prettier(info)
            f.write(formatted_json)
            f.write("\n")  # Add trailing newline

        print(f"Updated {info_json_path}: {old_version} -> {version}")
        return True

    except FileNotFoundError:
        print(f"Error: {info_json_path} not found", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {info_json_path}: {e}", file=sys.stderr)
        return False
    except (OSError, PermissionError, UnicodeDecodeError, UnicodeEncodeError) as e:
        print(f"Error updating {info_json_path}: {e}", file=sys.stderr)
        return False


def main():
    """Script entry point."""

    parser = argparse.ArgumentParser(
        description="Generate Factorio-style changelog from git history"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="changelog.txt",
        help="Output file path (default: changelog.txt)",
    )
    parser.add_argument(
        "-b",
        "--bump",
        action="store_true",
        help="Update the version field in info.json to match the latest tag",
    )
    parser.add_argument(
        "-c",
        "--commit",
        action="store_true",
        help="Create a release commit with info.json and changelog changes (requires --bump)",
    )

    args = parser.parse_args()

    # Validate --commit requires --bump
    if args.commit and not args.bump:
        print("Error: --commit can only be used with --bump", file=sys.stderr)
        sys.exit(1)

    # Check working tree is clean if --commit is used
    if args.commit:
        if is_working_tree_dirty():
            print(
                "Error: Working tree is not clean. Commit or stash changes before using --commit",
                file=sys.stderr,
            )
            sys.exit(1)

    generate_changelog(args.output)

    if args.bump:
        success = update_info_json_version()
        if not success and args.commit:
            print("Error: Failed to update info.json, skipping commit", file=sys.stderr)
            sys.exit(1)

    if args.commit:
        # Get latest tag for commit message
        tags = get_tags()
        if tags:
            latest_tag = tags[0][0]
            create_release_commit(args.output, "info.json", latest_tag)


if __name__ == "__main__":
    main()

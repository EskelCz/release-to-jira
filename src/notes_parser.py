import os
import re

PROJECT = os.environ["INPUT_JIRA_PROJECT"]
ISSUE_PATTERN = rf"{PROJECT}-[0-9]+"
CHANGES_SECTION = "What's Changed"
COMMITS_SECTION = "Commits"


def _get_section(md_content, section_title):
    return md_content.split(f"## {section_title}\n", 1)[1].split("\n\n", 1)[0]


def _parse_changelist(content):
    items = []
    for line in content.split("\n"):
        # Expect lines like:
        # - Some PR title by @author in https://github.com/owner/repo/pull/123
        # - <sha> - Commit message by @author in https://github.com/owner/repo/commit/<sha>
        # - <sha>: Commit message
        if not line.strip().startswith("- "):
            continue
        raw = line[2:]

        # Try PR-style first
        try:
            pr_title, tail = raw.split(" by @", 1)
            author, pr_link = tail.split(" in ", 1)
            items.append(
                {
                    "title": pr_title,
                    "author": author,
                    "link": pr_link,
                }
            )
            continue
        except Exception:
            pass

        # Fallback: treat as commit-style; strip leading sha and separators to get message
        msg = re.sub(r"^[0-9a-fA-F]{7,}\s*[:\-]\s*", "", raw).strip()
        if not msg:
            # If stripping didn't help, just use the raw line so we can still search for keys
            msg = raw
        items.append({"title": msg})
    return items


def extract_changes():
    with open("notes.md", "r") as f:
        content = f.read()

    items = []

    for section in (CHANGES_SECTION, COMMITS_SECTION):
        marker = f"## {section}\n"
        if marker in content:
            try:
                section_content = _get_section(content, section)
                items.extend(_parse_changelist(section_content))
            except Exception as ex:
                print("failed to parse section", section, ex)

    return items


def extract_issue_id(change):
    matches = re.findall(ISSUE_PATTERN, change)
    if not matches:
        return None
    return matches[0]

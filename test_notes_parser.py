#!/usr/bin/env python3
"""Test notes_parser module"""
import os
import sys
import tempfile

# Set environment variable before importing the module
os.environ["INPUT_JIRA_PROJECT"] = "TEST"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from notes_parser import extract_changes, extract_issue_id  # noqa: E402


def test_pr_style_parsing():
    """Test parsing PR-style lines from What's Changed section"""
    content = """## What's Changed

- TEST-123 Fix login bug by @alice in https://github.com/org/repo/pull/1
- TEST-456 Add new feature by @bob in https://github.com/org/repo/pull/2

**Full Changelog**: https://github.com/org/repo/compare/v1.0.0...v1.0.1
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='.') as f:
        f.write(content)
        f.flush()
        temp_name = f.name

    try:
        # Rename to notes.md
        os.rename(temp_name, 'notes.md')

        changes = extract_changes()
        assert len(changes) == 2, f"Expected 2 changes, got {len(changes)}"

        # Check first PR
        assert changes[0]["title"] == "TEST-123 Fix login bug"
        assert changes[0]["author"] == "alice"
        assert changes[0]["link"] == "https://github.com/org/repo/pull/1"

        # Check second PR
        assert changes[1]["title"] == "TEST-456 Add new feature"
        assert changes[1]["author"] == "bob"

        # Extract issue IDs
        issue1 = extract_issue_id(changes[0]["title"])
        issue2 = extract_issue_id(changes[1]["title"])
        assert issue1 == "TEST-123"
        assert issue2 == "TEST-456"

        print("✓ test_pr_style_parsing passed")
    finally:
        if os.path.exists('notes.md'):
            os.remove('notes.md')


def test_commit_style_parsing():
    """Test parsing commit-style lines from Commits section"""
    content = """## Commits

- 1234567 - TEST-789 Update documentation
- abcdef0: TEST-999 Fix typo in README

**Full Changelog**: https://github.com/org/repo/compare/v1.0.0...v1.0.1
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='.') as f:
        f.write(content)
        f.flush()
        temp_name = f.name

    try:
        os.rename(temp_name, 'notes.md')

        changes = extract_changes()
        assert len(changes) == 2, f"Expected 2 changes, got {len(changes)}"

        # Check that commit messages are extracted (without SHA prefix)
        assert "TEST-789" in changes[0]["title"]
        assert "TEST-999" in changes[1]["title"]

        # Extract issue IDs
        issue1 = extract_issue_id(changes[0]["title"])
        issue2 = extract_issue_id(changes[1]["title"])
        assert issue1 == "TEST-789"
        assert issue2 == "TEST-999"

        print("✓ test_commit_style_parsing passed")
    finally:
        if os.path.exists('notes.md'):
            os.remove('notes.md')


def test_mixed_prs_and_commits():
    """Test parsing both PRs and commits together"""
    content = """## What's Changed

- TEST-100 Feature A by @user1 in https://github.com/org/repo/pull/10
- TEST-200 Feature B by @user2 in https://github.com/org/repo/pull/20

## Commits

- abc1234 - TEST-300 Hotfix for issue
- def5678: TEST-400 Another commit

**Full Changelog**: https://github.com/org/repo/compare/v1.0.0...v1.0.1
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='.') as f:
        f.write(content)
        f.flush()
        temp_name = f.name

    try:
        os.rename(temp_name, 'notes.md')

        changes = extract_changes()
        assert len(changes) == 4, f"Expected 4 changes, got {len(changes)}"

        # Extract all issue IDs
        issue_ids = [extract_issue_id(change["title"]) for change in changes]
        issue_ids = [id for id in issue_ids if id]  # Filter out None

        assert len(issue_ids) == 4
        assert "TEST-100" in issue_ids
        assert "TEST-200" in issue_ids
        assert "TEST-300" in issue_ids
        assert "TEST-400" in issue_ids

        print("✓ test_mixed_prs_and_commits passed")
    finally:
        if os.path.exists('notes.md'):
            os.remove('notes.md')


def test_deduplication():
    """Test that duplicate issue IDs are handled properly"""
    content = """## What's Changed

- TEST-500 Initial fix by @user1 in https://github.com/org/repo/pull/1

## Commits

- abc1234 - TEST-500 Follow-up commit for same issue
- def5678: TEST-600 Different issue

**Full Changelog**: https://github.com/org/repo/compare/v1.0.0...v1.0.1
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='.') as f:
        f.write(content)
        f.flush()
        temp_name = f.name

    try:
        os.rename(temp_name, 'notes.md')

        changes = extract_changes()
        assert len(changes) == 3, f"Expected 3 changes, got {len(changes)}"

        # Extract issue IDs (simulating what main.py does)
        issue_ids = []
        seen = set()
        for change in changes:
            issue_id = extract_issue_id(change["title"])
            if issue_id and issue_id not in seen:
                seen.add(issue_id)
                issue_ids.append(issue_id)

        # Should have only 2 unique issue IDs
        assert len(issue_ids) == 2, f"Expected 2 unique issues, got {len(issue_ids)}"
        assert "TEST-500" in issue_ids
        assert "TEST-600" in issue_ids

        print("✓ test_deduplication passed")
    finally:
        if os.path.exists('notes.md'):
            os.remove('notes.md')


def test_no_issue_key():
    """Test lines without JIRA issue keys"""
    content = """## What's Changed

- Some change without issue key by @user1 in https://github.com/org/repo/pull/1

## Commits

- abc1234 - Another change without key

**Full Changelog**: https://github.com/org/repo/compare/v1.0.0...v1.0.1
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='.') as f:
        f.write(content)
        f.flush()
        temp_name = f.name

    try:
        os.rename(temp_name, 'notes.md')

        changes = extract_changes()
        assert len(changes) == 2, f"Expected 2 changes, got {len(changes)}"

        # Extract issue IDs - should be None for both
        issue1 = extract_issue_id(changes[0]["title"])
        issue2 = extract_issue_id(changes[1]["title"])
        assert issue1 is None
        assert issue2 is None

        print("✓ test_no_issue_key passed")
    finally:
        if os.path.exists('notes.md'):
            os.remove('notes.md')


if __name__ == "__main__":
    print("Running notes_parser tests...")
    test_pr_style_parsing()
    test_commit_style_parsing()
    test_mixed_prs_and_commits()
    test_deduplication()
    test_no_issue_key()
    print("\n✅ All tests passed!")

import os
from pprint import pprint

from jira_api import add_release_to_issue, get_or_create_release, mark_version_as_released
from notes_parser import extract_changes, extract_issue_id

release_name = os.environ["GITHUB_REF_NAME"]
release = get_or_create_release(release_name)
print("JIRA Release:")
pprint(release)

# Mark version as released if requested
mark_released = os.environ.get("INPUT_JIRA_MARK_RELEASED", "false").lower() == "true"
if mark_released:
    print(f"Marking version {release['name']} as released...")
    release = mark_version_as_released(release["id"])
    print("Version marked as released")

changes = extract_changes()
print("Parsed release items (PRs and commits):")
pprint(changes)

# Collect unique issue IDs from all parsed items
issue_ids = []
seen = set()
for change in changes:
    issue_id = extract_issue_id(change["title"])
    if not issue_id:
        print("No issue id:", change["title"])
        continue
    if issue_id not in seen:
        seen.add(issue_id)
        issue_ids.append(issue_id)

print("Issues to update:")
pprint(issue_ids)

for issue_id in issue_ids:
    print("Updating", issue_id)
    add_release_to_issue(release_name, issue_id)

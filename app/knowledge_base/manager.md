# Manager

Managers can do everything in `common.md` and `team-member.md` (they also submit their own weekly reports),
plus the following.

## Review Queue (`/review`)

- Lists reports from your team, filterable by status (defaults to "Submitted") and by project.
- Click a row to open that report for review.

## Reviewing a report (`/review/:id`)

- Opens the full report detail (tasks, blockers, achievements, hours).
- If the report is still in **Submitted** status, you get two actions at the bottom of the page:
  - **Approve** — marks the report **Approved**. Final; the team member can no longer edit it.
  - **Request Changes** — opens a dialog where you must write a comment (at least 3 characters) explaining
    what needs to change. Submitting moves the report to **NeedsCorrection** and shows your comment to the
    team member; they can then edit and resubmit.
- Reports that are already Approved/NeedsCorrection/Draft don't show these actions — you can only act on
  reports that are currently Submitted.

## Team Dashboard (`/dashboard`)

- Gives a team-wide view of weekly reports: a filter bar (week range, team member, project, status), a
  submission-status tracker showing who has/hasn't submitted for the selected week, a table of team reports,
  and a section that compares tasks/blockers/achievements across team members.
- Click through to a member's detail page (`/dashboard/members/:id`) for their individual profile/history.

## Projects (`/projects`)

- **Create a project**: click "Add Project", type a name (required) and an optional description, toggle
  Active/Inactive, then click the checkmark to save.
- **Edit a project**: click the pencil icon on its row, change name/description/active status, and click the
  checkmark to save (or the X to cancel).
- **Delete a project**: click the trash icon, then confirm in the dialog. This cannot be undone.
- **Assign or remove members**: click the people icon on a project's row (or next to it while editing) to
  open "Manage members". From there:
  - Under "Add members", check one or more users not yet on the project, click "Assign selected", review the
    list, then "Confirm assign" — members can be added in bulk, not just one at a time.
  - Under "Current members", check one or more existing members, click "Remove selected", review the list,
    then "Confirm remove" — also supports bulk removal.

## AI Assistant page (`/assistant`)

This is different from the "Help" bubble described in `common.md` — it has access to live report data via
tool calls, and is Manager/Admin only.

- **Chat tab**: ask natural-language questions about your team's reports (e.g. "what blockers came up last
  week for Project X?"). Conversation history is kept for the session.
- **Weekly Summary tab**: generates a written summary of a given week's reports, optionally scoped to one
  project.

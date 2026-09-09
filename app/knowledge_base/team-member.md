# TeamMember

Everything a TeamMember can do, in addition to `common.md`.

## Viewing your report history (`/reports`)

- "My Reports" lists every weekly report you've ever created, newest logic aside — filterable by status and
  by project using the two dropdowns above the table.
- Click any row (or "View") to open that report's details.

## Creating a weekly report

1. Go to "My Reports" and click "New Report".
2. Pick the **Project / category** the report is for, and the **week start/end dates** (these default to the
   current week and can't be changed once the report has been saved — pick carefully).
3. Fill in:
   - **Tasks** — add a row per task with a name, priority (Low/Medium/High/Critical), planned vs. actual
     percent complete, status (Not Started/In Progress/Completed/Blocked/Deferred), planned vs. actual hours,
     and an optional output/deliverable (e.g. a PR link).
   - **Blockers / challenges** — add a description per blocker; you can flag one as the "Key issue" and mark
     any as "Resolved". Only one blocker can be the key issue at a time.
   - **Achievements** — add a description per achievement; you can flag one as the "Key achievement" (also
     mutually exclusive).
   - **Hours by task type** (optional) — log hours against categories like Development, Testing, Meetings,
     etc.; a chart updates live as you enter them.
4. Click **"Save as Draft"** any time to save without submitting — you can come back and keep editing.
5. When it's ready, click **"Submit"**. This locks the report (it moves to `Submitted`) and sends it to your
   manager's Review Queue. Submit is disabled until the form is valid.

## Editing a report

- You can only edit a report while it's in **Draft** or **NeedsCorrection** status. Once submitted or
  approved, the form becomes read-only.
- To edit, open the report from "My Reports" — if it's editable, the form appears with your saved values, and
  the Week/Project fields are locked (you can't change the week or project of an existing report).

## Handling "Needs Correction"

- If your manager requests changes, the report's status becomes **NeedsCorrection** and you'll see their
  comment at the top of the report form when you open it.
- Make the requested changes and click **Submit** again — this re-submits the same report for review.

## Reviews on your report

- Open any of your reports to see its review history (who reviewed it, when, and any comments), shown at the
  bottom of the report detail view.

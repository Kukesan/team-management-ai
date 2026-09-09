# Getting Started

- Log in with your company email and password. Use "Forgot password" on the login
  screen if you're locked out, or ask an Admin to reset it.
- The left-hand navigation only shows the sections your role has access to -- if
  you don't see something described here, your role likely doesn't have it.
- Weeks in this app always start on Monday ("Week Start Date"). Reports, summaries,
  and dashboards are grouped by week.
# Common — all roles

Applies to every signed-in user: TeamMember, Manager, and Admin.

## Signing in

- Go to `/login` and enter your email and password.
- New accounts are created by an Admin inviting you (see `admin.md`) — there's a self-serve `/register` page
  too, but normal onboarding is via invite.
- If your session expires or your token becomes invalid, the app automatically signs you out and returns you
  to the login page.

## Navigating the app

- After login you land on your home page, which depends on your role.
- The left/top navigation only shows the sections your role can access. TeamMembers see "My Reports" and
  "Profile"; Managers additionally see "Review Queue", "Team Dashboard", "Projects", and "AI Assistant";
  Admins additionally see "Users".
- If you try to open a page your role doesn't allow, you'll land on a "Forbidden" page.

## Your profile (`/profile`)

- **Update your name**: go to Profile → "Profile information", edit "Full name", click "Save changes". Email
  is not editable from here.
- **Change your password**: go to Profile → "Change password", enter your current password, then a new
  password twice, and click "Update password".

## Report statuses

Every weekly report moves through these statuses:

- **Draft** — being written, not yet submitted, still fully editable by its owner.
- **Submitted** — sent for review, waiting in a manager's Review Queue. No longer editable by the owner.
- **NeedsCorrection** — a manager asked for changes; the report becomes editable again for its owner so they
  can fix it and resubmit.
- **Approved** — a manager signed off; final, no longer editable.

## The "Help" chat bubble

- The floating "?" button in the bottom-right corner (visible on every page, every role) is this how-to
  assistant. It only answers questions about how to use the app — it does not have access to your reports or
  any other live data. For questions about actual report content or team data, Managers/Admins should use the
  "AI Assistant" page instead (see `manager.md`).

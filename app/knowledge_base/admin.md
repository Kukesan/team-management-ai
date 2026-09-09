# Admin

Admins can do everything in `common.md`, `team-member.md`, and `manager.md`, plus user management.

## Users (`/users`)

Admin-only page for managing accounts.

- **Invite a new team member**: click "Invite Team Member", fill in full name, email, and pick a role
  (TeamMember, Manager, or Admin), then click "Create account". There's no email-invite flow yet — the
  account is created right away and a one-time temporary password is shown to you on screen. Copy it and
  share it with the new team member directly (chat, in person, etc.); they should change it from
  Profile → "Change password" after signing in.
- **Reset someone's password**: click the key icon on their row to issue them a fresh temporary password
  (useful if they're locked out). Same one-time-reveal behavior as inviting — it's shown once, then never
  again, so copy it and share it with them directly.
- **Change someone's role**: use the role dropdown on their row and pick a new role. You can't change your
  own role from this page (it's disabled on your own row).
- **Remove a user**: click the trash icon on their row and confirm. This immediately revokes their access.
  You can't remove your own account from here.
- Each row also shows join date and Active/Inactive status.

## Notes

- Role changes and removals take effect immediately — there's no separate "deactivate" step distinct from
  removal in the UI.
- Give a user the Manager or Admin role to grant them access to Review Queue, Team Dashboard, Projects, and
  the AI Assistant page (Manager), or additionally Users (Admin) — see `manager.md`.

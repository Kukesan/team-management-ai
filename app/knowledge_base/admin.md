# Admin

Admins can do everything in `common.md`, `team-member.md`, and `manager.md`, plus user management.

## Users (`/users`)

Admin-only page for managing accounts.

- **Invite a new team member**: click "Invite Team Member", fill in full name, email, and pick a role
  (TeamMember, Manager, or Admin), then click "Send invite". They receive an email invitation to set up their
  account.
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
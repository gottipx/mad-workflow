# Example board flow

1. Intake item enters Backlog.
2. `workstream-agent` creates or requests a compact specification and task candidates.
3. `architect-agent` defines contracts, architecture constraints, and design constraints.
4. `workstream-agent` creates task contracts and isolated workspaces.
5. `coding-agent` executes assigned tasks by scope.
6. `qa-agent` reviews and tests each completed branch.
7. `release-agent` merges passing branches into an integration branch.
8. Final gates pass.
9. Human reviewer approves merge to main.

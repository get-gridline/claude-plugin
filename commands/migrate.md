---
description: Plan and stage a migration off direct provider SDK calls onto Gridline
---

Run the `gridline-migrate` skill.

Start with the `gridline-repo-auditor` subagent so the plan is grounded in the actual call sites.
Propose before you edit, and stage the work so the reversible part lands first.

$ARGUMENTS may narrow the scope to a directory or a service. With no argument, audit the whole
repository.

---
description: Follow one Gridline request end to end by its request_id
---

Run the `gridline-trace` skill for the request id in $ARGUMENTS.

If $ARGUMENTS is empty, ask for a `request_id` and mention it is returned on every response as
`X-Request-Id`. Do not guess one.

Remember a failover writes two attempts under one id, so report every attempt and its own cost —
"the request cost $X" is wrong when the first hop failed and was billed.

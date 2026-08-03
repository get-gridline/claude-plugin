# Harnesses and surfaces

A **harness** is everything an agent can reach for. Each surface names a connection.

```
create_harness(id="support-tools")
attach_memory(harness="support-tools", connection="mem0-prod")
attach_sandbox(harness="support-tools", connection="e2b-prod", lifetime_seconds=900)
attach_skills(harness="support-tools", connection="openai-skills", skills=["pdf"])
add_mcp_server(harness="support-tools", connection="wiki", tools=["search", "get_page"])
```

## The surfaces

| Surface | What it gives the agent |
|---|---|
| memory | Recall across sessions |
| skills | Provider-hosted skills |
| sandbox | A filesystem and a shell |
| MCP servers | Your own tools, including through a tunnel |

## Sharing is the point

Two agents pointing at the same harness present the **same tool list** to the provider, so they
share one cached prefix. Two near-identical harnesses do not — they are two prefixes, each paid for
separately. When you find yourself creating a second harness that differs only slightly, check
whether the difference belongs in an assignment instead.

The cache order is `tools → system → messages`. Anything that changes the tool list invalidates the
whole cached prefix, which is why the tool set is a property of the harness rather than something
varied per request.

## What may be overridden per request

Only the MCP tool list. A request may narrow or replace `tools` for one turn; it may not swap the
memory store or the sandbox. Everything else is fixed by the session's harness.

The reason is caching again: a request that could change any surface could invalidate a prefix the
conversation has already paid for.

## What does not belong in a harness

Which store, or whose data — that is an assignment. See `assignment-and-tenancy.md`.

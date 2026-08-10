# Harnesses and surfaces

A **harness** is everything an agent can reach for. Each surface names a connection.

```
create_harness(project, harness_id="support-tools")
attach_memory(project, harness_id="support-tools", connection="mem0-prod")
attach_sandbox(project, harness_id="support-tools", connection="e2b-prod", lifetime_seconds=900)
attach_skills(project, harness_id="support-tools", connection="openai-skills", skills=["pdf"])
add_mcp_server(project, harness_id="support-tools", connection="wiki", tools=[
    {"name": "search", "description": "Full text search over the wiki"},
    {"name": "get_page", "description": "Fetch one page by title"},
])
```

## The surfaces

| Surface | What it gives the agent |
|---|---|
| memory | Recall across sessions |
| skills | Provider-hosted skills |
| sandbox | A filesystem and a shell |
| MCP servers | Your own tools, including through a tunnel |

## Scoping the skills a harness can see

A skills workspace belongs to the whole provider account. If prod and staging — or a project per
client — resolve to one Anthropic or OpenAI account, every one of them finds every skill in the
account, including ones somebody else put there.

`skills=` narrows it. An entry is a name, or a prefix ending in `*`:

```
attach_skills(project, harness_id="acme", connection="openai-skills", skills=["acme-*", "vat-return"])
```

Prefer the prefix. A list of names stops covering a skill created after you wrote it, and nobody
notices — where `acme-*` keeps working as the account grows.

Nothing outside the scope can be searched **or** loaded, and a skill outside it looks to the model
exactly like one that does not exist. Omit `skills=` and the agent sees the whole workspace.

The names are not checked when you save: skills live in your provider account and are created
outside Gridline, so a scope that matches nothing is accepted and `search_skills` tells the model
that its scope matched nothing rather than that the account is empty.

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

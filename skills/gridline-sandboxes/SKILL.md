---
name: gridline-sandboxes
description: Give a Gridline agent a filesystem and a shell through a sandbox provider, and control its network access and lifetime. Use when an agent needs to run code, write files, or when asked about sandboxes, E2B, Modal or Daytona.
---

# Sandboxes

Cite `gridline-primitives`.

## Attaching one

```
create_connection(project, connection_id="e2b-prod", kind="e2b", credential_ref="vault://…")
attach_sandbox(project, harness_id="…", connection="e2b-prod", lifetime_seconds=900,
               network="allowlist", allowed_domains=["pypi.org"])
```

The provider runs on **your** account and your bill. `browse_providers` is the live answer on which
exist and what each is for — and it says which are verified and which are not, which is worth passing
on rather than presenting them all as equivalent.

## A sandbox belongs to a conversation

The binding is the conversation, and it is **not something the model can name**. There is no `session`
parameter for a model to set, no `start_sandbox` or `stop_sandbox` offered, and a `session` appearing in
tool arguments is **ignored rather than honoured**.

Worth explaining if somebody asks why an agent cannot manage its own sandbox. A model that could open
a second sandbox will sometimes do so despite being told not to, then rebuild its working files from
the conversation — and the answer looks correct while the original filesystem is gone. Making the
binding something the model cannot address removes the possibility rather than relying on the
instruction.

## Network

- `network: "none"` — no egress. The right default for running untrusted output.
- `network: "allowlist"` with `allowed_domains` — the usual choice. `pypi.org` to install, and nothing
  else.
- Full egress — only when there is a reason, and say what it is.

An agent that can reach anything is an agent that can exfiltrate anything it has been given.

## Lifetime

`lifetime_seconds` bounds how long the sandbox lives. When it expires, **a resumed conversation gets a
fresh one** — the transcript survives, the filesystem does not. So anything meant to persist has to be
written somewhere that outlives the sandbox, and a workflow that assumes its files are still there
after a gap will silently start from empty.

Set it to the length of the work, not the length of the conversation.

## Modal offers no tools

If the user asks: a Modal connection provides sandboxed execution but exposes no tool surface, so it is
not the choice for an agent that should call sandbox tools itself. `browse_providers` is the current
authority.

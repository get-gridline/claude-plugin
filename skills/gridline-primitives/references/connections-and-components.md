# Connections and components

A **connection** is one provider account. A **component** is what kind of thing it is, from the
catalogue.

```
create_connection(id="e2b-prod",  component="e2b",  credential_ref="vault://…")
create_connection(id="mem0-prod", component="mem0", credential_ref="vault://…")
create_connection(id="wiki", component="mcp_http", base_url="https://wiki.internal/mcp")
```

## Naming a connection is the whole action

Point a harness at `e2b-prod` and its tools appear. You never enumerate them — the catalogue knows
what an E2B connection offers, and it stays correct as the provider changes.

**The exception is your own MCP server**, which declares its own tools. Gridline cannot know what
your wiki exposes, so `add_mcp_server` takes a tool list. (For a tunnelled server, `show_tunnel`
reports what the client actually found, which is better than typing them.)

## Finding components

`browse_providers` returns every component with prose about what it is for and when to choose it —
written for exactly the question "which memory provider should I use". Use it rather than guessing
from a name.

`browse_models` returns models with their capabilities, and takes a capability filter.

Both are **live**. Prefer them over any list written down.

## base_url

Only for components where the address is part of the account — your own MCP servers, a gateway, a
compatibility shim. For a first-party provider, leave it alone; Gridline knows where the provider
is.

A connection carrying a `credential_ref` may only reach the address its catalogue entry declares.
This stops a configuration change from redirecting your provider key somewhere else.

## Tunnelled connections

`base_url` of `tunnel://<tunnel>/<server>` reaches a server inside your own network. Such a
connection **may not carry a `credential_ref`** — a bearer token for your own server stays on your
own tunnel client and never reaches Gridline. See `tunnels.md`.

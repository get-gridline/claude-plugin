---
name: gridline-tunnel
description: Let a Gridline agent reach an MCP server inside your own network — a wiki, Jira, an internal API — without exposing it to the internet. Use for questions about tunnels, reaching internal or private MCP servers, firewalls, or when a tool server is not reachable from Gridline.
---

# Reaching a server inside your own network

Cite `gridline-primitives` and `references/tunnels.md`.

## Lead with what it does not require

People expect this to be the hard part. It is not, and saying so early changes how the rest is read:

- Nothing inbound. No public listener, no inbound firewall rule, no DNS record, no certificate.
- Egress to exactly two destinations: the Gridline broker, and your own named servers.
- **Gridline is never told the address of any of your servers.** The wire format carries a *name*;
  your client resolves it against a map only it holds. There is no field an address could go in.

## Flow

**1. Create the tunnel.**

```
create_tunnel(name="acme-internal", servers=["wiki", "jira"])
```

This also writes, into every project in the organisation (or only the pinned one), a connection whose
id **is** the server name and whose `base_url` is `tunnel://acme-internal/wiki`. Existing ids are
skipped, never overwritten — so a re-run is safe.

Names: tunnel names are unique deployment-wide, server names unique per organisation, and a create
**refuses a taken name** rather than overwriting it.

**2. Issue the credential — send them to the dashboard.**

Two secrets, shown once. **The default is to tell the user to generate them in the Gridline
dashboard.** The MCP tool deliberately does not return them.

The API call `POST /organisations/{org}/tunnels/{tunnel}/keys` does return both. Only offer it after
saying plainly that it will put two live credentials into this conversation, and therefore into the
transcript and anywhere it is stored. If they choose it anyway, say afterwards what is now in the
transcript and that rotating is the fix.

**3. Run the client.** One container, or a systemd unit. Give them the variables:

```
GRIDLINE_TUNNEL_URL=https://tunnel.get-gridline.dev   # an ORIGIN, no path
GRIDLINE_TUNNEL_NAME=acme-internal
GRIDLINE_KEY=…
GRIDLINE_BUNDLE_KEY=…                                  # exactly 32 bytes
GRIDLINE_SERVERS=wiki=http://wiki.internal:8000/mcp
jira=https://jira.internal/mcp
```

Plus `GRIDLINE_KEY_SLOT` if not slot 1, and **`GRIDLINE_TUNNEL_PROJECT` whenever the tunnel is
pinned**. Say this one unprompted every time: omit it on a pinned tunnel and every envelope fails to
open, with an error that names a key slot and never mentions pins. It looks like a bad credential and
it is not.

**4. Wire the harness.**

```
add_mcp_server(project, harness=…, connection="wiki", tools=[…])
```

`show_tunnel` reports what clients actually found, server by server, with tool names — read the tool
list from there rather than asking the user to type it.

**5. Check, then prove it.** `check(project)`, then run one real turn that uses a tunnelled tool and
assert `tools_degraded` is false. `show_tunnel` reporting `usable` does **not** mean a client is
connected right now; a call is the only thing that knows.

## Rules to state, because each one bites silently

- A tunnelled connection **may not carry a `credential_ref`**. A bearer for your own server is
  `GRIDLINE_SERVER_TOKEN_<NAME>` on your own client and never leaves your network.
- **A turn using a tunnelled tool does not stream.**
- A **pin** narrows a tunnel to one project inside its own organisation. It is not a way to reach
  across organisations.
- **Two credential slots** so rotation needs no coordinated restart: issue into the free slot, move
  clients at their own pace, retire the old. There is no free slot until one is retired, and retiring
  the **last** leaves the tunnel registered and carrying nothing — the broker then refuses calls
  until a new credential exists.
- `tools/call` is **never retried**. Replaying one after a timeout is how an agent files two tickets.

## In Kubernetes

Two things are almost always the bug:

- **`ADMIN_ADDR` must be `:8097`.** The default binds loopback, which a kubelet probe cannot reach —
  so a perfectly healthy client never becomes ready.
- **Readiness needs about 40 seconds of grace.** The client reports ready only after its first poll
  *returns*, and on a quiet tunnel that poll parks for the broker's full window. Use `/healthz` for
  liveness and `/readyz` with a generous `failureThreshold`. Anything tighter makes every rollout
  look broken.

Also: `NO_PROXY` for in-cluster upstreams if `HTTPS_PROXY` is set, and every replica must resolve the
same names to the same addresses — two clients on one tunnel pointing at different upstreams is
undetectable from Gridline's side, since it is never told either address. `show_tunnel` showing two
instances reporting different tools for one server is the only signal, so check it.

## Failure map

| Symptom | Cause and fix |
|---|---|
| 401 on poll, client exits 1 | Revoked credential, wrong tunnel, or unknown key. It stops loudly rather than retrying |
| 403 | The call was not authorised for this tunnel |
| 503 *no registered key* | Issue a credential |
| 503 *no tunnel client is connected* | Immediate, not a timeout. Nothing running, or it cannot reach the broker |
| 503 *did not take the call in time* | A client is running but saturated. One call in flight per process — add replicas |
| 404 | The client restarted; the session must re-initialize. This is the documented recovery |
| 502 | The reply did not open, or the client errored |
| 504 | Gridline gave up waiting upstream |

Startup refusals name the variable: a missing required one, a bundle key that is not 32 bytes, an
empty `GRIDLINE_SERVERS`, a malformed line (a bare URL with no `name=`), or a duplicate name.

# Tunnels

A tunnel lets a Gridline agent reach an MCP server inside your own network. **You run one small
client**; it dials out and holds the connection open. Nothing inbound: no public listener, no
inbound firewall rule, no DNS record, no certificate.

## The property that makes it safe

**Gridline is never told the address of any of your servers.** The wire format carries a *name*,
which your client resolves against a map only it holds. There is no field an address could go in,
so the strongest thing that can be asked for is the name of something you configured — and a name
your client does not know is refused.

## Setting one up

```
create_tunnel(name="acme-internal", servers=["wiki", "jira"])
```

This also writes, into every project in the organisation (or just the pinned one), a connection
whose id **is** the server name and whose `base_url` is `tunnel://acme-internal/wiki`. Existing
ids are skipped, never overwritten.

Then issue a credential — **from the dashboard.** It returns two secrets, once. Then run the client:

| Variable | Notes |
|---|---|
| `GRIDLINE_TUNNEL_URL` | An **origin, no path**. The client appends the rest; a path gives a 404 loop |
| `GRIDLINE_TUNNEL_NAME` | The tunnel's name — its id everywhere |
| `GRIDLINE_KEY` | The route credential |
| `GRIDLINE_BUNDLE_KEY` | The delivery secret. Must be 32 bytes; the client refuses otherwise |
| `GRIDLINE_SERVERS` | `name=url` per line. **The only place your addresses exist** |
| `GRIDLINE_KEY_SLOT` | Only if not slot `1` |
| `GRIDLINE_TUNNEL_PROJECT` | **Required whenever the tunnel is pinned.** Omit it and every envelope fails to open, with an error that does not mention pins |

Finally point a harness at it: `add_mcp_server(harness=…, connection="wiki", tools=[…])`.

## Rules that will bite otherwise

- A tunnelled connection **may not carry a `credential_ref`**. A bearer for your own server is
  `GRIDLINE_SERVER_TOKEN_<NAME>` on your own client, and never leaves your network.
- **A turn using a tunnelled tool does not stream.** The tool loop runs on Gridline's side.
- Tunnel names are unique deployment-wide; server names unique per organisation. A create refuses a
  taken name rather than overwriting.
- A **pin** narrows a tunnel to one project inside its own organisation. It is not a way to reach
  across organisations.
- **Two credential slots** exist so rotation needs no coordinated restart — issue into the free
  slot, move clients at their own pace, then retire the old one. There is no free slot until you
  retire one, and retiring the *last* leaves the tunnel registered and carrying nothing.
- `tools/call` is **never retried**. Replaying a tool call after a timeout is how an agent files two
  tickets. `initialize`, `tools/list` and `ping` may be retried once.

## Verifying

`show_tunnel` reports whether it is `usable` and what clients have reported seeing — server by
server, with tools and timestamps, per client instance. **It does not prove a client is connected
right now.** The only way to know is a call through it, so make one.

Two clients reporting *different* tools for one server means they point at different upstreams.
Nothing else can detect that, since Gridline is never told either address.

The client also serves `/healthz` (always 200) and `/readyz` (`{"ready","tunnel","servers"}`, 503
until polling) on `ADMIN_ADDR` — local only by default.

## Failure map

| Symptom | Cause |
|---|---|
| 401 on poll, client exits 1 | Credential revoked, wrong tunnel, or unknown key |
| 403 | The call was not authorised for this tunnel |
| 503 *no registered key* | Issue a credential |
| 503 *no tunnel client is connected* | Immediate, not a timeout. Nothing is running or it cannot reach the broker |
| 503 *did not take the call in time* | A client is running but saturated |
| 404 | The client restarted; the session must re-initialize |
| 502 | The reply did not open, or the client errored |
| 504 | Gridline gave up waiting |

Startup refusals name the variable: a missing required one, a bundle key that is not 32 bytes, an
empty `GRIDLINE_SERVERS`, a malformed line, a duplicate name.

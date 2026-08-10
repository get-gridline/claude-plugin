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

Then issue a credential — **from the dashboard.** It returns one value, once. Then run the
client, which needs two things:

| Variable | Notes |
|---|---|
| `GRIDLINE_CREDENTIAL` | One value. It carries which tunnel this is, which key slot, and all three secrets — the bearer presented on every poll, the envelope secret presented to nobody, and the secret that opens per-tenant bearers and only your own client holds |
| `GRIDLINE_SERVERS` | Your servers, as JSON: `{"acme-wiki":"http://wiki.internal:8000/mcp"}`. **The only place your addresses exist.** Or `GRIDLINE_SERVERS_FILE`, a path to the same JSON — setting both is refused rather than ranked |

Everything else has a working default. `GRIDLINE_TUNNEL_URL` is only for a broker that is not
the hosted one; `GRIDLINE_TUNNEL_ID` and `GRIDLINE_PROJECT_ID` are optional and are checked
against the credential rather than believed, which turns a credential pasted from another
environment into a named refusal at startup instead of a 401 — or, for the project, instead of a
cluster quietly serving another cluster's calls.

**Server names are compared exactly** — no case folding, no character substitution — so
`acme-wiki` and `jira.eu` need nothing spelt differently anywhere else. A server wanting a bearer
takes the long form:

```json
{"acme-wiki": {"url": "http://wiki.internal:8000/mcp", "token_file": "/gridline/tokens/acme-wiki"}}
```

`token` sets it inline; `token_file` reads it from a path, which is how a mounted Secret stays its
own Secret and rotating one server's bearer touches no other server's.

Finally point a harness at it: `add_mcp_server(project, harness_id=…, connection="wiki", tools=[…])`.

## Rules that will bite otherwise

- A tunnelled connection **may not carry a `credential_ref`**. Two ways to give your own server a
  bearer, and no precedence between them:
  - A `token` (or `token_file`) beside that server in `GRIDLINE_SERVERS` — one bearer for the
    whole tunnel, and it never leaves your network.
  - A **vault entry**, chosen per turn, when each of your own customers authenticates as
    themselves. A token you store in a Gridline vault *does* leave your network — you give it to
    us. We store it sealed and never return it, and **on a tunnelled call it stays sealed until it
    reaches your own client**, so nothing on our side that carries the traffic can read it. That
    last clause is specific to the tunnel: for a server Gridline dials directly, the same entry is
    opened on our side in order to be presented.
- **A turn using a tunnelled tool does not stream.** The tool loop runs on Gridline's side.
- Tunnel names are unique deployment-wide; server names unique per organisation. A create refuses a
  taken name rather than overwriting.
- A **pin** narrows a tunnel to one project inside its own organisation. It is not a way to reach
  across organisations.
- **Two credential slots** exist so rotation needs no coordinated restart — issue into the free
  slot, move clients at their own pace, then retire the old one. The slot rides inside the
  credential, so there is no second value to keep in step. There is no free slot until you retire
  one, and retiring the *last* leaves the tunnel registered and carrying nothing.
- `tools/call` is **never retried**. Replaying a tool call after a timeout is how an agent files two
  tickets. `initialize`, `tools/list` and `ping` may be retried once.

## Verifying

`show_tunnel` reports whether it is `usable` and what clients have reported seeing — server by
server, with tools and timestamps, per client instance. **It does not prove a client is connected
right now.** The only way to know is a call through it, so make one.

Two clients reporting *different* tools for one server means they point at different upstreams.
Nothing else can detect that, since Gridline is never told either address.

The client also serves `/healthz` (always 200) and `/readyz` (503 until polling) on `ADMIN_ADDR` —
local only by default. `/readyz` reports the tunnel, how many servers it holds, and
`opens_tenant_credentials`: whether it holds the key for per-turn bearers. False is ordinary for a
tunnel with no vaulted server, and is the whole diagnosis when those calls are being refused.

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

Startup refusals name the thing to change: a missing or edited credential, a secret inside it that
is not 32 bytes, no server map at all, a name written as a URL, an address with no scheme, a
misspelt field, or a `token_file` the client cannot read. All of it at startup rather than during
somebody's turn.

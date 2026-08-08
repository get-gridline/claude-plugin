---
name: gridline-primitives
description: How Gridline is put together — agents, harnesses, connections, assignments, projects, sessions, capabilities and keys. Load this when working with Gridline configuration, when a Gridline term needs defining, or before any other Gridline skill acts, so the vocabulary is right.
---

# What Gridline is

An abstraction and tracking layer for AI agents. Your code says *what kind* of thing an agent
needs; configuration decides *which provider* serves it.

**Gridline resells no compute.** Every provider — Anthropic, OpenAI, E2B, mem0 — runs on your own
account and your own bill. Gridline routes to them, records what happened, and fails over when one
is unavailable.

## The live catalogue always wins

`browse_providers`, `browse_models` and `GET /catalogue/surfaces` are the current truth about what
exists and what it supports. **Prefer them over anything written down here or in `references/`.**
Models are added, deprecated and repriced continuously; a list in a document is a snapshot. If a
reference here disagrees with the catalogue, the catalogue is right and the reference is stale.

## The three things you configure

Named once each, and pointed at by name from then on.

**A connection** is one provider account — an E2B account, a mem0 account, one of your own MCP
servers — described by where it lives and how it is reached. Naming the connection is the whole
action: its tools appear automatically and are never listed by hand. The exception is your own MCP
server, which declares its own tools.

**A harness** is everything an agent can reach for: memory, skills, a sandbox, MCP servers — each
naming a connection.

**An agent** is an id, a system prompt, and an ordered chain of models, plus the harness it runs
with by default.

So the order is always: `create_connection` → `create_harness` and attach things to it →
`create_agent` pointing at the harness. One connection backs many harnesses; one harness serves
many agents. **That sharing is the point** — two agents reaching for the same things get the same
tool list, and therefore the same cached prefix, which is the difference between paying for a
prompt once and paying for it per agent.

Ids never change; display names are free.

## What a harness deliberately does not carry

Which store, or whose data. That is an **assignment**, chosen per session and passed at call time.
Keeping it outside the harness is what lets one harness serve hundreds of tenants instead of
becoming hundreds of near-identical harnesses — and since the harness is what is cached, folding a
tenant into it would make the most common variation in your product the most expensive one.

## A project

The unit of ownership and isolation. Agents, harnesses, connections, credentials, budgets and
transcripts all live in one. A key is usually bound to a project; a person names one.

An organisation owns projects. A person creates a project *through* their organisation.

## Two ways to integrate

**Tier one — passthrough.** Keep the Anthropic or OpenAI client you already have and change its
base URL to Gridline's. Name an agent instead of a model. You get routing, failover, cost
attribution and transcripts with no new dependency. Reversible with an environment variable.

**Tier two — the SDK.** `pip install gridline`. Needed for approvals, the unified reply shape, and
anything that wants one parsing path across providers.

Start at tier one. Most of what Gridline offers arrives without touching application logic.

## Capabilities and what a fallback may change

Every model capability has a class, and the class decides whether a fallback chain may mix it:

| Class | Examples | Rule across a chain |
|---|---|---|
| `ADDITIVE` | prompt caching, vision, reasoning effort | **May vary.** Losing one is recorded as degradation |
| `CONTRACT` | tools, streaming, structured output | **Must be the same on every hop.** A hop lacking one breaks your code |
| `STATE` | thinking blocks, reasoning items | **Refused across vendors unless that hop opts in.** Opaque conversation state cannot transfer |

The consequence people hit: extended thinking is a `STATE` capability, and Anthropic's thinking
blocks and OpenAI's reasoning items are *different* state formats — one signed, one encrypted, with
no conversion between them. **So a thinking chain with a cross-vendor fallback is refused by
default.** Set `allow_state_loss: true` on the fallback and it is taken anyway, continuing on the
dialogue alone: a worse answer during an outage rather than no answer. Off unless you ask for it, and
one-way — a conversation that fails over that way holds two vendors' turns and can never be resumed
with either one's own state again. Turning thinking off entirely (`disable: ["thinking_blocks"]`) is
the other answer, and a different decision: nothing is ever produced, so nothing is ever lost.

`degraded` means *the output may differ*, because a different model answered — or because it could
not see the conversation's reasoning. It deliberately does not mean "lost a capability": losing
prompt caching costs money but produces identical output, and *which* capability went is reported
separately as `lost_capabilities`. Conflating them would make the most valuable fallback look like a
downgrade, and would leave you unable to tell a cheaper model from a lobotomised one.

## Validation happens when configuration is applied, not when you save

Half-finished configuration saves fine — otherwise editing would be unusable. Validity is enforced
when the configuration is applied to serve requests, because that is the boundary an invalid plan
must not cross. So an invalid chain does not break production; it simply never takes effect. `check(project)` is how you ask before then, and `explain_agent` shows what a given
agent would actually do, hop by hop.

Errors name the thing to change. If one does not, that is a bug worth reporting.

## Keys, and why there are several

`route`, `config` and `admin` are **different keys and never the same key**. A production key that
leaks can spend tokens: bad, bounded, and visible in your telemetry. If that same key could edit
routing, whoever held it could repoint a model and read every prompt.

- **`route`** — what your application holds. Spends tokens, reads the routing table. Cannot change
  configuration and cannot read a transcript.
- **`config`** — what this plugin asks for. Edits agents, harnesses, connections.
- **`admin`** — credentials, webhooks, tunnels, project creation.

A **person** authenticates and gets authorised by their organisation role (`OWNER`, `ADMIN`,
`MEMBER`) plus per-project grants. A **key** is not a person and is never a seat.

Scope comes from the credential, never from a request parameter. A key bound to a project *overrides*
any project you name; a person has no bound project, so they must name one.

## Credentials are references

You store a provider key once; Gridline hands back a `vault://…` reference. Configuration names the
reference, never the secret.

**The write path returns a fingerprint, and that is the entire read surface.** No endpoint returns
credential material, in any state, to any principal — including for support. So there is no
Gridline workflow that needs a secret written into a file or a conversation, and any suggestion
otherwise is wrong.

## Sessions

A conversation. Recording is on, and every turn is stored twice: a canonical shape you can read
across providers, and the provider's original bytes — because a tidied conversation cannot always
be continued, and the original is what makes resuming reliable.

`request_id` is the join. It is on every response as `X-Request-Id`, in the attempt records behind
every cost report, and on the stored transcript. **A failover writes two attempt records under one
`request_id`**, which is what makes the cost of a failed hop attributable rather than invisible.

## Reading further

Load from `references/` as needed — do not read them all up front:

`agents-and-hops.md` · `harness-and-surfaces.md` · `connections-and-components.md` ·
`capabilities-and-parity.md` · `assignment-and-tenancy.md` · `sessions-and-transcripts.md` ·
`tasks-and-metadata.md` · `telemetry-and-cost.md` · `webhooks-and-events.md` · `tunnels.md` ·
`credentials.md` · `http-api.md` · `errors.md` · `headers.md` · `environment.md` · `sdk.md` ·
`passthrough.md`

## Before acting, always

1. **Check you are connected.** Call `list_projects`. On a 401 or no tools at all, stop and say
   what to do — run `/mcp` to sign in — rather than guessing against an API you cannot reach. A
   workflow that half-works without credentials is worse than one that refuses.
2. **Know which project.** If more than one exists and the credential is not bound to one, ask.
   Never infer it.
3. **Never put a credential in a tool call.** Read it from the environment inside the same command
   that sends it. A hook enforces this, and it will refuse.

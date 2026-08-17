---
name: gridline-migrate
description: Move an application off direct Anthropic or OpenAI SDK calls, or off managed agents, and onto Gridline. Use when asked to migrate, integrate or adopt Gridline in an existing codebase, or to evaluate what switching would involve.
---

# Migrating onto Gridline

Cite `gridline-primitives`, `references/passthrough.md` and `references/sdk.md`.

## Audit before proposing anything

Delegate to `gridline-repo-auditor`. It returns every provider call site, model string,
managed-agent registration, tool declaration and existing base-URL override as a table. Do not sweep
inline — it reads a lot and only the conclusion matters.

A plan built on a README rather than the call sites will be wrong about the one thing that matters:
how many distinct agents there actually are.

## Group the work into the two tiers

**Tier one — passthrough.** A base URL and a model string. No new dependency, no change to how
responses are parsed. Most call sites are this.

**Tier two — the SDK.** Needed only for approvals, one reply shape across vendors, or a single
parsing path. Name *why* for each site rather than moving everything.

## Propose one agent per distinct (system prompt, model, tool set) triple

That is the natural unit. Name the collisions explicitly — two call sites with the same prompt and
different tools are two agents, and merging them silently changes behaviour for one of them.

Where triples are nearly identical, say so: near-identical harnesses mean separate cached prefixes,
which is a real recurring cost. Sharing one harness is usually right and is cheaper.

## Stage it so the reversible part lands first

**1. Configuration only.** Create the connections, harnesses and agents. Nothing calls them yet.
`check(project)` and `explain_agent` for each. Zero risk.

**2. Tier one, behind a variable.** Base URL from an environment variable with the provider's own as
the default:

```python
base_url=os.environ.get("LLM_BASE_URL", "https://api.anthropic.com")
```

**Insist on this even if the team is confident.** Reverting becomes a redeploy with one variable
changed rather than a rollback, which is the difference between an incident lasting a minute and
lasting as long as a release.

**3. Tier two, only where needed.** Per site, with the reason.

## Verify parity

Run the same prompt through both paths and compare *shapes*, not exact text — models are
nondeterministic and a diff of prose proves nothing. Check the reply has the fields the code reads.

Then `explain_agent` on each agent to see what a fallback would give up before it happens in
production rather than after.

## What you gain, and what changes

State both. A migration pitched as pure upside gets abandoned at the first surprise.

**Gained:** cost per tenant, agent, model and session, plus the waste line; failover with each
attempt's cost attributable through one `request_id`; transcripts; spend ceilings; approvals; one
reply shape (tier two); and the degradation signals — `tools_degraded` above all, because it is how
you tell "the model chose not to call a tool" from "the model was never given one".

**Changed:**

- A **cross-vendor fallback returns that vendor's response shape** to a raw client — so your parser
  meets something new exactly when a provider is down. Keep the chain within one vendor, or use the
  SDK.
- An **`ask` policy breaks a raw client**, which cannot render a pause. Agents reached by tier one
  should have no `ask` tools.
- A **proxy-run tool loop does not stream.** If a call site streams and its agent uses server-side
  tools, that combination does not work — flag it during the audit, not after.
- **Your own client-side tools keep working**, but Gridline sees them only as prefix tokens. Per-tool
  cost needs the tools in the harness.
- **Extended thinking rules out a cross-vendor fallback.** If a call site uses thinking, its chain
  stays within one vendor.

## If the codebase is not Python

Tier one works from any language — it is an HTTP base URL.

**TypeScript has a second option, and it is not the Python SDK.** `@get-gridline/ai-sdk-provider`
is a [Vercel AI SDK](https://ai-sdk.dev) provider: an application already calling `generateText` or
`streamText` points at Gridline instead of at one vendor, and gets the same reply shape it already
parses, plus approvals through the AI SDK's own `tool-approval-request` parts. **0.4.0 or newer**
for the approvals part; Node 22 or newer, ESM only, against `ai` 7.x. So a Node codebase does
**not** stop at tier one, and saying it does is the mistake to avoid here.

**Anything else does stop at tier one** — Go, Ruby, Java, the rest. Say plainly what that costs
(no approvals, no one reply shape across vendors) rather than implying a client exists that does
not.

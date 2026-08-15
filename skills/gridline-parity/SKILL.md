---
name: gridline-parity
description: Answer whether a given model or provider supports the capabilities an agent needs — tools, streaming, structured output, extended thinking, vision, prompt caching — and what a fallback to it would give up. Use for "can I use X with Y" questions and provider comparisons.
---

# Capability parity

Cite `references/capabilities-and-parity.md`.

## Ask the catalogue, never a list

```
browse_models(capability="tools")
browse_models(capability="thinking_blocks")
GET /catalogue/surfaces
```

**One capability per call.** `capability` is a single name, not a list, so a question about two is
two calls and the intersection is yours to take — or `explain_agent`, which answers it for a chain
that already exists. This is live: models are added, deprecated and repriced
continuously, so any list written down is a snapshot. If something here disagrees with the catalogue,
the catalogue is right.

## Then answer the actual question

"Can I use thinking and tools on provider X" has three possible answers and they are different:

1. **Yes** — and here is the model.
2. **Yes, and a cross-vendor fallback costs you the thinking** — because thinking is `STATE` and
   cannot transfer, so the chain is refused until the fallback says `allow_state_loss: true`. This
   is the answer people are surprised by, so say it plainly, including the part that outlives the
   turn: a conversation that fails over that way cannot be natively resumed afterwards.
3. **No** — and here is the nearest model that can.

## The class rules, briefly

| Class | May a chain mix it? |
|---|---|
| `ADDITIVE` — caching, vision, reasoning effort | Yes. Loss is recorded as degradation |
| `CONTRACT` — tools, streaming, structured output | No. A hop lacking one breaks your code |
| `STATE` — thinking blocks, reasoning items | Only where the fallback opts in, and it continues without the reasoning |

## Prompt caching, when asked about it

Two things people get wrong, and both change the advice:

**It is already on.** Every hop asks its provider to cache the prompt prefix unless somebody set
`cache: false` on that hop. There is nothing to enable, and no reason to turn it off for an agent
that holds a conversation: a cache write costs about a quarter more than a fresh input token and a
read costs a tenth of one, so it pays for itself well before the first reuse. The case for `false`
is an agent whose prompts are genuinely one-off and never repeat a prefix.

**Most providers cache without being asked at all.** On those, caching is a property of sending an
identical prefix twice and there is no marker to place — so `prompt_cache` appearing in what a
fallback loses is about the *rate card*, not about whether anything can be done differently. What
you can control is the prefix: an agent's prompt and its tool definitions are what gets cached, so
anything that varies them per turn is what stops a cache from being hit. That is why an assignment
sits beside the harness rather than inside it, and why the tool list is declared once rather than
rebuilt per request.

Switching caching off on a model that cannot cache is refused rather than accepted quietly, so a
setting that would have meant nothing is a message instead of a surprise on a bill.

## What a specific fallback gives up

`explain_agent(project, agent)` is the precise answer for a configured chain. Prefer it over
reasoning from the table when the user has an actual agent — it accounts for the models they really
chose.

## Retirement

If asked whether a model is being retired: **Gridline does not currently populate a retirement date**,
so the honest answer is that this cannot be answered from Gridline and they should check the
provider's own deprecation notices. Do not infer it from a model's age or name.

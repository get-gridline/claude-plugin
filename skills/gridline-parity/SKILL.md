---
name: gridline-parity
description: Answer whether a given model or provider supports the capabilities an agent needs — tools, streaming, structured output, extended thinking, vision, prompt caching — and what a fallback to it would give up. Use for "can I use X with Y" questions and provider comparisons.
---

# Capability parity

Cite `references/capabilities-and-parity.md`.

## Ask the catalogue, never a list

```
browse_models(capabilities=["tools", "thinking_blocks"])
GET /catalogue/surfaces
```

Returns only models with **all** of them. This is live: models are added, deprecated and repriced
continuously, so any list written down is a snapshot. If something here disagrees with the catalogue,
the catalogue is right.

## Then answer the actual question

"Can I use thinking and tools on provider X" has three possible answers and they are different:

1. **Yes** — and here is the model.
2. **Yes, but not with a cross-vendor fallback** — because thinking is `STATE` and cannot transfer.
   This is the answer people are surprised by, so say it plainly.
3. **No** — and here is the nearest model that can.

## The class rules, briefly

| Class | May a chain mix it? |
|---|---|
| `ADDITIVE` — caching, vision, reasoning effort | Yes. Loss is recorded as degradation |
| `CONTRACT` — tools, streaming, structured output | No. A hop lacking one breaks your code |
| `STATE` — thinking blocks, reasoning items | No. Opaque state cannot transfer between vendors |

## What a specific fallback gives up

`explain_agent(project, agent)` is the precise answer for a configured chain. Prefer it over
reasoning from the table when the user has an actual agent — it accounts for the models they really
chose.

## Retirement

If asked whether a model is being retired: **Gridline does not currently populate a retirement date**,
so the honest answer is that this cannot be answered from Gridline and they should check the
provider's own deprecation notices. Do not infer it from a model's age or name.

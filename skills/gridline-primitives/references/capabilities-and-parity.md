# Capabilities and parity

Every capability has a class, and the class decides whether a fallback chain may mix it.

| Class | Examples | Rule |
|---|---|---|
| `ADDITIVE` | prompt caching, vision, reasoning effort | May vary. Loss is recorded as degradation |
| `CONTRACT` | tools, streaming, structured output | Must be identical on every hop |
| `STATE` | thinking blocks, reasoning items | Must be identical on every hop |

## Why `CONTRACT` is strict

Your code is written against a shape. If hop one supports structured output and hop two does not, a
failover returns something your parser has never seen — at 3am, on the day a provider has an
outage. So a chain that mixes them is refused at configuration time instead.

## Why `STATE` is stricter, and the constraint everybody meets

Reasoning state is opaque and provider-specific. Gridline models it as **two distinct
capabilities** — `thinking_blocks` (Anthropic) and `reasoning_items` (OpenAI) — so "must be
identical" means "same state format" with no special cases.

The consequence: **an agent using extended thinking cannot have a cross-vendor fallback.** Not a
limitation of Gridline; the state genuinely cannot transfer. You choose thinking, or a cross-vendor
safety net. Within one vendor you can have both.

## Degraded vs lost

- **`degraded`** — a different model answered, so the output may differ.
- **`lost_capabilities`** — something like prompt caching was unavailable. Costs money; produces
  identical output.

Kept apart deliberately. Netting them together would make a perfectly good failover look like a
downgrade, and the useful signal — "this answer came from a different model" — would be buried.

## Answering "can I use X and Y on provider Z"

```
browse_models(capabilities=["tools", "thinking_blocks"])
```

Returns only models with all of them. Then `explain_agent` for what a specific chain gives up.

## The one degradation signal worth wiring an alert to

`tools_degraded` / `X-Tools-Degraded`. It means a turn went upstream with fewer tools than the
harness declares. Without it, a model that was never given its tools looks exactly like a model
that chose not to use them — it just answers, and says it is finished.

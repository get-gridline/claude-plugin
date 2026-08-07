# Gridline for Claude Code

Wire your application to Gridline without leaving your editor: configure agents and harnesses,
move code off a provider SDK, reach MCP servers inside your own network, and find out what a
conversation actually cost.

## What it is

A set of skills that know Gridline's model and its API. They trigger on what you are doing — ask
"why did last week cost so much" and the cost skill loads; start describing a fallback chain and
the routing skill loads with the rules that decide whether it will validate.

It talks to Gridline's hosted MCP server, so there is nothing to install and no API key on your
disk. You sign in once with `/mcp`.

## Install

```
/plugin marketplace add get-gridline/claude-plugin
/plugin install gridline@gridline
/mcp                                        # sign in to Gridline
```

Then just describe what you want. `/gridline:doctor` is a good first command — it reports what is
configured, what is half-configured, and what is wired to nothing.

If your Gridline is at a different address, set `GRIDLINE_MCP_URL` before starting Claude Code.

### For a whole team

Commit this to your repository's `.claude/settings.json` and everyone who opens it is offered the
plugin, so nobody has to run the commands above:

```json
{
  "extraKnownMarketplaces": {
    "gridline": {
      "source": { "source": "github", "repo": "get-gridline/claude-plugin" }
    }
  },
  "enabledPlugins": ["gridline@gridline"]
}
```

### Updating

```
/plugin marketplace update gridline
```

There is no version to pin and nothing to publish to a registry — a marketplace is a git repository,
so whatever is on its default branch is the current version.

## What it will not do

- **It will never write a credential into a file, a command, or the conversation.** A hook refuses
  any tool call carrying something shaped like an API key, a signing secret or a tunnel key.
  Credentials are read out of your environment and sent straight to the vault, which stores them
  as references and cannot hand them back.
- **It will always ask before destroying something.** See below — this is enforced, not suggested.
- **It will not delete a project.** That is deliberate and there is no tool for it; use the
  dashboard.
- **It will not guess which credential maps to which provider.** Ambiguous names get a question,
  not an assumption.

## Permissions

Gridline ships a recommended permission set. Paste it into `.claude/settings.json` in your project
(or your user settings) to make the read-only tools quiet while leaving every write confirmed:

```json
{
  "permissions": {
    "allow": [
      "mcp__gridline__list_projects",
      "mcp__gridline__describe_project",
      "mcp__gridline__explain_agent",
      "mcp__gridline__check",
      "mcp__gridline__browse_providers",
      "mcp__gridline__browse_models",
      "mcp__gridline__cost_report",
      "mcp__gridline__reliability_report",
      "mcp__gridline__list_tunnels",
      "mcp__gridline__show_tunnel",
      "mcp__gridline__list_webhooks",
      "mcp__gridline__list_tasks",
      "mcp__gridline__describe_task",
      "mcp__gridline__list_invitations"
    ],
    "ask": [
      "mcp__gridline__delete_tunnel",
      "mcp__gridline__delete_webhook",
      "mcp__gridline__retire_tunnel_key",
      "mcp__gridline__retire_webhook_secret",
      "mcp__gridline__revoke_invitation",
      "mcp__gridline__archive_task",
      "mcp__gridline__rename_project",
      "mcp__gridline__replay_webhooks",
      "mcp__gridline__create_webhook",
      "mcp__gridline__rotate_webhook_secret"
    ]
  }
}
```

Everything not listed stays at Claude Code's default, which is a confirmation per use. That is the
right place for the ordinary writes — `create_agent`, `attach_sandbox`, `add_mcp_server` — because
each is reversible and you will want to see it the first few times.

**The `ask` list is belt and braces, not the mechanism.** Every tool in it is *also* forced to
confirm by the plugin's own hook, whatever your settings say — because a permission block you have
to remember to paste is not "always". The list is here so the reasoning is visible and so a team
reviewing its settings can see what Gridline considers destructive:

| Tool | Why it always asks |
|---|---|
| `delete_tunnel` | Revokes **both** credential slots. Cannot be undone; re-registering the name issues new secrets, so every client stops working until reconfigured |
| `delete_webhook` | Takes its signing secrets with it. Undelivered events are lost |
| `retire_tunnel_key` | Retiring the last slot leaves the tunnel registered and carrying nothing — calls are refused until a new credential is issued |
| `retire_webhook_secret` | Retiring the one your receiver verifies with fails every subsequent delivery's signature check |
| `revoke_invitation` | The address must be invited again |
| `archive_task` | History is kept, but it stops accepting new sessions |
| `rename_project` | A project name is referenced by your own config, deploy scripts and dashboards. None of them follow the rename |
| `replay_webhooks` | Your receiver sees past events again. Anything not idempotent happens twice |
| `create_webhook` | Prints a live signing secret into the conversation, and therefore into the transcript |
| `rotate_webhook_secret` | Same — a live secret lands in the transcript |

The last two are worth a note: the skills offer to have *you* run them instead, so the secret
never enters a recorded conversation. If you let the tool run, the skill tells you plainly what is
now in the transcript and offers a rotation.

An HTTP `DELETE` typed by hand is confirmed too, so gating the tool is not something you can walk
around by reaching for `curl`.

## What is in it

**Reference** — `gridline-primitives` is the model of the product and everything else cites it.

**The three big workflows**

| Skill | For |
|---|---|
| `gridline-env-to-vault` | Turning the provider keys you already have into Gridline credentials |
| `gridline-migrate` | Moving an app off direct Anthropic/OpenAI SDK calls or managed agents |
| `gridline-tunnel` | Reaching an MCP server inside your own network |

**Everything else** — `gridline-agents`, `gridline-routing`, `gridline-parity`,
`gridline-cost`, `gridline-budgets`, `gridline-trace`, `gridline-sessions`, `gridline-tasks`,
`gridline-webhooks`, `gridline-sandboxes`, `gridline-approvals`, `gridline-keys`,
`gridline-incident`, `gridline-doctor`.

**Commands** — `/gridline:doctor`, `/gridline:cost [period]`, `/gridline:trace <request_id>`,
`/gridline:migrate`.

**Subagents** — `gridline-repo-auditor` (find every provider call site and model string) and
`gridline-secret-scout` (find credential variable *names*, never values). Both read-only.

## Requirements

- A Gridline account, and a `config` capability on your key or grant. The skills ask for the
  narrowest credential that works and escalate to `admin` only where a call needs it.
- Python SDK ≥ 0.2.0 if you want tier two (`pip install gridline`). Tier one — pointing your
  existing Anthropic or OpenAI client at Gridline's base URL — needs no SDK at all.

## Support

- Docs: <https://get-gridline.dev/docs>
- Issues: <https://github.com/get-gridline/gridline/issues>

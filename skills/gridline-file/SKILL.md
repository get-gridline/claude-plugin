---
name: gridline-file
description: Author, review and apply a .gridline file — a Gridline project's whole configuration as one reviewable file you commit, with plan and apply from the command line or CI. Use when asked to put Gridline config in version control, to generate a .gridline from a live project, to ship a routing change through a pull request, or when a .gridline file is open.
---

# A project as a file

Cite `gridline-primitives` for the vocabulary and `gridline-keys` for credentials.

A `.gridline` file is one Gridline project's configuration, in YAML, committed next to the application
that uses it. `gridline plan` says what would change; `gridline apply` ships it. That replaces clicking
in the dashboard for anything you would rather review as a diff.

**Its keys are the wire format.** This is not a separate schema — it is what `GET /projects/{name}`
returns and what `PUT /projects/{name}` accepts, so there is nothing to translate and nothing to drift.
Anything the API accepts, the file accepts.

## Install

```bash
pip install "gridline[yaml]"      # the `yaml` extra is what lets the file carry comments
gridline --help
```

JSON works with no extra installed — every JSON document is also YAML, and it is the same format. YAML
earns the extra for one reason: comments.

## The three rules

**One file, one project.** Environments and regions are the customer's own project layout: a project per
environment and region pairing, each with its own file. There is deliberately no environment concept
inside the file — one that could target four places has a blast radius nobody can read off the diff.

**Absence deletes.** The file is the truth about the sections it owns, so an agent or harness it does not
declare is *removed*. There is no flag to soften this. Two exceptions, both because absence there cannot
mean deletion:

- **connections** — the file may not declare them at all;
- **tasks** — sessions carry a task id for as long as they are retained, so a dropped stanza is reported
  and left alone. Archiving a task stays an explicit act.

**Connections are not in the file, and declaring one is refused rather than ignored.** A connection is
one provider account and it carries a credential reference. They are managed in the dashboard, and adding
a provider to an organisation writes one into every project it owns — so a file that could author them
would let a CI credential repoint a provider at a host it chose. `apply` sends the stored ones back
unchanged, which is exactly what makes absence safe for everything else: the file cannot express a
connection, so its silence about one says nothing. Harnesses and agents reference them by name; a name
that does not exist is reported by `plan`.

## The verbs

| Command | What it does |
|---|---|
| `gridline pull <project>` | Writes out what is live. **The way to start** on an existing project. |
| `gridline plan [file]` | What would change, and every problem. Writes nothing. Needs only `config`. |
| `gridline apply [file]` | Plans, refuses an invalid document, then writes. |
| `gridline render [file]` | The exact request body, locally. No network, no credential. |

The file argument is optional when there is exactly one `*.gridline` in the directory. Two candidates is
a refusal that lists them, never a guess.

Exit codes, because CI branches on them: **0** applied or nothing to do, **2** the configuration is
invalid, **1** anything else — a missing file, a refused credential, an unreachable control plane.

`apply` always plans first and refuses an invalid document. That is not a convenience: saving does not
validate — half-finished configuration has to stay saveable or the dashboard is unusable — so nothing on
the write path would otherwise stop a broken configuration being stored.

## Before you apply anything: ask

**Never run `gridline apply` without showing the plan and getting explicit confirmation.** Absence
deletes, so an apply nobody read can destroy agents and harnesses that took a long time to get right.
The sequence is not optional:

1. Run `gridline plan`.
2. Show the user the diff **and every removal, by name**.
3. Ask whether to apply, and wait for an answer.
4. Only then run `gridline apply`.

This holds even when the user asked you to "set up and deploy" in one breath — authoring the file and
applying it are two acts, and the second one needs its own yes. If the plan reports removals the user did
not expect, stop and say so rather than reasoning about whether they meant it.

Never invent a `--force`-style flag or reach past the CLI to `PUT` the document directly to avoid the
plan. There is no such flag by design.

## Writing one from a live project

The reliable path is to generate rather than compose:

```bash
gridline pull globex-prod > globex-prod.gridline
```

`pull` strips what the file may not own, so `pull` then `apply` is a no-op. If you are helping somebody
who has no project yet, remember a `.gridline` file **configures a project that already exists** —
creating one happens through an organisation, in the dashboard. Use `describe_project` to see what is
there before writing anything.

## The shape

```yaml
name: globex-prod

ceilings:
  - {amount: 40000, scope: project, period: month}

harnesses:
  standard:
    name: Standard
    memory: {connection: mem0}          # references a connection; never declares one
    tools:
      - connection: erp
    permissions:
      default: allow
      tools: {erp_create_bill: ask}
    subagents: [researcher]

agents:
  arti_chat:
    name: Chat
    system_prompt_file: ./prompts/arti_chat.md
    harness: standard
    model: {provider: anthropic, model: claude-opus-4-5}
    fallbacks:
      - {provider: bedrock, model: claude-opus-4-5}
      - {provider: openai, model: gpt-5, allow_state_loss: true}
```

`system_prompt_file` is resolved relative to the file and is **write-only** — `pull` emits the prompt
inline, because the API stores a string and has no idea a file was involved. Keep the reference form in
the file you already have. Declaring both it and `system` is refused: two answers to one question.

A chain crossing a reasoning-state boundary needs `allow_state_loss` on the hop *receiving* the failover.
Without it `plan` fails and names the flag — see `gridline-routing`.

## Sections that need more than `deploy`

`tasks` needs `config`, which anything that can apply already holds. **`webhooks` and `tunnels` need
`admin`**: one mints a signing secret, the other is an organisation-wide registration.

A credential without the capability means the section is **not managed** and `apply` says so, naming what
was missing, rather than failing. That is deliberate, and it is what keeps a freshly minted webhook secret
out of a build log: a pipeline credential is deploy-scoped and so never reaches that code.

A tunnel belongs to an *organisation*, not a project, so an unpinned one is shared across projects and one
project's file will never remove it. `project_pinned: true` binds it, and then absence does remove it.
What servers a tunnel reaches is reported by the client that found them and is never declared here.

## The credential

Issue one holding the **`deployer`** preset — `config` to read and diff, `deploy` to apply — bound to the
one project the file configures. Set it as `GRIDLINE_CONFIG_KEY`.

`deploy` is narrower than `admin` on purpose: it cannot write a provider credential, mint an API key,
delete the project, or send traffic. The worst a leaked pipeline secret does is apply a document to one
project.

**Never reuse the application's `GRIDLINE_API_KEY`.** That is a `route` credential and the two stay
separate: one credential that could both spend tokens and edit routing could repoint a model at itself
and read every prompt.

## In CI

Plan on a pull request, apply on merge. Filter on paths so a repository's other pull requests do not run a
plan that reports nothing — a check that always says nothing stops being read. Serialise applies per
branch: two runs applying different revisions of one file race, and the loser is refused rather than
silently lost, which is correct and still a red build somebody has to investigate.

If the user wants a ready-made workflow, offer to write one and walk through the secret setup; do not
assume which branch is theirs or that `main` should auto-apply without an approving reviewer.

# LOOPSPEC.yaml

The single artefact the interview produces. Generation is a pure function of this file, so
regenerating after an edit is cheap — which is exactly why you should get it approved before
writing anything else.

Keep it to about forty lines. The user should be able to read the whole thing on a phone and
tell you what is wrong with it.

---

## Full example

```yaml
# LOOPSPEC.yaml
project:
  name: bench-dashboard
  description: >
    App in the Bench stack that takes uploaded files and renders a dashboard.
    Plots live in app/examples/.

size: standard            # minimal | standard | full

goal:
  name: add-one-plot
  unit: >
    One plot added to the dashboard: contract, implementation, and a blessed
    reference render, registered in the manifest.

verify:
  pattern: golden-outputs           # see reference/verifier-patterns.md
  command: python harness/verify.py --all
  gates:
    - {id: L0, name: lint and types,      cmd: "ruff check app && mypy app",        blocking: true}
    - {id: L1, name: contract wiring,     cmd: "python harness/verify.py --gates L1", blocking: true}
    - {id: L2, name: renders from fixture, cmd: "python harness/verify.py --gates L2", blocking: true}
    - {id: L3, name: structure matches,   cmd: "python harness/verify.py --gates L3", blocking: true}
    - {id: L4, name: diff vs golden,      cmd: "python harness/verify.py --gates L4", blocking: true}
  advisory:
    - id: L5
      name: legibility and accessibility
      rubric: >
        Readable at 480px. Axes labelled with units. Distinguishable under
        deuteranopia. Answers the question in the contract. Flag disclosure
        risks as high severity.

deny:
  - "app/examples/**/contract.yaml"
  - "app/examples/**/golden.png"
  - "app/fixtures/**"
  - "harness/verify.py"
  - "gate.yaml"
  - ".github/workflows/**"
  - "**/.env*"
  - "infra/**"

autonomy:
  default: L1
  per_goal: {add-one-plot: L2}

trigger:
  type: schedule          # schedule | push | manual | file-arrival
  cron: "0 8 * * 1-5"

stop:
  max_attempts: 6
  no_progress: 3

notes:
  stubbed:
    - "Bench runtime target unknown — deployment smoke gate is skipped until filled in"
```

---

## Fields

| Field | Required | Notes |
|---|---|---|
| `project.name` | yes | Used for directory and branch names. Keep it kebab-case. |
| `project.description` | yes | Two or three lines. Goes into the generated `LOOP.md` header. |
| `size` | yes | `minimal` (4 files) · `standard` (9) · `full` (15+). Default `standard`. |
| `goal.name` | yes | Kebab-case. Becomes the `--goal` argument and the branch prefix. |
| `goal.unit` | yes | One increment, in plain language. If this reads like a project, go back to the interview. |
| `verify.pattern` | yes | One of the eight in `verifier-patterns.md`. Recorded so a future reader knows the reasoning. |
| `verify.command` | yes | The single command that returns non-zero when the work is not done. |
| `verify.gates[]` | yes | Ordered cheapest first. Each needs `id`, `name`, `cmd`, `blocking`. |
| `verify.advisory[]` | no | Model-judged gates. Each needs `id`, `name`, `rubric`. Never blocking by default. |
| `deny[]` | yes | Glob patterns. Always includes whatever the verifier reads to decide. |
| `autonomy.default` | yes | `L1` report · `L2` branch and PR · `L3` merge. Default `L1`. |
| `autonomy.per_goal` | no | Per-goal overrides. |
| `trigger.type` | yes | `schedule` · `push` · `manual` · `file-arrival`. |
| `trigger.cron` | if schedule | Standard five-field cron, UTC. |
| `stop.max_attempts` | yes | Default 6. |
| `stop.no_progress` | yes | Identical failures before halting. Default 3. |
| `notes.stubbed[]` | no | Anything the loop cannot verify yet. Surfaces in `STATE.md` and caps autonomy. |

---

## What each `size` generates

**`minimal`** — one person trying the idea out.

```
LOOP.md  STATE.md  harness/verify.py  harness/run_loop.sh
```

**`standard`** — a team loop on a schedule. The usual answer.

```
+ AGENTS.md  gate.yaml  harness/check_deny.py
  loop-run-log.md  .claude/agents/implementer.md
```

**`full`** — multiple agents, budget control, CI.

```
+ loop-budget.md  harness/hooks/{post_edit,pre_commit}.sh
  .claude/agents/{verifier,auditor}.md  .github/workflows/loop.yml
  skills/<project>/SKILL.md  docs/LOOP.md
```

---

## Validating before you generate

`forge.py` refuses on these, and the refusals are worth understanding rather than working
around:

- `verify.gates` is empty, or none is blocking → there is no stop condition, so there is no
  loop
- `deny` does not cover the files `verify.command` reads → the agent can edit its own
  criteria, which makes every green result meaningless
- `autonomy.default` is `L3` on a first generation → nobody should start unattended
- `goal.unit` is over 200 characters → almost always a project wearing a unit's clothing

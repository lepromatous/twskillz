---
name: loop-forge
description: Designs and generates a complete agentic loop for a project — LOOP.md, STATE.md, verify script, gate.yaml, subagents, CI trigger — by interviewing the user about what "done" means and what the loop must never touch. Use this whenever someone wants to set up a loop, an agent loop, loop engineering, an autonomous or self-running agent workflow, a harness, a verification loop, a Ralph loop, or says anything like "make this run by itself", "I want an agent that keeps working until it's finished", "automate this with an agent", or asks how to stop babysitting a coding agent. Also use it to audit or repair an existing loop that spins, overruns its budget, or ships unverified work.
---

# Loop Forge

Turn a rough intention into a working loop.

A loop is a system that prompts an agent so a human does not have to: it finds the work,
hands it out, checks the result, writes down what happened, and decides whether to go again.
The files in this skill's `templates/` are the parts. The interview is how you work out what
goes in them.

**The scaffolding is the easy half.** Anyone can generate a folder of markdown. The half that
decides whether the loop is useful or expensive is the verifier — the thing that answers *is
it done?* without asking the agent, which is a poor judge of its own work. Most of this skill
is about finding that answer for a project that does not obviously have one.

If you take one instruction from this file: **do not generate anything until you can state,
in one sentence, the command that returns non-zero when the work is not finished.**

---

## The shape of the job

```
rough intention  ->  interview  ->  LOOPSPEC.yaml  ->  forge.py  ->  the loop files
                     (you)          (~40 lines,        (mechanical)
                                     human reviews)
```

The spec in the middle matters. Do not go straight from conversation to thirty generated
files — nobody reviews thirty files, and a loop nobody reviewed is a loop nobody trusts.
Produce one short spec, put it in front of the user, let them argue with it, *then* generate.
Regenerating after an edit is cheap because generation is a pure function of the spec.

---

## Step 1 — Read what you already have

Before asking anything, mine the conversation and the repository. Most answers are already
sitting there and asking for them again is the fastest way to make this feel like paperwork.

Look for, in order:

- **An existing test command.** `pytest`, `npm test`, `go test`, `make check`. If one exists,
  you have most of a verifier already and the interview gets much shorter.
- **CI config.** `.github/workflows/`, `.gitlab-ci.yml`. Whatever CI already enforces is the
  blocking gate set, near enough.
- **Linters, type checkers, schemas.** `ruff`, `eslint`, `mypy`, `tsconfig`, JSON Schema,
  dbt tests, Great Expectations. Each one is a free computational gate.
- **The stated goal.** "Take uploaded files and make a dashboard" tells you the unit of work
  is one plot, and that the loop's goal is `add-one-plot` rather than `build-the-app`.
- **Anything obviously untouchable.** Secrets, infrastructure, migrations, the CI config
  itself.

State what you inferred and ask only about the gaps. "I can see you already run pytest and
ruff in CI — I'll use those as the blocking gates. Two things I can't work out from here:"
is a much better opening than six questions.

## Step 2 — Interview

Read `reference/interview.md` for the full script, the inference rules, and worked examples
of good and bad answers.

The short version: **six questions, maximum, one at a time.** In priority order —

1. **What is one unit of finished work?** Not the project, one increment. "One plot added",
   "one flaky test fixed", "one dependency bumped". A loop that tries to build the whole
   thing has no place to stop.
2. **What command tells you it worked?** This is the question. Keep pushing until you get
   something that exits non-zero on failure. If they cannot name one, go to Step 3.
3. **What matters that a computer can't check?** Readability, tone, whether a chart actually
   answers its question. This becomes an advisory gate, never a blocking one.
4. **What must it never touch?** Secrets, infra, migrations, the test files themselves. When
   in doubt, add it — a denylist that is slightly too wide costs an escalation, one that is
   too narrow costs an incident.
5. **When it succeeds, what should happen?** Write a report / commit to a branch / merge.
   That is autonomy level L1 / L2 / L3. **Default to L1 and say so.**
6. **What sets it off?** A schedule, a push, or a person. Nightly is the right first answer
   for most teams.

If a tappable-options tool is available (`ask_user_input_v0` or similar), use it for
questions 5 and 6 — they are multiple choice and typing on a phone is miserable.

**Do not ask about**: which model, token budgets, worktrees, context windows, sub-agent
topology. Those have sensible defaults in the templates. Every question you ask that the
template could have answered makes loop engineering feel harder than it is, which is the
opposite of the point.

## Step 3 — Find the verifier

This is where the value is. Read **`reference/verifier-patterns.md`** — it catalogues eight
ways to manufacture a machine-checkable stop condition, organised by what the project
produces. Match the project to a pattern and propose it concretely.

The most useful move in the catalogue, because it generalises: when the goal is subjective
("a nice dashboard", "a clean report"), find the artefact folder and turn it into an answer
key. Each item becomes an input fixture, a written contract, and a blessed reference output.
"Does it look nice" is unfalsifiable; "does it match its contract and its reference" is not.

**If no verifier can be built, say so and stop.** Some work genuinely cannot be checked
without a human reading it. Tell the user plainly: a loop here would be an expensive way to
generate unreviewed output, and they are better served by a good skill file and ordinary
prompting. `reference/verifier-patterns.md` has the list of shapes where this is the honest
answer. Declining to build the loop is a valid and sometimes correct outcome of this skill.

## Step 4 — Write LOOPSPEC.yaml and get it approved

Schema and a full worked example: `reference/loopspec-schema.md`.

Keep it to about forty lines. Show it in the conversation, not as a file to download — the
user should be able to read the whole thing on a phone. Ask one question: *does this describe
the loop you want?*

Pay attention to `size:`, which controls how much gets generated:

| `size` | Files | When |
|---|---|---|
| `minimal` | 4 | One person, one repo, trying the idea out. Start here. |
| `standard` | 9 | A team loop that will run on a schedule. The usual answer. |
| `full` | 15+ | Multiple sub-agents, skills, CI, budget ceilings, run ledger. |

**Default to `standard`.** Suggest `minimal` for anyone doing this for the first time. Fifteen
files handed to a sceptic is how a good idea dies in review.

## Step 5 — Generate

```bash
python scripts/forge.py --spec LOOPSPEC.yaml --out <project-dir>
```

Then **run the verifier it generated** and show the output. A gate that fails with a specific,
actionable message is the whole mechanism, and seeing it fail once teaches more than any
explanation:

```bash
python <project-dir>/harness/verify.py --all
```

If everything passes on the first run, the loop has nothing to do and the verifier is
probably too weak. Say so rather than presenting it as success.

## Step 6 — Hand over honestly

Close with three things and no more:

1. **The one command** to start it, at L1.
2. **What is stubbed** and must be filled in before it runs unattended.
3. **The caveat.** An unattended loop makes unattended mistakes, and the faster it ships code
   the user did not write, the wider the gap between what exists and what they understand.
   Read the diffs. Anyone who describes a loop as hands-off has misunderstood it.

---

## Design rules to encode, every time

These are not preferences. They are the difference between a loop that works and one that
quietly burns money, and they are already baked into the templates — do not generate around
them.

**Success is silent, failure is verbose.** A passing gate emits nothing; a failing gate emits
everything needed to fix it. The failure text is not a log, it is literally the next prompt.
Narrating successes fills the context window with nothing.

**Computational before inferential.** Deterministic checks — tests, linters, schemas, diffs —
run first, cost nothing, and block. A model judging quality runs last, costs a lot, and
advises. Never let a judge be the only thing between the loop and the main branch.

**The agent may not edit its own success criteria.** Tests, contracts, reference outputs, the
verifier itself, and the gate config all go on the denylist, and the denylist is checked
*before* verification runs. Otherwise the shortest path to "done" is to move the goalposts,
and the agent will find it. This is the single most important line in the generated
`gate.yaml`.

**Fresh context every attempt; state on disk.** Each iteration rebuilds its brief from
`STATE.md` plus the failing gate text rather than carrying a conversation forward. The agent
forgets between runs; the repository does not. This is why a well-built loop runs at constant
quality instead of degrading as the window fills.

**Stop rules are not optional.** An attempt ceiling, and a no-progress detector that halts
when the same failure repeats. That second one is the one people leave out. An agent failing
identically for the third time is not persisting — it is stuck on a signal it cannot act on,
and from the outside that is indistinguishable from persistence while the bill grows.

**Constraints beat instructions.** Writing "follow our conventions" in a prompt and wiring a
check that blocks the merge are not two versions of the same control. The first is a request.
When you find yourself adding a rule to `AGENTS.md`, ask whether it belongs in the verifier
instead. It usually does.

**Ratchet, don't brainstorm.** Every line of the generated `AGENTS.md` should trace to a real
failure. Rules nobody earned dilute the ones somebody did, and each line competes for
attention on every single turn. Keep it under 60 lines and seed it sparsely.

---

## Auditing an existing loop

Same skill, different entry point. Ask for `LOOP.md`, `gate.yaml`, and the run log, then check
in this order — the list is roughly ordered by how often each one is the actual problem:

1. **Can the agent edit its own criteria?** Check the denylist covers tests, contracts,
   reference outputs, the verifier, and the gate config. This is the fatal one.
2. **Is there a no-progress rule?** Without it, loops spin. Look for repeated identical
   failures in the run log.
3. **Does an inferential gate block?** If a model's opinion can halt the pipeline on its own,
   the pipeline will halt for reasons nobody can reproduce.
4. **Does the brief get rebuilt from disk each attempt,** or does the conversation grow?
5. **Is there a ceiling and a circuit breaker?**
6. **Which gate fails most?** From the run log. That gate is either doing its job or badly
   written — and the fix is nearly always a better fixture, not a longer prompt.

Report findings smallest-fix-first. Do not regenerate a working loop from scratch to fix one
missing stop rule.

---

## Files in this skill

| Path | Read it when |
|---|---|
| `reference/interview.md` | Running the interview. Script, inference rules, worked examples. |
| `reference/verifier-patterns.md` | **Always.** Eight ways to build a stop condition, plus when to refuse. |
| `reference/loopspec-schema.md` | Writing the spec. Full field reference and a filled example. |
| `templates/` | Generated by `forge.py`; edit these to change house style for a team. |
| `scripts/forge.py` | Generation. `--spec` in, project directory out. No dependencies required. |

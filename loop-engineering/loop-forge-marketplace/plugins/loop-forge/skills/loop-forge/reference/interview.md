# The interview

Six questions, maximum, one at a time. Infer everything you can before asking anything.

The goal is a filled `LOOPSPEC.yaml` and a user who feels like they answered a few obvious
questions, not one who feels audited. If the interview is longer than the explanation of what
a loop is, this skill has failed at its purpose.

---

## Inference first

Every question you can skip is worth skipping. Before the first message, look for:

| Signal | What it gives you |
|---|---|
| `pytest` / `npm test` / `make check` in the repo | the verifier (Pattern 1) — question 2 is answered |
| `.github/workflows/*` | the current blocking gates, and the trigger style the team already uses |
| `ruff` / `eslint` / `mypy` / `tsconfig` | free computational gates, no need to ask |
| a folder of examples, fixtures, or reference outputs | Pattern 2 is available — propose it |
| `schema.sql`, dbt tests, JSON Schema, pydantic models | Pattern 3 invariants exist already |
| `.env`, `secrets/`, `infra/`, `migrations/` | denylist entries — question 4 mostly answered |
| the user's own description of the project | the unit of work, usually |

Then open by stating what you found:

> "You've already got pytest and ruff wired into CI, so I'll use those as the blocking checks.
> Two things I can't work out from here — what counts as one finished piece of work, and what
> the loop should never touch."

That reads as competence. Six cold questions read as a form.

---

## The questions

### 1. What is one unit of finished work?

The single most important answer and the one people get wrong, because they describe the
project instead of an increment.

- Bad: "build the dashboard app"
- Good: "add one plot to the dashboard"
- Bad: "fix the test suite"
- Good: "fix one failing test"
- Bad: "migrate to the new API"
- Good: "migrate one endpoint"

If the answer is project-sized, ask what the smallest useful piece is. If there genuinely
isn't one, that is a signal to refuse — see `verifier-patterns.md` §4.

*Fills:* `goal.unit`, and usually `goal.name`.

### 2. What command tells you it worked?

The question this whole skill turns on. Push until you get something runnable.

Escalating prompts if the first answer is vague:

- "If someone else did this work, what would you run before believing them?"
- "What would have caught the last thing that went wrong here?"
- "Is there anything that's currently red that ought to be green?"

If they say "I'd look at it" — that is Pattern 2 or Pattern 7, and your job is to propose the
concrete version. Do not accept "I'd look at it" as the verifier. Propose:

> "Then let's give the loop something to look at. If we take three of your existing charts,
> save the input that produced each one and a copy of the output you're happy with, the loop
> can check its own work against those. Adding a fourth chart becomes something a machine can
> mark."

*Fills:* `verify.pattern`, `verify.gates`.

### 3. What matters that a computer can't check?

Readability, tone, whether a chart answers its question, whether an explanation makes sense
to a newcomer. Real, and not mechanically checkable.

Capture it as an advisory gate with a written rubric. Say explicitly that it advises rather
than blocks, and why: model judgement is not reproducible, and a pipeline that halts for
reasons nobody can reproduce gets switched off.

If they cannot think of anything, skip it. An advisory gate that exists for completeness is
pure cost.

*Fills:* `verify.advisory`.

### 4. What must it never touch?

Offer a starting list rather than an open question — people under-answer open questions about
risk, and the cost of a too-wide denylist is one escalation while the cost of a too-narrow one
is an incident.

> "I'll block secrets, infrastructure, migrations, CI config, and the checks themselves.
> Anything else in your repo that would be bad for an agent to edit unsupervised?"

Always include, without asking: the tests, contracts, goldens, fixtures, the verifier, and
the gate config. Explain in one line — if the agent can edit what it is judged against, the
fastest route to done is to lower the bar, and it will find that route.

*Fills:* `deny`.

### 5. When it succeeds, what should happen?

Multiple choice. Use tappable options if the tool is available.

- **Write a report, change nothing** → `L1`
- **Commit to a branch and open a PR for me** → `L2`
- **Merge it** → `L3`

**Recommend L1 regardless of what they pick**, for the first week, and say why: the point of
week one is finding out which gates are badly specified, and you learn that from reading
diffs, not from merges. Someone who starts at L3 finds out their verifier was weak by
discovering it in main.

*Fills:* `autonomy.default`.

### 6. What sets it off?

Multiple choice again.

- **Nightly** — the right default for most teams
- **On every push** — for fast, cheap gates only; expensive on a busy repo
- **Only when I ask** — the right answer for anyone nervous, and a fine place to start

*Fills:* `trigger`.

---

## What not to ask

Which model, token ceilings, worktree strategy, context-window management, sub-agent
topology, retry counts, compaction.

All of these have defaults in the templates that are right for the large majority of cases.
Asking about them makes loop engineering feel like a discipline requiring a specialist, which
is the opposite of what this skill is for. If a user raises one, answer it properly — but do
not volunteer the question.

---

## Worked example

**User:** "We've got a monthly regulatory report. Same twelve tables, new data each month.
Takes someone three days and it's mostly mechanical. Can I loop this?"

**Inference:** monthly report, tabular, recurring, an existing definition of correct
(last month's report). Likely Pattern 3 plus Pattern 5. Ask about a prior artefact before
anything else.

**Q1:** "What's one finished piece — one table, or the whole report?"
→ *"One table, I suppose. They're independent."*

**Q2:** "What would you run before believing someone else had built table 7 correctly?"
→ *"I'd check the totals reconcile to the source extract, and compare against last month for
anything that moved more than about 10% without a reason."*

That is the verifier, and it was there all along. Pattern 3 — reconciliation plus a
period-over-period delta check.

**Q3:** "Anything that matters but isn't in those two checks?"
→ *"The commentary paragraph under each table has to read sensibly."*

Advisory gate, rubric-judged. Not blocking.

**Q4:** Offer the standard denylist, plus the reconciliation checks themselves and the
prior-month reference extracts.

**Q5:** → *"Branch and PR."* Recommend L1 for the first month anyway.

**Q6:** → *"Monthly, when the extract lands."* File-arrival trigger, monthly cadence.

**Spec:** `unit: one table`, Pattern 3, four blocking gates, one advisory, L1 rising to L2,
`size: standard`. Nine files. The interview took six messages.

---

## Signals to stop and reconsider

Pull out of the interview and revisit `verifier-patterns.md` §4 if you hear:

- "I'd just know if it was right" — after two attempts to make it concrete
- "It depends on the context each time" — the spec changes per unit, so no stable contract
- "It needs to go straight out to clients" — irreversible; human gate or nothing
- "We don't have any tests but I don't want to write any" — the verifier build *is* the
  project, and that is worth saying out loud

None of these mean the conversation was wasted. "You don't want a loop, you want a good skill
file, and here's why" is a genuinely useful thing to hand someone.

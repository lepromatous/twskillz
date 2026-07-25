# Verifier patterns

How to manufacture a machine-checkable stop condition for a project that does not obviously
have one.

Read this before generating anything. The interview questions are easy; this is the part that
decides whether the loop is worth building.

**Contents**

1. [Why this is the hard part](#1-why-this-is-the-hard-part)
2. [The eight patterns](#2-the-eight-patterns)
3. [Choosing one](#3-choosing-one)
4. [When to refuse](#4-when-to-refuse)
5. [Quality checks on a proposed verifier](#5-quality-checks-on-a-proposed-verifier)

---

## 1. Why this is the hard part

An agent asked whether its own work is finished will say yes. Not from dishonesty — it has no
independent evidence, so it reports its intent rather than its result. Every loop that
terminates on the agent's own say-so terminates confidently on broken output.

So a loop needs an external judge. And the judge has to be *cheap*, because it runs on every
attempt, and *specific*, because its output becomes the next prompt. "Something is wrong"
gives the agent nothing to act on and it will spin.

Which means the real question in every interview is:

> **What command exits non-zero when the work is not finished, and prints something an agent
> could act on?**

Most people cannot answer that about their own project on the first ask. That is normal. The
patterns below are how you help them find it.

---

## 2. The eight patterns

### Pattern 1 — Existing test suite

*Shape:* code that already has tests.

The verifier is the test command. This is the easy case and you should recognise it fast:
`pytest`, `npm test`, `go test ./...`, `make check`.

*Gate stack:* lint → typecheck → unit → integration.

*The trap:* tests go on the denylist. An agent told to make the tests pass will, given the
chance, edit the tests. Also ban `skip`, `xfail`, `# type: ignore`, and `# noqa` additions in
the diff — those are the same move wearing a hat.

*Unit of work:* one failing test, one flaky test, one bug ticket.

---

### Pattern 2 — Golden outputs (fixture → contract → reference)

*Shape:* the project produces artefacts a human judges by eye. Charts, reports, rendered
pages, generated documents, exported files.

This is the most broadly useful pattern in the catalogue because it converts subjective goals
into checkable ones. For each artefact, three things sit side by side:

```
<artefact>/
  fixture        a small, committed, deterministic input
  contract       what the output must contain, written down
  golden         a blessed reference output, produced once, approved by a human
```

The verifier renders from the fixture and checks the result against the contract
(structurally) and against the golden (byte or perceptual diff).

*Gate stack:* wiring → renders-without-error → structure-matches-contract → diff-vs-golden.

*The trap:* the golden and the contract go on the denylist, and blessing a new golden is a
human action. A red diff has two causes — an intentional change and a regression — and no
automated check can tell them apart. That judgement stays human, permanently.

*Second trap:* pin the rendering environment. Fonts, backends, and library versions change
pixel output, and a diff gate that goes red for unrelated reasons is a gate everyone learns
to ignore, which is worse than no gate.

*Unit of work:* one artefact added or fixed.

---

### Pattern 3 — Invariants and properties

*Shape:* data pipelines, transforms, ETL. There is no single right answer, but there are
things that must always hold.

Assert properties rather than values: row counts within bounds, no nulls in key columns,
referential integrity across joins, sums that reconcile to a control total, no duplicate
keys, distributions inside plausible ranges, output schema matches declaration.

*Gate stack:* schema → per-table invariants → cross-table reconciliation → row-count deltas
against the prior run.

*The trap:* invariants that are too loose pass everything and the loop declares victory on
garbage. Write the invariant that would have caught the last real incident. If nobody can
remember an incident, the pipeline is either very good or unmonitored, and it is usually the
second.

*Unit of work:* one table, one transform, one failing check.

---

### Pattern 4 — Differential / behaviour preservation

*Shape:* refactors, migrations, rewrites, library swaps, translating code between languages.

The verifier runs old and new against the same inputs and compares outputs. The specification
is the existing behaviour, which means you do not have to write one down.

*Gate stack:* both versions build → same outputs across a corpus of inputs → no performance
regression beyond a threshold.

*The trap:* your input corpus is the real spec, so its coverage is your risk. Include the
weird production inputs, not just the tidy ones. And decide up front which existing bugs are
being preserved deliberately — otherwise the loop will faithfully reproduce them and someone
will file a ticket.

*Unit of work:* one module, one endpoint, one query.

---

### Pattern 5 — Reproducibility

*Shape:* analyses, notebooks, statistical reports, anything where the numbers matter.

The verifier re-runs the whole thing from a clean state and checks the outputs are identical.
This catches the failure that matters most in analytical work: results that depend on
execution order, a stale cache, or an uncommitted file on someone's laptop.

*Gate stack:* clean-environment build → run to completion → outputs byte-identical (or
within a stated numerical tolerance) → every input traceable to a committed source.

*The trap:* seeds and timestamps. Pin every random seed, freeze the clock, and make the loop
fail loudly rather than tolerantly if it cannot. "Nearly the same numbers" is a verifier that
does not verify.

*Unit of work:* one analysis, one figure, one table.

---

### Pattern 6 — Round trip

*Shape:* parsers, serialisers, format converters, importers and exporters, API clients.

`parse(render(x)) == x` for every `x` in a corpus. Cheap, and it catches a surprising
proportion of real bugs.

*Gate stack:* round trip over the corpus → error cases produce the right error, not a crash
→ fuzz the parser if the input is untrusted.

*The trap:* round-tripping only the outputs you generated yourself. Feed it real files from
the wild, especially malformed ones.

*Unit of work:* one format feature, one failing sample.

---

### Pattern 7 — Structure plus rubric

*Shape:* documents, reports, specs, slide decks. Prose deliverables.

Split the check in two. The computational half asserts structure: required sections present,
every claim carrying a citation, no placeholder text, tables well-formed, length in range,
terminology matching a glossary. The inferential half is a model reading it against a written
rubric.

*Gate stack:* structure (blocking) → rubric judge (advisory, blocking only on the loud
failures).

*The trap:* letting the rubric judge block on its own. Model judgement is not reproducible;
a pipeline that halts for reasons nobody can reproduce gets switched off within a month.
Reserve blocking for a small, explicit list — a missing citation, a factual claim the
document contradicts elsewhere.

*Unit of work:* one section, one document.

---

### Pattern 8 — Human checkpoint as the gate

*Shape:* work that genuinely needs a person, but where the loop can still do the surrounding
labour.

The loop does everything up to the judgement call, then stops and asks. It is a real loop —
it still has a trigger, state, and stop rules — it just has a human in one gate. Do not treat
this as a failure to design a proper verifier. For a lot of valuable work it is the correct
architecture, and it is much better than pretending an automated check exists.

*Gate stack:* everything mechanical → package the decision for a human (context, options,
recommendation) → wait → resume on the answer.

*The trap:* asking too often. If the loop stops on every unit, you have rebuilt manual
prompting with extra steps. Batch the questions, or raise the threshold at which it asks.

---

## 3. Choosing one

| The project produces… | Pattern |
|---|---|
| code with tests | 1 — test suite |
| charts, reports, rendered pages, documents-as-artefacts | 2 — golden outputs |
| transformed data | 3 — invariants |
| a rewrite of something that already works | 4 — differential |
| numbers people will quote | 5 — reproducibility |
| a parser or converter | 6 — round trip |
| prose | 7 — structure plus rubric |
| a decision | 8 — human checkpoint |

Combining two is normal and usually better than one. A dashboard project is Pattern 2 for the
charts and Pattern 3 for the ingest layer, and those want different gates because a change to
ingest can pass every chart gate while breaking every chart.

---

## 4. When to refuse

Say plainly that a loop is the wrong tool when:

- **Nothing about the output can be checked without a person reading all of it.** Original
  writing, strategy, design direction, novel research. Recommend a good skill file and
  ordinary prompting instead — that is not a consolation prize, it is the right tool.
- **Each unit of work is enormous.** If "one unit" takes a week, there is no loop, there is a
  project. Help them find a smaller increment first; if there isn't one, stop.
- **The consequences of a wrong action are irreversible.** Sending mail, moving money,
  changing production data, publishing. Pattern 8 with a hard human gate, or nothing.
- **There is no existing signal at all** — no tests, no schema, no reference outputs, and no
  appetite to build any. The loop would need a verifier built first, and that build is the
  actual project. Say so and offer to help with that instead.

Refusing well is a good outcome. A generated loop that nobody can trust costs more than the
hour saved by not having this conversation, and it poisons the team against the technique for
a year.

---

## 5. Quality checks on a proposed verifier

Before writing it into the spec, put the candidate verifier through these five. If it fails
one, fix it now — every one of these is much cheaper to fix before generation than after.

1. **Deterministic?** Same input, same verdict, every time. A flaky gate teaches everyone to
   re-run until green, which trains the exact habit the loop exists to remove.
2. **Fast?** It runs on every attempt. Over a minute or two and iteration gets expensive;
   split it so the cheap gates run first and fail early.
3. **Actionable?** Read the failure text and ask whether *you* could fix the problem from it
   alone. If not, neither can the agent, and it will spin until the no-progress rule fires.
4. **Offline?** No live databases, no network calls, no upstream services. A gate that goes
   red for reasons the agent cannot fix is unactionable red, which is the worst kind.
5. **Tamper-proof?** Everything it reads to decide — tests, contracts, goldens, fixtures,
   the verifier itself, the gate config — is on the denylist. If the agent can edit any of
   it, a green result means nothing at all.

Then one last check, and it catches more bad loops than the other five combined:

> **Run the verifier against the current, unfinished state of the project. Does it fail?**

If it passes before any work has been done, it is not measuring the thing you care about.
Fix that before generating a single file.

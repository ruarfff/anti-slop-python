# Paired refactoring comparison, protocol v1

Frozen before the six new agent runs on 2026-09-07. This is a small controlled
comparison, not a GEPA optimization or a statistical demonstration of general
effectiveness. No model API dependency is needed to replay the saved results.

## Question and conditions

Does adding anti-slop-python feedback to a strong design prompt improve a coding
agent's first completed refactor? Compare three independent pairs using the same
554-line order-report source. Every run starts fresh. Both conditions receive
`prompt.md`; the only treatment is `control.md` versus `linter.md`, and permission
to run the linter. Both can inspect the original, run a supplied CLI smoke test,
write their own checks, and use the formatter.

This measures the whole tool plus feedback. It does not isolate explanatory
guidance from bare lint messages or from Ruff alone. The prompt deliberately
states good design goals; a weak prompt would make an unhelpful control.

## Fixed setup

- Agent: gpt-5.6-luna, medium reasoning, no inherited conversation history.
- Six completions, three pairs. Run each pair concurrently, one pair at a time.
  Alternate dispatch order: control first, linter first, control first.
- Twelve-minute wall-time ceiling per run; completion ends a run sooner. No
  reviewer feedback, repairs, best-of selection, or discarded completed runs.
- Same interpreter, dependencies, tool access and task source; linter frozen at
  repository commit d708c168ddd91ba98a36e478b18af54a8007bee8.
- The agent runtime does not expose a seed, sampling temperature, token budget,
  token usage or price here. Do not invent these values or equate wall time with
  token cost. Root work and host load can affect latency.
- Workspaces are separate directories on a shared host, with instruction-based
  read boundaries. This is not enforced filesystem isolation. Capture public
  completion reports and diagnostic logs, not private reasoning traces.
- Source SHA-256:
  `29d3ce2a3d1263a2976222833704050da85b22a2e66b733c35ee5f8d8f8ac223`.

## Evaluation, frozen before dispatch

Use `tests/test_order_report_refactoring.py` in a fresh process for each candidate.
The agents do not receive that path, test source or results. Record its hash with
the run manifest. The 43 cases include byte comparisons of demo, CSV, text and
JSON outputs; CLI errors; invalid and duplicate records; validation order;
malformed/missing input files; 12 deterministically generated CSV datasets; public
signatures, resolved annotation shapes, constants and record values. The generated
datasets extend coverage within this application; they are not unseen projects.
Annotation shapes ignore package relocation and future-import string storage,
but retain concrete type names and generic arguments. This is not a full static
type check.

Primary outcome: preserved behavior and contracts **and** a sound module split.
Report each hard-gate failure separately. Design review uses these fixed criteria:

1. Responsibilities are separated into named, cohesive modules, with closely
   related code kept together. A smaller file alone does not establish this.
2. Imports are explicit, dependencies are acyclic, and the facade retains the
   original API without an unnecessary second implementation.
3. No metric bypass: compression, arbitrary line chunks, dropped comments or
   contracts, catch-all helpers, suppressions, renamed production files, runtime
   loading of the reference, or configuration changes.
4. No unrelated changes to business decisions, validation order or side effects.

The root performs source review after completion. This review is **not blind**:
run identities and tool reports are visible. Separate observations from measured
checks; do not give subjective scores a spurious numerical precision.

Secondary outcomes: default lint compliance over the entire directory, diagnostic
codes, file count, maximum/total physical lines, elapsed wall time, and tool
invocations. A correct control is not a failed refactor merely because it has a
lint finding. Do not rank candidates by least lines or most extracted files.

Calibrate the evaluator using the unchanged original, the earlier repaired
refactor, an empty entry point, an omitted annotation, and a changed tax rate.
These must respectively expose the missing split, pass the checks, fail behavior,
fail the contract check, and fail byte comparisons. Record controls, including
any gaps in the checks, before interpreting candidate results.

## Changes and reporting

Preserve every first completion before reading withheld results. Record hashes,
exact prompts, model/settings, timestamps, exit states, public completion reports,
diagnostic logs and per-test outcomes. Keep the original example unchanged.
Use failures to identify product or test gaps, but do not retrofit the scores.
Any resulting linter fix needs a targeted regression check and a separate
confirmation run if agent effectiveness is claimed. The six initial results stay
associated with their original linter revision.

Report ties and regressions. Three repetitions of one deliberately sectioned,
synthetic application cannot establish reliability across Python codebases,
large repositories, other models or all rules. No confidence/significance claim
will be made from this sample. Additional projects and a Ruff-only ablation are
future work, not results of this experiment.

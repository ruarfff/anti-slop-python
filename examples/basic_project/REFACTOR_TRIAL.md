# Coding-agent refactoring trials

The controlled follow-up did **not** show that adding anti-slop-python improves
refactor correctness over a strong prompt. It did show a narrower benefit:
agents followed specific lint feedback to remove wildcard imports. Clean lint
still accompanied broken public APIs and changed validation order.

Nine fresh agents produced nine preserved first completions. None was repaired
by the parent or discarded. The original guided trial is retained below as
historical context; its reviewed solution was not supplied to these agents.

## Controlled comparison: 2026-09-07

The question was whether the tool helps when the agent already receives a good
refactoring prompt. Three pairs compared the same prompt with and without
anti-slop-python. Each run started from the same 554-line `order_report.py`.

All agents used `gpt-5.6-luna`, medium reasoning, without inherited conversation
history. Each had a fresh workspace, the reference source, Python 3.14.7, Ruff
0.16.5, four visible CLI smoke comparisons, and permission to write its own
checks. Each had a 12-minute ceiling; all finished sooner. The six initial runs
used the tool at commit `d708c168ddd91ba98a36e478b18af54a8007bee8` (policy v1).

The [common prompt](../refactoring_evaluation/prompt.md) asks for cohesive
modules, explicit interfaces, acyclic dependencies, preserved public names and
types, identical errors and outputs, and no unrelated rewrites or metric bypass.
The [control](../refactoring_evaluation/control.md) used that prompt and behavior
checks. The [linter condition](../refactoring_evaluation/linter.md) additionally
required initial, iterative, and final whole-directory lint runs and reading
the diagnostic guidance. Both could use Ruff's formatter. Controls could not
run lint checks. No module layout was supplied.

The [protocol](../refactoring_evaluation/PROTOCOL.md) and 43 evaluator cases were
fixed before dispatch. Agents were instructed not to read the withheld tests,
other runs, or the parent repository. Each pair ran concurrently, then the next
pair started; dispatch order alternated. Candidates were saved before withheld
results were inspected. Source review used fixed criteria but was not blind.

### What the checks measure

The original 43 cases comprise 41 behavior and API cases, one original-source
hash check, and one whole-directory lint check. They compare:

- CLI stdout, stderr, exit status, and text, CSV, and JSON exports byte for byte.
- Invalid and duplicate records, validation order, missing and malformed files,
  and 12 deterministically generated CSV datasets.
- The 51 declared public functions/classes and six public constants, callable
  signatures, resolved type shapes, and demo record values.

A control's lint failure does not itself mean its refactor is incorrect.
Acceptance requires preserved behavior and contracts plus a sound module split.
The review separately checks responsibility boundaries, imports and cycles,
metric bypass, and unrelated business-logic changes. A low line count is not a
quality score.

Before using the evaluator, calibration checked the earlier repaired solution
(43 passes), the unchanged original (only the size-policy case failed), an empty
entry point (41 failures), removed function annotations (contract and lint
failures), and a changed tax rate (10 behavior/contract failures despite clean
lint). The [calibration record](../refactoring_evaluation/calibration.json)
includes each outcome. This establishes sensitivity to those defects, not
complete correctness coverage.

### Initial paired results, policy v1

Results below use the frozen 43 cases and the saved, self-contained candidates.
“Lines” is the largest module / total Python source. All extracted modules
passed the 500-line limit.

| Run | Cases passed | Behavior/API failure | Saved lint | Files | Lines | Seconds |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Pair 1, strong prompt | 42/43 | None found | Fail | 7 | 141 / 674 | 112 |
| Pair 1, with linter | 42/43 | Package import fails | Pass | 7 | 131 / 645 | 184 |
| Pair 2, strong prompt | 41/43 | Package import fails | Fail | 7 | 130 / 641 | 138 |
| Pair 2, with linter | 42/43 | Package import fails | Pass | 6 | 193 / 710 | 156 |
| Pair 3, strong prompt | 41/43 | Validation order changes | Fail | 6 | 206 / 599 | 117 |
| Pair 3, with linter | 41/43 | Package import fails | Fail* | 9 | 157 / 722 | 171 |

Only one of three controls met the behavior/API and design criteria; none of
three linter candidates did. The linter improved compliance with its own policy
on this sample, but that did not translate into a correct refactor. Much of the
lint cleanup involved Ruff's existing `F401` and `I001` checks. There was no
Ruff-only condition, so this does not establish value beyond Ruff alone.

*Pair 3's linter agent logged a final lint pass in its workspace. The saved
candidate has four `I001` findings. Two stray application drafts outside
`candidate/` affected Ruff's first-party import classification. The archive
retains those files' hashes and names, but excludes them from the candidate.
Both the earlier repository-root replay and the corrected project-directory
replay are saved. Changing the replay directory alone did not remove these
findings. Reported workspace success and independent replay are distinct results.

The median reported time was 117 seconds for controls and 171 seconds with the
original linter. These are agent-reported wall times, affected by host load and
tool calls, not controlled cost measurements. Token usage and cost were unavailable.

### Design review and changes prompted by failures

All six initial candidates had acyclic static import graphs and retained the
original definitions somewhere in their source. That did not guarantee that the
public entry point could import or expose those definitions.

- Pair 1's control preserved the original function/class bodies and used named
  imports. It retained unnecessary imports, but its models, input, pricing,
  reporting, presentation, and export boundaries were coherent.
- Pair 1's linter candidate replaced named imports with eight wildcard imports.
  Policy v1 accepted them. It also rewrote 22 definitions unnecessarily. Its
  package failure came from bare sibling imports; wildcard syntax was a separate
  design problem, not the cause of that import error.
- Pair 2's linter candidate preserved all original function/class bodies and
  made a reasonable coarse split. Bare sibling imports still broke package use.
- Pair 3's control used eight wildcard imports with `noqa: F403` despite the
  prompt's prohibition on suppressions. It also reordered input validation.
  Pair 3's linter candidate placed the real input workflow in `demo.py`, mixing
  sample data with production orchestration, and broke package imports.

These findings led to three generic product changes (policy v2):

1. Enable Ruff's `F403` by default. Its guidance asks for named imports and
   explicit public exports through `__all__`, while retaining project overrides.
2. Add `F401` guidance to check for public re-exports before removing imports.
   Expand `SPY003` guidance to preserve validation order, side effects, and type
   information, and to verify imports and entry points.
3. Run each Ruff subprocess from its configuration's directory, with absolute
   target paths. Independent regression cases reproduced caller-dependent `src`
   classification and per-file exclusions. This fixes configuration resolution;
   it does not repair candidates that rely on stray workspace files.

### Development confirmations and an evaluator gap

Two fresh agents received the same task and updated policy v2. The
[confirmation protocol](../refactoring_evaluation/CONFIRMATION.md) was fixed
before either started. Both first completions passed all 43 original cases.

Source review then found that confirmation 2 exposed only five of the original
57 public names when imported as a standalone module. Its package import and
CLI worked. The original evaluator had checked the full API only in package
mode. Two new tests now compare the complete declared API in fresh processes
for package and standalone imports. They were applied to **every** saved
candidate. These are a post-hoc extension, not a replacement for the old scores.

| Run | Policy | Original 43 | Extended 45 | Failure in extended checks | Files | Largest / total lines |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| Pair 1, strong prompt | v1 | 42 | 44 | Lint | 7 | 141 / 674 |
| Pair 1, with linter | v1 | 42 | 43 | Package API, checked twice | 7 | 131 / 645 |
| Pair 2, strong prompt | v1 | 41 | 42 | Lint and package API, checked twice | 7 | 130 / 641 |
| Pair 2, with linter | v1 | 42 | 43 | Package API, checked twice | 6 | 193 / 710 |
| Pair 3, strong prompt | v1 | 41 | 43 | Lint and validation order | 6 | 206 / 599 |
| Pair 3, with linter | v1 | 41 | 42 | Lint and package API, checked twice | 9 | 157 / 722 |
| Confirmation 1 | v2 | 43 | 45 | None found | 7 | 257 / 781 |
| Confirmation 2 | v2 | 43 | 44 | Standalone API loses 52 names | 8 | 159 / 776 |
| Final validation | v3 | — | 43 | Validation order and standalone API | 4 | 394 / 671 |

The package checks overlap; two failed cases can represent one import defect.
The final run was evaluated directly with 45 cases. All three development runs
passed their frozen lint policy. Confirmation times were 136 and 293 seconds;
final validation took 144 seconds.

There is direct evidence of agents following the new diagnostic: confirmation
2 introduced ten wildcard imports, received ten `F403` findings with guidance,
and replaced all ten without reviewer feedback. Its
[diagnostic log](../refactoring_evaluation/runs/confirmation2-linter/lint.jsonl)
records that sequence. Confirmation 1 and final validation also removed wildcard
imports after findings. This demonstrates correction of a specific shortcut.
It does not demonstrate preservation of the whole public API: confirmation 2's
fallback import branch retained only its five CLI dependencies.

Policy v3 clarified that `SPY003` and `F401` require the full public API in every
supported import mode. The [final protocol](../refactoring_evaluation/FINAL_VALIDATION.md)
fixed one further run and prohibited more tuning or candidates in this
experiment. That agent still changed validation order and lost standalone
exports, despite clean lint. Its four-module split also left reporting,
presentation, export, demo, and CLI responsibilities together in a 394-line
facade. We retained the result and stopped as planned.

### What this supports, and what it does not

The tool can make a specific design shortcut visible and get a smaller coding
agent to correct it. The experiment also produced a real Ruff configuration
fix and clearer, tested feedback. These are useful outcomes.

It has **not** proved a general correctness or module-design advantage over a
good prompt. All controls already met the line limit. The final stronger-guidance
candidate remained incorrect. Static checks cannot establish validation order,
runtime import compatibility, or complete behavior preservation; those require
project tests and review. Named imports and `__all__` alone do not prove that
both branches of a compatibility facade expose the same names.

The study covers one synthetic, already sectioned application and one model.
Generated datasets broaden inputs within that application, not across projects.
The development confirmations reused the task after failure analysis and are
not an independent holdout. Review was not blind, runs were not seeded, and
there is no significance claim or Ruff-only ablation. The API check covers the
57 declared public names, not accidental standard-library re-exports, all import
relocations, pickling, or every possible input. Type-shape checks are not a
static proof of type correctness.

Workspace boundaries were instructions on a shared filesystem, not enforced
isolation. Pair 1's linter agent wrote five draft files outside its run via
relative patch paths. They were moved out of the repository and their hashes
and the agent's post-run audit are saved. The agent reported no reading of other
runs or withheld tests; that is not independently enforced evidence. There were
nine coding rollouts and one post-run audit call, with no parent repairs to
candidate code.

To establish broader value, a subsequent study needs unseen real projects,
enforced workspace isolation, and strong-prompt, Ruff-only, and anti-slop-python
conditions. Those are next experiments, not claims made by this one.

All prompts, candidate hashes, first completions, per-case results, diagnostics,
policy patches, and reproduction commands are in
[`examples/refactoring_evaluation`](../refactoring_evaluation/README.md).
The repository tests replay the saved behavior outcomes, including expected
failures, without model calls. The oversized original remains unchanged.

## Historical guided trial: 2026-09-05

The following record describes the earlier trial and its review repair. Its
reported test counts belong to that point in time.

This trial checks whether a smaller coding agent can use the `SPY003` diagnostic
to refactor the order-report example while preserving its behavior.

### Setup

- Date: 2026-09-05.
- Agent: `gpt-5.6-luna`, medium reasoning.
- The agent started without the parent conversation history.
- The original `src/example_project/order_report.py` remained at its existing path.
- The agent received an identical copy in `src/example_project/order_report_refactored/`.
- The agent could edit only that copied directory. The linter and configuration
  were outside its assigned scope.
- The parent prepared independent regression checks in
  `tests/test_order_report_refactoring.py` at the repository root.

The original file has 554 physical lines and this SHA-256 digest:

```text
29d3ce2a3d1263a2976222833704050da85b22a2e66b733c35ee5f8d8f8ac223
```

### Agent prompt

The following is the task prompt, with the local checkout path replaced by
`<repository-root>`. The runtime also supplied its common system and developer
instructions. The agent received no proposed module layout from the parent.

> Work in <repository-root>. Refactor the order-report example by following anti-slop-python's diagnostic guidance. First run `UV_CACHE_DIR=/tmp/anti-slop-python-uv-cache uv run anti-slop-python examples/basic_project/src/example_project/order_report.py` and read its output. The original file must remain unchanged. An identical copy is ready at examples/basic_project/src/example_project/order_report_refactored/order_report.py. Make all changes inside the order_report_refactored directory, including any new modules. Keep its order_report.py as the public import and direct-script entry point; preserve the original public functions, types, constants, CLI options, and behavior. Run anti-slop-python over the entire refactored directory until it passes. Verify behavior against the original. Do not modify linter code, configuration, exclusions, or thresholds. Do not commit or push. Read applicable AGENTS.md instructions. Use the installed uv environment; `uv run python -m pytest` works if the pytest executable is unavailable. Report the initial diagnostic, your module layout, checks performed, and any limitations. This is a single-agent trial; do not spawn further agents.

### Evaluation

A successful result must pass the linter across every extracted module. The
parent also compares the original and refactored versions for:

- Demo stdout and all four exported files, byte for byte.
- CSV input with rounding, discounts, shipping thresholds, ordering, stock
  shortages, multiple customers, and empty orders.
- Invalid quantities, references, dates, shipping methods, amounts, duplicate
  records, and the order of validation failures.
- CLI help, argument errors, public callable parameters and annotation presence,
  constants, and demo data values.
- Preservation of the original file by its SHA-256 digest.

Passing the checks is separate from the design review. That review looks for
cohesive responsibilities, clear imports, and attempts to satisfy the line limit
through compression or weakened contracts.

### First completion and review

The agent separated models, parsing, pricing, inventory, report aggregation,
presentation, exports, and demo data. `order_report.py` became a CLI and public
import facade. All nine files were under 500 lines, with no rule suppressions
or threshold changes.

The parent tests were available in the shared checkout during the agent's run.
They were independently written, but were not withheld. The agent reported that
they caught missing facade exports and constants, plus a changed validation
order. It fixed those failures before its first completion. The first completed
candidate passed all 28 regression cases and the linter.

The parent's design review found remaining defects that those checks missed:

- Five public functions had lost parameter and return annotations:
  `format_money`, `render_invoice_header`, `render_invoice_lines`,
  `render_invoice_totals`, and `load_report`.
- Several explicit keyword constructors had become positional calls;
  `parse_customer` used a generator unpack. These rewrites were unnecessary
  for separating responsibilities and made the field mapping less clear.
- Some explicit local collection annotations were removed.

The parent added an annotation-preservation assertion, verified that it failed,
and asked the same agent to restore annotations and the original keyword
arguments while keeping its module boundaries. The parent did not edit the
refactored implementation. This was a review repair, not a success achieved by
diagnostic guidance alone.

### Final result

The same agent completed the review repair. The parent then reran the checks:

- All 140 repository tests passed, including the 28 refactoring cases with the
  new annotation-preservation assertion.
- The whole refactored directory passed `anti-slop-python` with exit code 0
  and no output.
- Repository Ruff checks, the source/test self-check, and formatting checks
  passed. The refactored files also passed an explicit formatting check because
  the root project excludes examples.
- The original SHA-256 digest was unchanged.
- A static check of the relative imports found no dependency cycles.

| Module | Lines | Responsibility |
| --- | ---: | --- |
| `order_report.py` | 155 | Public API exports and CLI |
| `parsing.py` | 129 | CSV loading and validation |
| `exports.py` | 83 | Text, CSV, and JSON file export |
| `models.py` | 73 | Shared record types |
| `presentation.py` | 71 | Text rendering |
| `pricing.py` | 70 | Invoice calculations |
| `reporting.py` | 65 | Workflow and aggregate totals |
| `demo.py` | 53 | Sample data |
| `inventory.py` | 23 | Stock requests and shortages |

The split follows responsibilities and uses explicit imports. Total source
length grew from 554 to 722 lines, mainly from imports and the compatibility
facade. The result passes because each module has a smaller scope, rather than
because the agent removed enough source lines.

This is evidence that a smaller model can use the guidance with regression tests
and review. The first completion also exposed a gap: the guidance should make
preservation of type annotations and avoidance of unrelated rewrites explicit.
The linter's guidance was not changed during this trial.

After the trial, version `0.2.0` added Ruff's annotation rules to the default
policy. Missing function annotations now fail the linter directly. The test
counts and results above describe the policy at the time of the trial.

Reproduce the final checks from the repository root:

```console
uv run anti-slop-python examples/basic_project/src/example_project/order_report_refactored
uv run python -m pytest tests/test_order_report_refactoring.py
uv run python examples/basic_project/src/example_project/order_report_refactored/order_report.py --demo
```

### Limits

This is one guided trial, without a comparison run that omits the guidance.
It can demonstrate that this agent followed the guidance on this example; it
cannot establish that the guidance caused the result or that agents will
reliably follow it on other projects. The starting module already has section
comments that identify its responsibilities. The regression cases cover selected
behavior, not every possible input or external caller.

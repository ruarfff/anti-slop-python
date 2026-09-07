# Reproducible coding-agent comparison

This directory preserves nine first-completion refactors, including failures.
Read the [trial report](../basic_project/REFACTOR_TRIAL.md) for the results and
limits. The initial comparison did not establish a correctness advantage over
a strong prompt. Later runs showed agents correcting wildcard imports in
response to feedback, while some still broke behavior or public imports.

The original before-fix example and the earlier reviewed refactor remain in
`examples/basic_project`. No saved candidate here was repaired after completion.
These snapshots are evidence, not recommended implementations. Do not format,
fix, or lint-autofix them in place; their source hashes are checked.

## Replay without a coding model

Run from the repository root:

```sh
uv sync --locked --dev
uv run python -m pytest tests/test_refactoring_evaluation.py
```

The nine replay tests verify candidate hashes and reproduce each saved behavior
and API outcome using 45 child cases per candidate. Expected failures are part
of the record: a passing replay test means the outcome was reproduced, not that
the saved refactor is correct. The replay excludes the lint case from outcome
comparison because current policy differs from the original tool. Product tests
cover current policy independently.

To inspect one candidate directly, use a fresh output directory:

```sh
uv run python examples/refactoring_evaluation/evaluate.py \
  examples/refactoring_evaluation/runs/confirmation1-linter/candidate \
  /tmp/anti-slop-confirmation-replay --include-import-modes
```

This candidate passes all 45 cases and exits 0. The other eight snapshots each
fail at least one case under the current policy and exit 1. Output includes
`results.json`, `pytest.txt`, and JUnit `tests.xml`. A test/setup error is not a
successful evaluation. Omit `--include-import-modes` to run the original 43 cases.
The output directory must not already exist.

Calibration can also run without a model:

```sh
uv run python examples/refactoring_evaluation/calibrate.py \
  /tmp/anti-slop-calibration-replay
```

It checks the known repaired refactor and four deliberately bad alternatives:
unchanged oversized source, an empty entry point, a removed annotation, and a
changed tax rate. These controls establish detection of selected failures.

## Replay a frozen lint policy

The study used Python 3.14.7 and Ruff 0.16.5. `uv.lock` records dependencies;
Python is selected separately. Different interpreters or Ruff versions can
change diagnostics. Use the recorded versions when comparing exact policy
outcomes. The normal regression replay also runs on the repository's supported
CI interpreter.

Policy v1 is the implementation at commit
`d708c168ddd91ba98a36e478b18af54a8007bee8`. Policies v2 and v3 are stored as patches
against that same commit, not sequential patches. The patches reconstruct exact
tool source hashes in the corresponding run manifests.

For example, restore v2 into a fresh directory and replay confirmation 2:

```sh
mkdir /tmp/anti-slop-frozen-v2
git archive d708c168ddd91ba98a36e478b18af54a8007bee8 src/anti_slop_python \
  | tar -x -C /tmp/anti-slop-frozen-v2
git -C /tmp/anti-slop-frozen-v2 apply \
  "$PWD/examples/refactoring_evaluation/policies/v2.patch"
uv run python examples/refactoring_evaluation/evaluate.py \
  examples/refactoring_evaluation/runs/confirmation2-linter/candidate \
  /tmp/anti-slop-frozen-v2-replay \
  --tool-path /tmp/anti-slop-frozen-v2/src --include-import-modes
```

Expected: 44 passes, a standalone-export failure, exit 1. Omit the patch for v1;
use `v3.patch` against a fresh v1 extraction for the final validation. Run records
identify the appropriate policy. `manifest.json` maps each `tool/` source file
to its SHA-256; that prefix corresponds to `src/` in this extraction.

`evaluate.py` starts pytest in the saved candidate's project directory, beside
its `pyproject.toml`, and passes absolute paths. Pair 3's original linter run had
two stray modules outside `candidate/` that changed Ruff's import classification.
Its independent snapshot fails `I001` even though its workspace log ended with
exit 0. Replay deliberately does not restore those stray files. Earlier results
from running pytest in the repository root are retained separately.

## Start a new model run

The helpers prepare and capture workspaces; they do not call a model API or add
a model dependency. This example snapshots the **current** tool:

```sh
uv run python examples/refactoring_evaluation/prepare.py \
  /tmp/anti-slop-new-linter linter
```

Use `control` for a matched run without lint access. Start a fresh coding agent
with the generated `prompt.txt`, an explicit working directory, the recorded
model/settings, and no previous conversation. Both conditions receive the common
prompt, reference source, four CLI smoke comparisons, and the same time ceiling.
The tool wrapper records its diagnostics in `lint.jsonl`. Do not give the agent
the withheld evaluator or earlier candidates. For stronger isolation, run future
trials in separate containers with only the prepared workspace mounted.

At the first completion, capture before inspecting withheld results:

```sh
uv run python examples/refactoring_evaluation/archive.py \
  /tmp/anti-slop-new-linter /tmp/anti-slop-new-snapshot
uv run python examples/refactoring_evaluation/evaluate.py \
  /tmp/anti-slop-new-snapshot/candidate /tmp/anti-slop-new-results \
  --tool-path /tmp/anti-slop-new-linter/tool --include-import-modes
```

Save the agent's public completion, actual model/settings and start/finish times,
and any workspace-boundary violations alongside the archive. `archive.py`
reports changed immutable files; treat them as protocol violations, not normal
success. It does not enforce access boundaries. Starting a fresh model run is
not deterministic reproduction: seeds, temperature, tokens, and cost were not
exposed by the runtime used for this study.

Do not continue a completed agent with evaluator feedback and then replace its
first result. A repair is a separate intervention. The original comparison,
v2 confirmations, and final v3 validation have separate frozen protocols.

## Artifact map

| Artifact | Purpose |
| --- | --- |
| `PROTOCOL.md` | Initial three-pair design and review criteria, fixed before dispatch |
| `CONFIRMATION.md` | Two v2 development runs and replay-context correction |
| `FINAL_VALIDATION.md` | Post-hoc import probes and one final v3 run; no further tuning |
| `prompt.md`, `control.md`, `linter.md` | Common strong prompt and condition-specific instructions |
| `experiment.json` | All nine runs, model/settings, timing, policy, metrics, and unavailable fields |
| `calibration.json` | Original evaluator's positive and negative controls |
| `policies/*.patch` | Exact v2 and v3 changes from v1 |
| `runs/*/prompt.txt` | Exact rendered task supplied to that agent |
| `runs/*/manifest.json` | Original source, tool, prompt, and evaluator hashes |
| `runs/*/capture.json` | Saved candidate hashes and immutable-file audit |
| `runs/*/candidate/` | Unmodified first-completion source |
| `runs/*/agent_report.md` | Agent's public completion report, not independently accepted proof |
| `runs/*/lint.jsonl` | Wrapper calls, diagnostics, elapsed time, and exit codes; absent for controls |
| `runs/*/results.json`, `pytest.txt` | Original 43-case results under that run's policy; final run uses 45 directly |
| `runs/*/extended_results.json`, `extended_pytest.txt` | All nine candidates with two extra import-mode probes |
| `runs/*/repository_cwd_results.json` | Earlier repository-root replay of the original six candidates |
| `runs/*/structure.json` | Static import graph, wildcard locations, and definition changes to aid review |
| `runs/*/extra_workspace_files.json` | Application drafts found outside a candidate |
| `unscoped_files.json`, `runs/pair1-linter/audit.md` | Shared-workspace write violation and post-run agent explanation |

The 43-case evaluator is `tests/test_order_report_refactoring.py`; its hash was
fixed before the original agents. `tests/test_order_report_import_modes.py`
contains the later two-case extension. `tests/test_refactoring_evaluation.py`
replays the nine named snapshots and verifies their source hashes. Static graph
and AST metrics support source review; they do not replace runtime import checks
or prove design quality.

Absolute local paths in prompts and captured test output record the original
run context. They are historical data, not paths needed to run the replay.
The ordinary Ruff configuration excludes `examples/`, where intentional failures
and immutable candidate snapshots live. Check harness formatting explicitly
without touching those snapshots:

```sh
uv run ruff format --check examples/refactoring_evaluation/*.py
uv run ruff check examples/refactoring_evaluation/*.py
```

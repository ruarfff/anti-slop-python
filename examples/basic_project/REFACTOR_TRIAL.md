# Coding-agent refactoring trials

The linter helped agents correct specific problems, but this test did not show
that it produced more correct refactors than a good prompt alone.

## First trial: 2026-09-05

We asked `gpt-5.6-luna`, with medium reasoning, to use the linter's guidance to
split the 554-line `order_report.py` into smaller modules.

The agent made a sensible split, but dropped type annotations and made unrelated
changes. It fixed these after review. The result passed the tests and linter,
but needed help from tests and a reviewer. We added default annotation checks
after this trial.

The [original](src/example_project/order_report.py) and
[reviewed refactor](src/example_project/order_report_refactored/) remain as examples.

## Comparison: 2026-09-07

To see whether the linter added value, we ran three pairs of fresh agents using
the same model and settings. Each started with the original file, no conversation
history, and a 12-minute limit.

Both groups received a prompt asking them to split code by responsibility and
preserve types, public functions, outputs, and error handling. Both could run
behavior checks. One group also had to run anti-slop-python on all resulting
modules and follow its guidance. Agents could not change the lint settings or
suppress findings.

We prepared tests before the runs to check report outputs, invalid inputs,
validation order, types, and public imports. Agents were told not to read these
tests. We evaluated every first completion without a review or repair round.

| Approach | Passed behavior and public-interface checks |
| --- | ---: |
| Good prompt alone | 1 of 3 |
| Same prompt plus linter | 0 of 3 |

All six agents brought every module below 500 lines. Most failures involved
broken package imports; one agent changed the order of validation errors.
Lint findings were counted separately from behavior failures.

One agent replaced named imports with `import *`, which the old policy allowed.
Another agent's lint pass could not be repeated outside its workspace because
stray files affected Ruff's import checks. Smaller files and clean lint were not
enough to show that the refactor worked.

## Changes from the findings

We made three changes:

- Enabled `F403` to reject wildcard imports.
- Added guidance to preserve public exports with named imports and `__all__`,
  keep types and validation order, and check every supported way of importing
  or running the module.
- Fixed Ruff's relative configuration paths so checks use the project's settings
  consistently when run from another directory.

## Follow-up runs

Two fresh agents used the updated linter. Both passed the original tests.
Review then found a gap in our tests: one refactor lost 52 public names when
imported as a standalone module, even though package imports worked.

We added checks for both import modes and applied them to every completed run.
Only one of the two follow-up refactors passed the expanded checks. The earlier
results above were unchanged.

The new feedback did help with a specific problem. One follow-up agent introduced
ten wildcard imports. `F403` flagged all ten, and the agent removed them without
reviewer help.

We clarified the guidance to preserve the full public interface in every import
mode, then ran one final fresh agent. It still lost public names and changed
validation order, despite passing the linter. We recorded that failure and
stopped. The comparison and follow-ups covered nine runs in total.

## What this tells us

The tool can catch known shortcuts and guide an agent toward a fix. It cannot
confirm that a refactor preserves behavior. Tests and review are still needed.

This was one small example with existing section comments and one model. Later
runs reused that example after we had seen the failures. We did not compare
against Ruff alone, and the reviewer knew which agents used the linter.
Workspaces shared a computer; access limits were instructions, and one agent
wrote outside its assigned folder. These limits prevent broader claims about
effectiveness across Python projects.

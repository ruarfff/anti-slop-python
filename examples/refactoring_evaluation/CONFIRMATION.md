# Development confirmation, frozen before dispatch

After all six original completions were saved, their withheld checks exposed
package import failures, a validation-order change, wildcard imports and lint
suppressions. This motivated the following changes:

- SPY003 guidance explicitly asks agents to preserve validation order, side
  effects and type information, and to check package imports and entry points.
- F401 guidance describes public exports through named imports and `__all__`.
- F403 is enabled by default, with guidance to use named imports. Existing Ruff
  overrides and policy notices remain supported.
- Ruff subprocesses run from each configuration's directory, with absolute file
  arguments. Separate minimal reproductions showed caller-dependent source roots
  and exclusions. Investigation began with four extra I001 findings when replaying
  pair3-linter from the repository root.

Run two fresh agents concurrently with the same model, settings, source, common
prompt, linter-condition prompt, smoke test and 12-minute ceiling. Each gets the
updated tool snapshot. Do not provide the failed candidates, withheld tests or
reviewer instructions, and do not repair their first completions. Capture and
evaluate both outcomes, including failures. No further policy tuning will be
included in these two results.

These are development confirmations on the same application, after inspecting
the initial results. They are not an untouched project holdout or a new randomized
control comparison. They cannot separate the effects of the added rule, guidance
changes and Ruff context fix. The original six results remain unchanged in their
own records.

## Replay correction

The behavioral evaluator source and its 43 cases remain unchanged. The replay
launcher now starts pytest from the candidate's project directory. Re-evaluate
**all** original snapshots with the frozen old tool in that context. Retain the
earlier repository-root results as `repository_cwd_results.json`.

Further inspection found two stray application drafts at pair3-linter's workspace
root. They affect Ruff's first-party import classification. Changing the replay
directory alone therefore does not remove its four I001 findings: the independent
candidate intentionally excludes those drafts. Report the logged in-workspace
lint pass separately from the saved candidate's lint failure. This result is not
evidence that the production cwd fix repairs non-self-contained refactors.

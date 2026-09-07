# Final development validation

Both first confirmations passed the original 43 cases. Source review then found
that confirmation2-linter only re-exported five of the original 57 declared public
names in standalone import mode. Its package import passed. The new
`tests/test_order_report_import_modes.py` reproduces the loss of 52 names in a
fresh process; this exposes an evaluator gap rather than changing its old score.

Retain the original 43-case outcomes. Add two separate checks for package and
standalone import modes, and run those against **all** saved candidates. Keep
their results distinct as extended evaluation. The earlier repaired example
must pass both additional checks.

Clarify SPY003 and F401 guidance to require the complete public API in every
supported import mode. Do not add a speculative import-flow analysis rule:
F403 detects wildcard syntax, while import compatibility needs executable checks.

Run exactly one more fresh gpt-5.6-luna agent, medium reasoning, same common prompt
and linter condition, same source, same smoke test and 12-minute limit. Freeze
the updated tool and all 45 checks before dispatch. Provide no reviewer feedback
or previous candidates. Save the first completion and report it even if it fails.
Do not tune further or run more candidates in this experiment.

This is another development confirmation on the same task, not an independent
project holdout. Report the two earlier confirmations' 43-case success alongside
the newly observed standalone-import failure. Do not present all three as a
single pre-registered experiment.

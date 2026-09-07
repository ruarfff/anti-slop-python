# Basic rule demonstration

This small project demonstrates the current `anti-slop-python` policy. The
`violations.py` module contains seven intentional native and Ruff-backed
violations. The `preferred.py` module shows clearer alternatives for those rules.
`order_report.py` demonstrates `SPY003` with an oversized working module.
`order_report_refactored/` contains the result of a coding-agent refactoring
trial. The original remains unchanged. The project's
`pyproject.toml` does not repeat the policy because `anti-slop-python` supplies the
defaults.

`annotation_violations.py` adds an intentional example for each of the nine
Ruff annotation rules enabled by the policy.
`wildcard_violations.py` demonstrates `F403`; `explicit_exports.py` shows a named
public re-export through `__all__`.

| Code | Demonstration |
| --- | --- |
| `SPY001` | Replace a container of `Any` with a specific element type |
| `SPY002` | Replace dynamic attribute access with direct access |
| `SPY003` | Refactor the oversized `order_report.py` module |
| `ANN001`, `ANN002`, `ANN003` | Annotate parameters, `*args`, and `**kwargs` |
| `ANN201`, `ANN202`, `ANN204`, `ANN205`, `ANN206` | Annotate function and method returns |
| `ANN401` | Replace an `Any` parameter with its actual type |
| `F403` | Preserve public exports with named imports and `__all__` |
| `C901` | Replace a complex decision chain with data |
| `PLR0915` | Replace a long sequence of statements with one operation |
| `TID251` | Replace runtime patching with dependency injection |
| `E722` | Replace a bare exception handler with a specific exception |
| `BLE001` | Replace `except Exception` with a specific exception |

From the repository root, scan the project explicitly:

```console
$ uv run anti-slop-python examples/basic_project
```

The command reports 18 diagnostics: seven from `violations.py`, nine from
`annotation_violations.py`, `SPY003` from `order_report.py`, and `F403` from
`wildcard_violations.py`. It exits with status 1. `preferred.py`,
`explicit_exports.py`, and `order_report_refactored/` produce no diagnostics:

```console
$ uv run anti-slop-python examples/basic_project/src/example_project/preferred.py
```

## Module-size refactoring exercise

`order_report.py` is a before-fix example of a small order-reporting tool that
grew into one large module. It loads CSV files, calculates invoices, checks
stock, and produces text, CSV, and JSON reports. Its functions stay small enough
to pass the function-size and complexity checks, but the file exceeds 500 lines.

Check the size violation, then run the built-in demo:

```console
uv run anti-slop-python examples/basic_project/src/example_project/order_report.py
uv run python examples/basic_project/src/example_project/order_report.py --demo
```

The demo uses only the standard library and built-in data. It prints two orders,
a notebook stock shortage, and a grand total of `USD 63.97`. Add
`--output /tmp/order-report-before` to save text, CSV, and JSON outputs for
comparison after refactoring.

The agent's refactored version has its own entry point. Check all of its modules
and run its demo from the repository root:

```console
uv run anti-slop-python examples/basic_project/src/example_project/order_report_refactored
uv run python examples/basic_project/src/example_project/order_report_refactored/order_report.py --demo
uv run python -m pytest tests/test_order_report_refactoring.py
```

See [the trial record](REFACTOR_TRIAL.md) for the original guided trial and a
nine-run follow-up with strong-prompt controls, saved failures, and replayable
checks. The original file remains the before-fix exercise; the refactored
directory is the earlier reviewed result, not a selected comparison winner.

Suggested coding-agent prompt:

> Copy examples/basic_project/src/example_project/order_report.py to a separate
> working directory, run anti-slop-python on the copy, and fix SPY003 there.
> Preserve public imports, type contracts, validation order, CLI and report outputs.
> Check the full public API through package and standalone imports, plus each
> supported entry point.
> Organize the code by responsibility,
> without suppressing the rule, raising the limit, or compressing the source.
> Run the demo before and after the change and compare all exported reports.

The root project excludes `examples/` from Ruff and pre-commit checks because
these violations are intentional. Its direct self-check targets `src` and
`tests`.

# anti-slop-python

[![PyPI - Version](https://img.shields.io/pypi/v/anti-slop-python)](https://pypi.org/project/anti-slop-python/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/anti-slop-python)](https://pypi.org/project/anti-slop-python/)
[![skills.sh](https://skills.sh/b/ruarfff/anti-slop-python)](https://skills.sh/ruarfff/anti-slop-python)
[![License: MIT](https://img.shields.io/github/license/ruarfff/anti-slop-python)](LICENSE)

`anti-slop-python` is a small, opinionated architectural
linter for Python inspired by and largely copied from
[dmmulroy/anti-slop](https://github.com/dmmulroy/anti-slop).

It requires [ruff](https://github.com/astral-sh/ruff) so it is not a standalone linter.

`anti-slop-python` does not attempt to determine whether code was written by a human
or an agent. It rejects patterns that weaken evidence about types, invariants,
boundaries, and dependencies.

It also catches very common issues when using LLMs to generate Python code like functions
and files getting way too big.

## Setup

### Install it using the agent skill

The repository includes `install-anti-slop-python`, an Agent Skill that
installs and configures anti-slop-python in a target Python repository.

The [`skills` CLI](https://github.com/vercel-labs/skills) supports project and
global installs for many coding agents.

```bash
# Install interactively for the current project
npx skills add ruarfff/anti-slop-python --skill install-anti-slop-python
```

Make the skill available everywhere on your system:

```bash
npx skills add ruarfff/anti-slop-python --skill install-anti-slop-python --agent '*' --global --yes
```

See the [`skills` CLI documentation](https://github.com/vercel-labs/skills#supported-agents).

### Install it with pre-commit

This repository applies `anti-slop-python` to itself through the local hook in
`.pre-commit-config.yaml`.

The repository includes hook metadata. Add this entry to
`.pre-commit-config.yaml` and replace the revision with the release to use:

```yaml
repos:
  - repo: https://github.com/ruarfff/anti-slop-python
    rev: v0.2.0
    hooks:
      - id: anti-slop-python
```

Run against an entire project:

```bash
uv run pre-commit run anti-slop-python --all-files
```

#### Adopt it for selected directories

Use pre-commit's `files` regular expression to limit the hook to selected
parts of a project:

```yaml
repos:
  - repo: https://github.com/ruarfff/anti-slop-python
    rev: v0.2.0
    hooks:
      - id: anti-slop-python
        files: ^(?:src/a-specific-module/|tests/tests-for-that-module/)
```

Useful if you want to gradually introduce `anti-slop-python` to a project.

Expand the `files` expression as more directories adopt the policy.
This does not override the project's Ruff configuration for files outside the selected directories.

#### Exclude specific files during adoption

To adopt the module-size limit incrementally, add a hook-level `exclude` in
`.pre-commit-config.yaml` for existing large files:

```yaml
repos:
  - repo: https://github.com/ruarfff/anti-slop-python
    rev: v0.2.0  # Replace with the release to use.
    hooks:
      - id: anti-slop-python
        exclude: ^(?:src/legacy/reporting\.py|tests/test_legacy_reporting\.py)$
```

The [pre-commit filter](https://pre-commit.com/#regular-expressions) is a regular
expression over repository-relative paths. The anchors and escaped dots make
this example match only the two named files. Remove each path as its file is
refactored to meet the limit. This filter also applies to
`pre-commit run anti-slop-python --all-files`.

This skips **all checks in this hook** for those files, including other native
rules and Ruff-backed checks. It does not disable only `SPY003`. A separate Ruff
hook or command can still check them.

Native rules do not currently support per-file rule ignores. Ruff's
`per-file-ignores`, Ruff exclusions, and `# noqa: SPY003` do not disable
`SPY003`. The pre-commit filter also does not apply to direct CLI runs such as
`anti-slop-python .`. For direct runs, pass only the files or directories ready
for enforcement, for example:

```console
uvx anti-slop-python src/new_package/ tests/test_new_package.py
```

## Rules

Native `anti-slop-python` rules cover some checks that Ruff does not provide:

| Rule | Name | Rejected pattern |
| --- | --- | --- |
| SPY001 | `no-any-containers` | `dict`, `list`, `set`, or `tuple` parameterized with `Any` (including their `typing` aliases) |
| SPY002 | `no-dynamic-attribute-access` | Calls to `getattr()`, `setattr()`, or `delattr()` |
| SPY003 | `too-many-module-lines` | Modules over 500 physical lines, or test modules over 1,500; both limits are configurable |

### Ruff-backed policy

`anti-slop-python` uses Ruff for checks that Ruff already provides. It enables this
policy by default:

| Rule | Default policy |
| --- | --- |
| [`ANN001`, `ANN002`, `ANN003`](https://docs.astral.sh/ruff/rules/#flake8-annotations-ann) | Require annotations on function parameters, including `*args` and `**kwargs` |
| [`ANN201`, `ANN202`, `ANN204`, `ANN205`, `ANN206`](https://docs.astral.sh/ruff/rules/#flake8-annotations-ann) | Require return annotations on public/private functions and special, static, and class methods |
| [`ANN401`](https://docs.astral.sh/ruff/rules/any-type/) | Reject `Any` on function arguments |
| [`F403`](https://docs.astral.sh/ruff/rules/undefined-local-with-import-star/) | Require named imports instead of wildcard imports |
| [`C901`](https://docs.astral.sh/ruff/rules/complex-structure/) | Cyclomatic complexity of at most 10 |
| [`PLR0915`](https://docs.astral.sh/ruff/rules/too-many-statements/) | At most 40 statements per function or method |
| [`TID251`](https://docs.astral.sh/ruff/rules/banned-api/) | Ban `unittest.mock.patch` and `mock.patch` |
| [`E722`](https://docs.astral.sh/ruff/rules/bare-except/) | Reject bare exception handlers |
| [`BLE001`](https://docs.astral.sh/ruff/rules/blind-except/) | Reject broad exception handlers |

No Ruff configuration is required when you run `anti-slop-python`. Its defaults are
equivalent to:

```toml
[tool.ruff.lint]
extend-select = ["ANN", "BLE001", "C901", "E722", "F403", "PLR0915", "TID251"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-statements = 40

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"mock.patch".msg = "Avoid patching state. Pass the dependency explicitly instead."
"unittest.mock.patch".msg = "Avoid patching state. Pass the dependency explicitly instead."
```

Project Ruff settings remain authoritative. Use them only when the project
must change or extend the defaults. For example:

```toml
[tool.ruff.lint]
extend-ignore = ["C901"]

[tool.ruff.lint.pylint]
max-statements = 50
```

`ignore` and `extend-ignore` disable default rules. Explicit thresholds,
exclusions, per-file ignores, and `noqa` comments also apply.

Relative Ruff paths, including source roots and exclusions, resolve from the
directory containing that project's Ruff configuration. Checking a project from
its parent directory uses the same settings as checking from the project itself.

If the project defines the `TID251` banned-API table, it replaces the default
provided by `anti-slop-python`.

Inline `noqa` comments can suppress a recommended Ruff diagnostic, so
`anti-slop-python` audits them and prints a non-failing policy notice with the
source location. Ruff exclusions apply to Ruff-backed checks. Native SPY rules
still check every Python file in the paths passed to `anti-slop-python`; use the
command paths or pre-commit `files`/`exclude` settings to control that scope.

When a Ruff override is weaker than the default policy, `anti-slop-python` prints a
non-failing policy notice. Stricter settings do not produce a notice. The
defaults apply only to Ruff runs started by `anti-slop-python`; add the equivalent
configuration above if a separate `ruff check` command must enforce the same
policy.

## Why these rules exist

These rules do not identify whether an LLM wrote the code. Humans produce the
same patterns.

The rules here are an opinionated set of guidelines that cover common issues
with LLM generated code and are an attempt to reduce the review burden.

An agent can add a large amount of locally plausible code without first "learning" the
project's types, boundaries, or dependency design. The rules help against some common
shortcuts LLMs use to make code fulfill an immediate goal while making later changes
harder to reason about.

The rules also try to encourage better design by pushing back on the most annoying
things LLMs tend to do like writing massive functions, files with thousands of lines,
tests that patch and mock everything, etc.

The following are some example rules and why they were added:

### SPY001 — Do not put `Any` in containers

`SPY001` rejects `dict`, `list`, `set`, and `tuple` types parameterized with
`Any`, including the equivalent aliases from `typing`. A container usually
carries data across several lines, functions, or layers. Once its element type
becomes `Any`, every value taken from it escapes useful static checking and can
spread uncertainty through the rest of the program.

An agent often introduces this pattern when it can see that a value is a list
or dictionary but has not established the shape of the contents. `Any` makes
the immediate type error disappear without resolving that missing knowledge.
The rule forces the implementation to name the real type. A burden you probably
wouldn't always want for yourself but an LLM can deal with it and maybe produce
better code because of it.

Ruff's [`ANN401`](https://docs.astral.sh/ruff/rules/any-type/) rule is related
but does not replace `SPY001`: `ANN401` checks function parameters annotated
directly with `Any`, while `SPY001` checks for `Any` inside container types such
as `list[Any]` and `dict[str, Any]`.

### SPY002 — Do not hide attributes behind strings

`SPY002` rejects calls to `getattr()`, `setattr()`, and `delattr()`. Dynamic
attribute access turns an interface into a runtime string convention. Type
checkers and refactoring tools have less evidence, misspelled names fail late,
and a default passed to `getattr()` can hide a missing invariant.

Generated code often uses `getattr(value, "name", None)` to support several
assumed object shapes without checking which shapes the application actually
allows. The rule requires direct attribute access for a known interface.

Ruff has related [`B009`](https://docs.astral.sh/ruff/rules/get-attr-with-constant/),
[`B010`](https://docs.astral.sh/ruff/rules/set-attr-with-constant/), and
preview-only [`B043`](https://docs.astral.sh/ruff/rules/del-attr-with-constant/)
rules. They flag `getattr()`, `setattr()`, and `delattr()` only when the
attribute name is a constant string. They therefore allow calls such as
`getattr(value, name)`, which may be intentional but still make an interface
depend on runtime strings. `SPY002` rejects
the built-ins regardless of whether the name is constant.

### SPY003 — Limit module size

`SPY003` allows 500 physical lines per production module and 1,500 per test
module by default. It counts code, comments, blank lines, and docstrings. A
final newline terminates the last line; it does not add another line. The
diagnostic appears at line 1 and includes the actual count and active limit.
Files with syntax errors report the syntax error instead of native diagnostics.
Native rules do not support `noqa` suppression.

For incremental adoption, see [Exclude specific files during adoption](#exclude-specific-files-during-adoption).

A module can contain many small, simple functions and still become hard to
maintain. This check complements Ruff's function size and complexity limits by
catching growth across the whole file. The 500-line limit is an opinionated
review threshold, not proof that a module has poor design.

When it fails, look for distinct responsibilities and move cohesive code into
focused modules. Do not remove useful documentation, compress code, or split
files at arbitrary line boundaries just to pass the check.

The diagnostic includes refactoring guidance. Each extracted module should have
a clear purpose and interface. Keep closely related code together, minimize
shared state and cross-module calls, and avoid circular imports. Moving unrelated
code into a generic helpers module does not improve the design. Preserve public
APIs and verify behavior after changing the boundaries.
Check package imports, standalone imports where supported, and every entry point.
Each supported import mode must retain the full public API.
Preserve validation order, side effects, and type information when moving code.

The [agent comparison](examples/basic_project/REFACTOR_TRIAL.md) records a strong
prompt baseline, repeated linter-guided runs, withheld behavior checks and the
failures that led to improvements. A clean lint result does not establish API
compatibility or correct behavior.

#### Test modules and configuration

Test modules can contain many independent scenarios, fixtures, and deliberate
repetition. Their larger budget helps keep related cases together. Files named
`test_*.py`, `*_test.py`, or `conftest.py` use the test limit automatically,
at any directory depth. Names are case-sensitive. Importing `pytest` or using
assertions does not change a file's classification. A helper such as
`tests/helpers.py` uses the production limit unless a configured pattern matches.

Set the limits and add test-helper paths in `pyproject.toml`:

```toml
[tool.anti-slop-python]
max-module-lines = 500
max-test-module-lines = 1500
test-file-patterns = ["tests/**", "specs/**"]
```

Limits must be positive integers. Patterns extend the automatic filename
conventions; an empty list keeps only those conventions. Patterns are matched
against the complete, case-sensitive path relative to this `pyproject.toml`,
using `/` separators. They use shell-style matching: `*` can span directories,
so `tests/**` includes both immediate and nested files. Absolute paths and `..`
segments are rejected. Patterns cannot classify files outside the configuration
directory as tests.

For each source file, the checker searches its directory and parents for the
nearest `[tool.anti-slop-python]` table. A nested `pyproject.toml` without this
table inherits the parent settings. A nearer table replaces the parent table;
omitted options use the defaults above. This works for direct file arguments,
directory scans, and pre-commit, regardless of the current working directory.
Invalid options stop the CLI with exit code 2.

Only the module-size budget changes for tests. Other native and Ruff-backed
rules still apply. Oversized tests receive guidance specific to test design:

```text
tests/test_orders.py:1:1 SPY003 Too many lines in test module (1620 > 1500)
  Group tests by the behavior or component they verify.
  Keep each scenario readable and preserve assertions and edge cases.
  Do not remove coverage, compress cases, or hide setup in shared fixtures
  merely to satisfy this limit.
```

For Python callers, `check_file()` discovers configuration automatically.
`check_source()` uses defaults without reading configuration files; pass a
`ModuleSizeSettings` instance from `anti_slop_python.configuration` with its
`settings=` argument to supply custom values. The `root` field sets the base
directory for additional test patterns. Invalid file configuration raises
`ConfigurationError` when calling `check_file()` directly.

### ANN — Keep function contracts explicit

The annotation rules require parameter and return types on functions and methods,
including private helpers, special methods, and variadic arguments. `ANN401`
also rejects `Any` on function arguments. Local variables can use type inference;
this policy does not require annotations on every assignment.

A refactoring agent can preserve runtime output while removing type information
that callers and type checkers need. These rules catch missing function
annotations even when the function moves to a different file. They check the
current source, not Git history, and do not establish that the annotations are
correct. Use a type checker to check their consistency with the implementation.

Keep the actual types when moving code. Do not replace them with `Any`, broad
`object` types, or casts merely to pass. Projects can adopt these Ruff-backed
rules incrementally without disabling other checks on a legacy file:

```toml
[tool.ruff.lint.per-file-ignores]
"src/legacy.py" = ["ANN"]
```

The native rules still run on that file, and ignored annotation rules produce
policy notices. This policy does not require explicit annotations on `self`
or `cls`. Ruff's annotation-specific settings remain project-controlled.

### F403 — Keep imports and public exports explicit

Wildcard imports hide which module provides a name. They can also hide unused
import findings during a refactor. Use named imports and preserve the intended
public API. For a facade that re-exports a name, declare it in `__all__`:

```python
from .pricing import calculate_tax

__all__ = ["calculate_tax"]
```

When Ruff reports `F401`, the output also explains how to preserve public
re-exports. Do not delete a public name or replace named imports with `import *`
merely to clear that finding. `F403` checks wildcard syntax; it does not verify
that imports resolve at runtime. Test imports and behavior separately.

For incremental adoption, retain a specific legacy facade while checking other
files and rules:

```toml
[tool.ruff.lint.per-file-ignores]
"src/legacy/__init__.py" = ["F403"]
```

This produces a policy notice. Native rules continue to run on the file.

### [`C901`](https://docs.astral.sh/ruff/rules/complex-structure/) — Limit decision complexity

`C901` measures the number of paths through a function. Anti-slop-python uses a
maximum McCabe complexity of 10. A function can be short and still be complex
when it contains many branches, loops, or exception paths. Each added path
increases the number of states that a reader and a test suite must consider.

Coding agents tend to tack on more complexity to achieve a goal like making tests pass.

### [`PLR0915`](https://docs.astral.sh/ruff/rules/too-many-statements/) — Limit function size

`PLR0915` rejects functions or methods with more than 40 statements. This
complements `C901`: a long function can have simple control flow and still do
too much. 

Generated implementations tend to keep the full requested workflow in one
function because that is the easiest shape to produce in one pass. The
statement limit makes things like mixed responsibilities more visible. 

### [`TID251`](https://docs.astral.sh/ruff/rules/banned-api/) — Do not patch dependencies

Ruff's `TID251` rule can ban project-selected APIs. Anti-slop-python uses it to ban
`unittest.mock.patch` and `mock.patch`. Patching replaces module or object
state at runtime, so a test depends on where a symbol happens to be imported
rather than on an explicit interface. Refactoring an import can then break the
test even when behavior has not changed.

Agents frequently reach for `patch()` because it can isolate almost any call
without changing production design. There's a tendency to test implementation rather than behavior
when trying to improve test coverage.

This setting helps a little with directing a clearer interface-based design, although it is generally 
not enough by itself and LLMs need a lot of direction to get to this kind of design.

### [`E722`](https://docs.astral.sh/ruff/rules/bare-except/) — Do not use bare exception handlers

`E722` rejects a bare `except:` handler. A bare handler catches
`BaseException`, including `KeyboardInterrupt` and `SystemExit`. It can prevent
a process from stopping and can disguise failures that the code cannot
actually recover from.

LLMs tend to be good at building exception handling but occasionally they take shortcuts and 
this helps avoid that. 

### [`BLE001`](https://docs.astral.sh/ruff/rules/blind-except/) — Do not catch broad exceptions

`BLE001` flags broad named handlers such as `except Exception` and
`except BaseException` when they handle or swallow the error. 

Ruff permits broad handlers that re-raise and recognized logging patterns 
that retain the exception trace.

A coding agent may wrap a large generated block in `except Exception` because it
does not know the operation's failure contract. This setting forces the agent to 
work through the possible errors and make them clear.

## Usage

Run Ruff and the native checker together on directories or individual Python
files:

```console
uvx anti-slop-python .
uvx anti-slop-python src/
uvx anti-slop-python src/anti_slop_python/cli.py
```

Diagnostics use a conventional source format, and any diagnostic makes the
command exit with status 1:

```text
src/api/parser.py:41:12 SPY001 Avoid containers parameterized with Any
  Describe the actual data with concrete types, TypedDict, or a dataclass.
  Validate untrusted data at the boundary; narrow unknown values before use.
  Do not remove annotations or hide Any behind aliases, casts, or bare containers.
src/api/parser.py:45:8 SPY002 Avoid dynamic attribute access
  Use direct attribute access for a known interface.
  For runtime choices, use an explicit mapping of supported operations.
  Preserve missing-value behavior explicitly.
  Do not replace this call with __dict__, vars(), or a reflection wrapper.
src/api/large_module.py:1:1 SPY003 Too many lines in module (642 > 500)
  Separate distinct responsibilities into cohesive modules with clear interfaces.
  Keep closely related code together and preserve public APIs and behavior.
  Preserve validation order, side effects, and type information when moving code.
  Verify package and standalone imports where supported, plus each entry point.
  Check that every supported import mode exposes the full public API.
  Do not compress code, remove useful comments, split at arbitrary line counts,
  or move unrelated code into a generic helpers module to satisfy this limit.
src/orders/service.py:18:5 C901 `create_order` is too complex (14 > 10)
  Simplify the decision model; extract cohesive operations with explicit inputs.
  Use a lookup table only when the branches represent a data mapping.
  Preserve edge cases; do not hide branches in lambdas or raise the limit.
```

Each native rule and recommended Ruff rule includes indented guidance after the
source line. It describes the intended design change and common shortcuts to
avoid. Other Ruff diagnostics retain their original output. Ruff's message,
including any project-defined banned-API explanation, remains on the first line.
When reading diagnostics through the Python API, `message` contains the summary;
`str(diagnostic)` includes the source location and guidance.

| Rule | Guidance |
| --- | --- |
| `ANN` | Declare real parameter and return types; preserve existing type information |
| `SPY001` | Describe and validate the actual data instead of hiding `Any` |
| `SPY002` | Use explicit interfaces and preserve missing-value behavior |
| `SPY003` | Separate production responsibilities or group tests by behavior; preserve related code and test coverage |
| `F401`, `F403` | Keep public exports through named imports and `__all__`; check every supported import mode |
| `C901` | Simplify decisions while preserving edge cases |
| `PLR0915` | Extract meaningful steps while preserving ordering and side effects |
| `TID251` | Follow the project's API policy; pass dependencies when test isolation is needed |
| `E722` | Catch specific recoverable errors and allow interrupts to propagate |
| `BLE001` | Handle known failures; do not add logging or defaults just to silence the rule |

Policy notices are written to standard error and do not change the exit code:

```text
anti-slop-python policy notice: C901 is disabled; recommended: enabled
```

Ruff runs in check-only mode even if the project has `fix = true`.

For local development:

```console
uv sync --dev
uv run pre-commit install
uv run anti-slop-python src tests
uv run pre-commit run --all-files
uv run pytest
uv run ruff format --check .
uv run ruff check .
```

## Examples

[`examples/basic_project`](examples/basic_project) is a small Python project
with intentional native and Ruff-backed violations, plus preferred
alternatives. This repository's Ruff and pre-commit checks exclude `examples/`;
its direct self-check targets `src` and `tests`.

Run the example explicitly to see its diagnostics:

```console
uv run anti-slop-python examples/basic_project
```

The [agent comparison](examples/basic_project/REFACTOR_TRIAL.md) records nine
fresh refactoring runs, including a strong-prompt control and saved failures.
It shows agents correcting specific lint findings, but does not establish an
overall refactor-correctness advantage. The
[evaluation harness](examples/refactoring_evaluation) replays those outcomes
without model calls.

## Scope and limitations

Native checks use Python's built-in `ast` and a pragmatic import alias map.
They do not perform scope-aware name resolution, type checking, cross-file
analysis, suppressions, or autofixes. Native configuration currently covers only
module-size limits and additional test-file patterns. Ruff-backed checks use
the project's effective Ruff configuration and suppression behavior.

## Releases

Version `0.2.0` adds module-size enforcement, function annotation checks,
explicit-import checks, and refactoring guidance. Versions come from Git tags
through `hatch-vcs`.
The publishing workflow selects at least `v0.2.0` for the next untagged `main`
commit, then continues with patch increments. Opening a PR does not publish a
release; publishing runs after eligible changes reach `main`.

## License

[MIT](LICENSE)

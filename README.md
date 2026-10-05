# jtest

A testing framework for Jo, with a shared API and Python and Ruby runners.

| Package | Platform | Provides |
| --- | --- | --- |
| `jtest` | pure | Suite declarations, assertions, and assertion results |
| `jtest-python` | python | `jtest.Runner` on Python |
| `jtest-ruby` | ruby | `jtest.Runner` on Ruby |

Both runners expose the same `jtest.Runner` API. Select one runner for the
module's platform. The core and runner share the `jtest` namespace, outside
Jo's implicitly imported `jo` namespace.

## Install

In your project's `jo.toml`:

```toml
jo = "0.13"

[module.tests]
kind = "app"
depth = 2
platform = "python"
enable-ffi = true
src = ["tests/"]
packages = [
  { name = "jtest-python", version = "0.1" },
]
```

For Ruby, change `platform` to `"ruby"` and the runner dependency to `jtest-ruby`.
The test source stays the same. `depth = 2` allows the runner's dependency on
the shared core package. All three packages are available in the public registry.

## Write tests

```jo
import jo.IO.stdout
import jo.IO.args
import jtest.Testing
import jtest.Runner
import jtest.suite
import jtest.test
import jtest.checkEquals
import jtest.thisSuite

def main(): Unit receives stdout, args =
  val root = Testing.define("my tests", () => suites())
  assert: Runner.runWithArgs(root), "tests failed"

private def suites(): Unit receives thisSuite =
  suite: "math", () =>
    test: "adds numbers", () =>
      checkEquals("one plus one", 1 + 1, 2)
```

```sh
jo run tests
jo run tests -- math
jo run tests -- "math/adds numbers"
```

Assertions accumulate failures and retain their source locations. Unexpected
exceptions fail the current test, and execution continues. The runner returns
`false` on failure; the example assertion makes the application exit unsuccessfully.

Filters are test-path prefixes. The root's name is not part of a path. A filter
that matches no tests succeeds and skips all suite fixtures.

## Fixtures and parallel execution

Set `thisSuite.beforeSuite = () => setup()` for a once-per-run fixture. Only
selected suites are prepared, outermost first. Fixture exceptions abort the run.

Set `thisSuite.parallel = true` on a nested suite whose direct children are
independent. Parallel child suites share a pool; serial child suites preserve
their ordering. A parallel suite inside a serial child can start another pool,
so the worker count is a per-pool limit, not a global concurrency limit.
The root is a declaration container; put parallel work in a nested suite.

Reports stay in declaration order. Terminal progress is redrawn in place; CI
logs receive periodic progress lines. `NO_COLOR` disables terminal colors.

`JTEST_WORKERS` sets the default worker count, otherwise the host's available
CPU count is used. `Runner.run(root, filter, lanes)` overrides it: negative
values use the default, and zero selects one worker.

## Development

Use Jo 0.13.11, Python 3.12+, Ruby 3.3+, and JDK 17+.

```sh
jo run test-python
jo run test-ruby
python3 scripts/check-output.py
jo package core
jo package python
jo package ruby
```

Both backends run the same conformance tests. The intentional failing test
scenarios verify reporting and exception recovery; the overall command succeeds
only when all conformance checks pass. `src/runner/` is shared source compiled into
each runner package; `src/python/` and `src/ruby/` supply the host operations.

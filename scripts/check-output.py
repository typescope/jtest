"""Check reporting parity and clean failure exits on both backends."""

import re
import subprocess
from pathlib import Path


def report(platform):
    result = subprocess.run(
        ["jo", "run", f"test-{platform}"], capture_output=True, text=True, check=True
    )
    output = result.stdout
    assert "CONFORMANCE PASSED" in output, output
    assert "failure alpha (tests/Tests.jo:" in output, output
    assert "failure beta: expected [2] but got [1]" in output, output
    assert "before exception" in output and "expected exception" in output, output
    assert "1 passed, 2 failed" in output, output
    assert "0 passed, 0 failed, 3 skipped" in output, output
    assert "\x1b[" not in output, "redirected output must not contain ANSI escapes"
    return re.sub(r" in [0-9.]+s", " in <elapsed>s", output)


def failure_report(platform):
    result = subprocess.run(
        ["jo", "run", f"test-{platform}-failure"], capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, (result.returncode, output)
    assert (
        "intentional failure: intentional (test-fixtures/failure/Run.jo:"
        in result.stdout
    ), output
    assert "0 passed, 1 failed" in result.stdout, output
    assert "Traceback" not in output, output
    assert "SystemExit" not in output, output
    assert "tests failed" not in output, output
    assert "src/runner/Runner.jo" not in output, output
    return re.sub(r" in [0-9.]+s", " in <elapsed>s", result.stdout)


if __name__ == "__main__":
    assert Path("jo.toml").exists(), "run from the repository root"
    assert report("python") == report("ruby"), "backend reports differ"
    assert failure_report("python") == failure_report("ruby"), (
        "backend failure reports differ"
    )
    print("Python and Ruby reports match; failure exits are clean")

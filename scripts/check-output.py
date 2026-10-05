"""Check observable reporting parity after building the conformance apps."""

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


if __name__ == "__main__":
    assert Path("jo.toml").exists(), "run from the repository root"
    assert report("python") == report("ruby"), "backend reports differ"
    print("Python and Ruby reports match")

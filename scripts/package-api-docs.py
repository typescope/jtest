#!/usr/bin/env python3
"""Package generated Jo API docs and SHA-512 checksums for a GitHub release."""

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


PACKAGES = {"core": "jtest", "python": "jtest-python", "ruby": "jtest-ruby"}


def package_docs(version, output, root=Path(".")):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError(f"expected a release version such as 0.2.0, got {version!r}")
    sources = []
    for module, package in PACKAGES.items():
        source = root / ".build" / module / "doc"
        for name in ("index.html", "data.js"):
            if not (source / name).is_file():
                raise ValueError(f"missing {source / name}; run jo doc {module}")
        data = json.loads((source / "data.js").read_text().split("=", 1)[1].rstrip(";\n"))
        if data["meta"].get("version") != version:
            raise ValueError(f"{source}: generated docs do not match version {version}")
        if data.get("home") != (root / "README.md").read_text():
            raise ValueError(f"{source}: regenerate docs with --readme README.md")
        sources.append((package, source))

    output.mkdir(parents=True, exist_ok=True)
    for package, source in sources:
        archive = output / f"{package}-api-docs-v{version}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    target = Path(package) / version / path.relative_to(source)
                    zipped.write(path, target.as_posix())
        digest = hashlib.sha512(archive.read_bytes()).hexdigest()
        archive.with_name(archive.name + ".sha512").write_text(f"{digest}  {archive.name}\n")
        print(archive)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        package_docs(args.version, args.output)
    except ValueError as error:
        parser.exit(1, f"{error}\n")

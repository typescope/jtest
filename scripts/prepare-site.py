#!/usr/bin/env python3
"""Download released API docs and prepare the changelog for the Zola site."""

import argparse
import hashlib
import io
import json
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


ASSET_BASE = "https://github.com/typescope/jtest/releases/download"


def read_url(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def unpack_docs(archive, destination, version):
    prefix = PurePosixPath(version)
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        for member in zipped.namelist():
            path = PurePosixPath(member)
            if ".." in path.parts or "\\" in member or not path.is_relative_to(prefix):
                raise ValueError(f"unexpected API archive path: {member}")
        for name in ("index.html", "data.js"):
            if f"{prefix}/{name}" not in zipped.namelist():
                raise ValueError(f"{version}: API archive is missing {name}")
        zipped.extractall(destination)


def prepare_site(root, asset_base=ASSET_BASE):
    docs = root / "docs"
    versions = [
        json.loads(line)["version"]
        for line in (docs / "api-versions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    if not versions or any(not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v) for v in versions):
        raise ValueError("api-versions.jsonl must list stable release versions")
    if len(set(versions)) != len(versions):
        raise ValueError("api-versions.jsonl contains a duplicate version")
    latest = max(versions, key=lambda v: tuple(map(int, v.split("."))))

    # Build in a temporary directory so a failed download cannot publish partial docs.
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        for version in versions:
            name = f"jtest-docs-v{version}.zip"
            url = f"{asset_base.rstrip('/')}/v{version}/{name}"
            archive = read_url(url)
            checksum = read_url(url + ".sha512").decode().split()
            if not checksum or hashlib.sha512(archive).hexdigest() != checksum[0]:
                raise ValueError(f"checksum mismatch: {url}")
            unpack_docs(archive, staging, version)
            print(f"jtest {version}: /api/{version}/")

        target = f"../{latest}/"
        alias = staging / "latest"
        alias.mkdir()
        (alias / "index.html").write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            '<title>jtest API</title>'
            f'<meta http-equiv="refresh" content="0;url={target}">'
            f'<script>location.replace("{target}" + location.search + location.hash)</script>'
            f'<a href="{target}">Read jtest {latest} API documentation</a></html>\n'
        )

        destination = docs / "static" / "api"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(staging, destination)

    (docs / "api-docs.json").write_text(json.dumps({"version": latest, "path": "api/latest/"}) + "\n")
    # Nest the changelog headings below the page's single h1.
    changelog = re.sub(r"(?m)^(#{1,5}) ", r"#\1 ", (root / "CHANGELOG.md").read_text())
    (docs / "changelog.md").write_text(changelog)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-base", default=ASSET_BASE)
    args = parser.parse_args()
    prepare_site(Path("."), args.asset_base)

"""Exercise unified release archives, version selection, and failed site preparation."""

import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


package = load_script("package-api-docs")
site = load_script("prepare-site")


class DocsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.assets = self.root / "releases"
        self.source = self.root / "generated-docs"
        self.readme = self.root / "README.md"
        (self.root / "docs").mkdir()
        self.readme.write_text("# jtest\n\nRelease introduction.\n")
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.10.0]\n\n### Fixed\n\n- A fix.\n")
        versions = ["0.2.0", "0.10.0"]
        (self.root / "docs/api-versions.jsonl").write_text(
            "".join(json.dumps({"version": version}) + "\n" for version in versions)
        )
        self.source.mkdir()
        (self.source / "index.html").write_text("<!doctype html><title>API</title>")
        (self.source / "assets").mkdir()
        (self.source / "assets/app.js").write_text("// doc app")
        for version in versions:
            data = {
                "meta": {"version": version}, "home": self.readme.read_text(),
                "symbols": {"jtest.Testing": {}, "jtest.Runner": {}},
            }
            (self.source / "data.js").write_text("var JO_DOC_DATA=" + json.dumps(data))
            package.package_docs(version, self.source, self.assets / f"v{version}", self.readme)

    def test_archive_contains_readme_core_runner_and_complete_doc_tree(self):
        archive = self.assets / "v0.2.0/jtest-docs-v0.2.0.zip"
        digest = archive.with_name(archive.name + ".sha512").read_text().split()[0]
        self.assertEqual(digest, hashlib.sha512(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive) as zipped:
            self.assertIn("0.2.0/assets/app.js", zipped.namelist())
            data = json.loads(zipped.read("0.2.0/data.js").split(b"=", 1)[1])
            self.assertEqual(data["home"], self.readme.read_text())
            self.assertIn("jtest.Testing", data["symbols"])
            self.assertIn("jtest.Runner", data["symbols"])

    def test_latest_is_semantic_and_old_versions_remain_accessible(self):
        site.prepare_site(self.root, self.assets.as_uri())
        metadata = json.loads((self.root / "docs/api-docs.json").read_text())
        self.assertEqual(metadata, {"version": "0.10.0", "path": "api/latest/"})
        base = self.root / "docs/static/api"
        self.assertTrue((base / "0.2.0/index.html").is_file())
        self.assertTrue((base / "0.10.0/index.html").is_file())
        self.assertIn("../0.10.0/", (base / "latest/index.html").read_text())
        self.assertIn("location.hash", (base / "latest/index.html").read_text())
        self.assertIn("## Changelog", (self.root / "docs/changelog.md").read_text())

    def test_corrupt_download_preserves_existing_site(self):
        destination = self.root / "docs/static/api"
        destination.mkdir(parents=True)
        (destination / "existing.html").write_text("published docs")
        archive = self.assets / "v0.2.0/jtest-docs-v0.2.0.zip"
        archive.write_bytes(archive.read_bytes() + b"corrupted")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            site.prepare_site(self.root, self.assets.as_uri())
        self.assertEqual((destination / "existing.html").read_text(), "published docs")

    def test_archive_rejects_paths_outside_its_version(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("0.2.0/../../escape.html", "unexpected")
        with self.assertRaisesRegex(ValueError, "unexpected API archive path"):
            site.unpack_docs(archive.getvalue(), self.root / "unpacked", "0.2.0")

    def test_missing_doc_files_fail_before_extraction(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("0.2.0/index.html", "API")
        with self.assertRaisesRegex(ValueError, "missing data.js"):
            site.unpack_docs(archive.getvalue(), self.root / "unpacked", "0.2.0")

    def test_packaging_rejects_wrong_version_and_stale_readme(self):
        with self.assertRaisesRegex(ValueError, "do not match version"):
            package.package_docs("0.2.0", self.source, self.root / "output", self.readme)
        self.readme.write_text("Updated introduction")
        with self.assertRaisesRegex(ValueError, "regenerate docs with --readme"):
            package.package_docs("0.10.0", self.source, self.root / "output", self.readme)

    def test_packaging_requires_both_core_and_runner(self):
        data = json.loads((self.source / "data.js").read_text().split("=", 1)[1])
        del data["symbols"]["jtest.Runner"]
        (self.source / "data.js").write_text("var JO_DOC_DATA=" + json.dumps(data))
        with self.assertRaisesRegex(ValueError, "core and shared runner docs together"):
            package.package_docs("0.10.0", self.source, self.root / "output", self.readme)


if __name__ == "__main__":
    with contextlib.redirect_stdout(io.StringIO()):
        unittest.main()

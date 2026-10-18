"""Exercise release archives, version selection, and failed site preparation."""

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
        (self.root / "docs").mkdir()
        (self.root / "README.md").write_text("# jtest\n\nRelease introduction.\n")
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.10.0]\n\n### Fixed\n\n- A fix.\n")
        versions = ["0.2.0", "0.10.0"]
        (self.root / "docs/api-versions.jsonl").write_text(
            "".join(json.dumps({"version": version}) + "\n" for version in versions)
        )
        for version in versions:
            for module in package.PACKAGES:
                source = self.root / ".build" / module / "doc"
                source.mkdir(parents=True, exist_ok=True)
                (source / "index.html").write_text("<!doctype html><title>API</title>")
                data = {"meta": {"version": version}, "home": (self.root / "README.md").read_text()}
                (source / "data.js").write_text("var JO_DOC_DATA=" + json.dumps(data))
                (source / "assets").mkdir(exist_ok=True)
                (source / "assets/app.js").write_text("// doc app")
            package.package_docs(version, self.assets / f"v{version}", self.root)

    def test_release_archives_contain_readme_and_complete_doc_tree(self):
        for name in package.PACKAGES.values():
            archive = self.assets / "v0.2.0" / f"{name}-api-docs-v0.2.0.zip"
            digest = archive.with_name(archive.name + ".sha512").read_text().split()[0]
            self.assertEqual(digest, hashlib.sha512(archive.read_bytes()).hexdigest())
            with zipfile.ZipFile(archive) as zipped:
                self.assertIn(f"{name}/0.2.0/assets/app.js", zipped.namelist())
                data = json.loads(zipped.read(f"{name}/0.2.0/data.js").split(b"=", 1)[1])
                self.assertEqual(data["home"], (self.root / "README.md").read_text())

    def test_latest_is_semantic_and_old_versions_remain_accessible(self):
        site.prepare_site(self.root, self.assets.as_uri())
        metadata = json.loads((self.root / "docs/api-docs.json").read_text())
        self.assertEqual(len(metadata["libraries"]), 3)
        for library in metadata["libraries"]:
            self.assertEqual(library["version"], "0.10.0")
            base = self.root / "docs/static/api" / library["name"]
            self.assertTrue((base / "0.2.0/index.html").is_file())
            self.assertTrue((base / "0.10.0/index.html").is_file())
            self.assertIn("../0.10.0/", (base / "latest/index.html").read_text())
            self.assertIn("location.hash", (base / "latest/index.html").read_text())
        self.assertIn("## Changelog", (self.root / "docs/changelog.md").read_text())

    def test_corrupt_download_preserves_existing_site(self):
        destination = self.root / "docs/static/api"
        destination.mkdir(parents=True)
        (destination / "existing.html").write_text("published docs")
        archive = self.assets / "v0.2.0/jtest-api-docs-v0.2.0.zip"
        archive.write_bytes(archive.read_bytes() + b"corrupted")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            site.prepare_site(self.root, self.assets.as_uri())
        self.assertEqual((destination / "existing.html").read_text(), "published docs")

    def test_archive_rejects_paths_outside_its_package_and_version(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("jtest/0.2.0/../../escape.html", "unexpected")
        with self.assertRaisesRegex(ValueError, "unexpected API archive path"):
            site.unpack_docs(archive.getvalue(), self.root / "unpacked", "jtest", "0.2.0")

    def test_missing_doc_files_fail_before_extraction(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("jtest/0.2.0/index.html", "API")
        with self.assertRaisesRegex(ValueError, "missing data.js"):
            site.unpack_docs(archive.getvalue(), self.root / "unpacked", "jtest", "0.2.0")

    def test_packaging_rejects_wrong_version_and_stale_readme(self):
        with self.assertRaisesRegex(ValueError, "do not match version"):
            package.package_docs("0.2.0", self.root / "output", self.root)
        (self.root / "README.md").write_text("Updated introduction")
        with self.assertRaisesRegex(ValueError, "regenerate docs with --readme"):
            package.package_docs("0.10.0", self.root / "output", self.root)


if __name__ == "__main__":
    with contextlib.redirect_stdout(io.StringIO()):
        unittest.main()

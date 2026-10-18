# Releases

All three packages share a version and are published as assets of one release
in `typescope/jtest`. Their registrations in `typescope/packages` use namespace
`jtest`, their respective runtimes, and `[publish].github = "typescope/jtest"`.

1. Set all three package versions in `jo.toml`.
2. Use the CI compiler version and run both conformance apps and the report
   parity check from README.md.
3. Run `jo package core`, `jo package python`, and `jo package ruby`. Generate
   and package the API documentation as described below.
4. Inspect each artifact's `meta.toml`. The core must be pure with no package
   dependencies; each runner must depend only on the matching core version.
5. Verify every `.sha512` file from its `.build/<module>/release/` directory.
6. Commit the reviewed sources, wait for green CI, tag that commit `vVERSION`,
   and publish each package's `.joy`, source ZIP, and checksums, plus the unified
   API documentation ZIP and its checksum.
7. Once registrations are merged, trigger `sync-releases.yml` in
   `typescope/packages` and verify all three versions at `pkg.jo-lang.org`.
8. Publish the API docs website: add the version to `docs/api-versions.jsonl`
   in a PR, wait for its merge and the Pages deployment, then verify the live
   root redirect and version URLs as described below.

Never replace published artifacts or move a published tag. Package registration
is a reviewed PR; leave merges to a maintainer. Do not switch downstream users
until all three versions are available from the public registry.

## API documentation assets

Generate one API site from the same clean, merged release commit as the
packages, using the CI compiler. Compile the core and shared runner sources
together, with `README.md` as the home page. Python host helpers supply the
private implementation names needed for type checking; the public runner API
is shared with Ruby and appears only once.

Set `VERSION` to the package version in `jo.toml`:

```sh
VERSION=0.2.1
API_DIR="/tmp/jtest-api-v$VERSION"
jo compile --doc --use-runtime-api python --title jtest --project-version "$VERSION" \
  --readme README.md --out "$API_DIR" \
  src/core/*.jo src/runner/*.jo src/python/*.jo
python3 scripts/package-api-docs.py "$VERSION" --source "$API_DIR" \
  --output "/tmp/jtest-docs-release/v$VERSION"
```

The script checks the version, README, and presence of both the core and runner
API. It produces `jtest-docs-vVERSION.zip` and its `.sha512` file. The archive
contains `<version>/index.html`, `data.js`, and assets. Verify the checksum from
the output directory:

```sh
(cd "/tmp/jtest-docs-release/v$VERSION" && sha512sum --check *.sha512)
```

Include both files when creating the GitHub release alongside the package
assets. If the release already exists, add the new documentation assets with:

```sh
gh release upload "v$VERSION" "/tmp/jtest-docs-release/v$VERSION/"* \
  --repo typescope/jtest
```

Do not use `--clobber`. To add docs for an older release, check out its published
tag in a separate directory and use that release's compiler. Run the doc
compiler command from that checkout with its original README, then invoke
the current `package-api-docs.py` by its absolute path. Do not generate an
older version's API docs from current `main`.

## Publish the API docs website

After uploading the API assets, append `{"version": "VERSION"}` to
`docs/api-versions.jsonl` in a PR. Keep all existing entries: the site downloads
and verifies the archives for every listed version on every build. Only append
a version once its unified API archive and checksum are available in the release.

After this manifest PR is merged to `main`, the `Docs` workflow downloads all
listed API archives and publishes them to GitHub Pages. Wait for the deployment
from that merge commit to succeed:

```sh
gh run list --repo typescope/jtest --workflow docs.yml --branch main --limit 5
gh run watch RUN_ID --repo typescope/jtest --exit-status
```

Use the run ID for the merged manifest commit. A successful PR build validates
the site; the deployment runs after merge.

The site root redirects to the latest listed version. Documentation URLs are:

- `https://jtest.jo-lang.org/` → `https://jtest.jo-lang.org/0.2.1/`
- `https://jtest.jo-lang.org/<version>/`

The redirect preserves query strings and API symbol links. Previous version
paths remain accessible when a new release is added. The README in each API
archive is that version's home page.

Set the repository's Pages source to **GitHub Actions** and its custom domain
to **jtest.jo-lang.org** once. Configure DNS with a `CNAME` from
`jtest.jo-lang.org` to `typescope.github.io`, and enable **Enforce HTTPS** once
GitHub has issued the certificate. The custom domain is a repository Pages
setting for the Actions publishing workflow.

The `Docs` workflow checks PRs and deploys site changes merged to `main`.
To republish manually:

```sh
gh workflow run docs.yml --repo typescope/jtest --ref main
```

Wait for that run with the same commands above. Before announcing the docs,
open `https://jtest.jo-lang.org/` in a browser and confirm it redirects
to `/$VERSION/`. Check the versioned page, an API symbol link, and an earlier
version's URL. Verify the published doc files respond successfully:

```sh
curl --fail --silent --show-error --output /dev/null \
  "https://jtest.jo-lang.org/$VERSION/index.html"
curl --fail --silent --show-error --output /dev/null \
  "https://jtest.jo-lang.org/$VERSION/data.js"
```

Website publication is complete once the Pages deployment and these live
checks pass.

For a local preview, run:

```sh
python3 scripts/test-docs.py
python3 scripts/prepare-site.py
python3 -m http.server 8000 --directory docs/public
```

`prepare-site.py` builds the ignored `docs/public/` directory using Python's
standard library. It contains the root redirect and a directory for each version.

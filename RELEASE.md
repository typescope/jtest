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
   and publish the `.joy`, source ZIP, API documentation ZIP, and their checksums
   for every package.
7. Once registrations are merged, trigger `sync-releases.yml` in
   `typescope/packages` and verify all three versions at `pkg.jo-lang.org`.

Never replace published artifacts or move a published tag. Package registration
is a reviewed PR; leave merges to a maintainer. Do not switch downstream users
until all three versions are available from the public registry.

## API documentation assets

Generate documentation from the same clean, merged release commit as the
packages, using the CI compiler. All three modules use `README.md` as the API
documentation home page. Set `VERSION` to the package version in `jo.toml`:

```sh
VERSION=0.2.0
jo doc core
jo doc python
jo doc ruby
python3 scripts/package-api-docs.py "$VERSION" --output "/tmp/jtest-api-release/v$VERSION"
```

The script checks that the generated version and README match the checkout.
It produces these archives and a `.sha512` file for each:

- `jtest-api-docs-vVERSION.zip`
- `jtest-python-api-docs-vVERSION.zip`
- `jtest-ruby-api-docs-vVERSION.zip`

Each archive contains `<package>/<version>/index.html`, `data.js`, and assets.
Verify the checksums from the output directory:

```sh
(cd "/tmp/jtest-api-release/v$VERSION" && sha512sum --check *.sha512)
```

Include all six files when creating the GitHub release alongside the package
assets. If the release already exists, add the new documentation assets with:

```sh
gh release upload "v$VERSION" "/tmp/jtest-api-release/v$VERSION/"* \
  --repo typescope/jtest
```

Do not use `--clobber`. To add docs for an older release, check out its published
tag in a separate directory, use that release's compiler, and add the same
`--readme README.md` and package `--title` doc options if they are missing.
Generate and package from those released sources, including their original
README. Do not generate an older version's API docs from current `main`.

## GitHub Pages

After uploading the API assets, append `{"version": "VERSION"}` to
`docs/api-versions.jsonl` in a PR. Keep all existing entries: the site downloads
and verifies the archives for every listed version on every build. Only append
a version once its three API archives and checksums are available in the release.

The site shows only the latest version per package. Documentation URLs are:

- `https://typescope.github.io/jtest/api/<package>/latest/`
- `https://typescope.github.io/jtest/api/<package>/<version>/`

The latest aliases preserve API symbol links, and previous version paths remain
accessible when a new release is added. The changelog is rendered directly from
the repository's `CHANGELOG.md`.

Set the repository's Pages source to **GitHub Actions** once. The `Docs` workflow
checks PRs and deploys site changes merged to `main`. To republish manually:

```sh
gh workflow run docs.yml --repo typescope/jtest --ref main
```

For a local preview, install Zola 0.22.1, then run:

```sh
python3 scripts/test-docs.py
python3 scripts/prepare-site.py
zola --root docs serve
```

`prepare-site.py` regenerates ignored site data and the downloaded API tree;
generated `.build/` documentation is only read when packaging release assets.

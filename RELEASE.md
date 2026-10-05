# Releases

All three packages share a version and are published as assets of one release
in `typescope/jtest`. Their registrations in `typescope/packages` use namespace
`jtest`, their respective runtimes, and `[publish].github = "typescope/jtest"`.

1. Set all three package versions in `jo.toml`.
2. Use the CI compiler version and run both conformance apps and the report
   parity check from README.md.
3. Run `jo package core`, `jo package python`, and `jo package ruby`.
4. Inspect each artifact's `meta.toml`. The core must be pure with no package
   dependencies; each runner must depend only on the matching core version.
5. Verify every `.sha512` file from its `.build/<module>/release/` directory.
6. Commit the reviewed sources, wait for green CI, tag that commit `vVERSION`,
   and publish the `.joy`, source ZIP, and both checksums for every package.
7. Once registrations are merged, trigger `sync-releases.yml` in
   `typescope/packages` and verify all three versions at `pkg.jo-lang.org`.

Never replace published artifacts or move a published tag. Package registration
is a reviewed PR; leave merges to a maintainer. Do not switch downstream users
until all three versions are available from the public registry.

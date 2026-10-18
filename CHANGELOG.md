# Changelog

## [Unreleased]

### Added

- A GitHub Pages site with the changelog and unified API documentation for
  assertions, suites, and both runners. Earlier versions remain at versioned URLs.
- Release API documentation archives with the README as their introduction.

### Fixed

- `Runner.runWithArgs` uses normal process exit with status 1 after reporting
  failed tests on Python and Ruby, removing the extra runner exception
  traceback. ([#2](https://github.com/typescope/jtest/issues/2))

## [0.2.0] - 2026-10-13

### Breaking changes

- Requires Jo 0.14.0. The compiler uses SAST format 2.0, which is incompatible
  with the format used by Jo 0.13. Rebuild `jtest`, `jtest-python`, and
  `jtest-ruby` together with this release before using them in projects.
- `Runner.runWithArgs` now returns `Unit` and exits with a non-zero process
  status when any selected test fails. Remove wrappers such as
  `assert: Runner.runWithArgs(root), "tests failed"`. Use
  `Runner.run(root, filter, lanes)` when the caller needs to inspect or handle
  the Boolean result.

### Changed

- The README example and CI compiler now target Jo 0.14.0.

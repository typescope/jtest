# jtest contributor instructions

- `src/core/` is pure Jo. Keep host FFI out of it.
- `src/runner/` is compiled into both runner packages. Keep behavior shared.
- `src/python/` and `src/ruby/` implement the host operations.
- Both runners expose `jtest.Runner`; a module selects exactly one runner.
- Run `jo run test-python`, `jo run test-ruby`, and `python3 scripts/check-output.py`.
- Run `jo package core`, `jo package python`, and `jo package ruby` for package changes.
- Use `rg` for searches and preserve unrelated changes.
- Do not edit generated `.build/` output.
- Review the diff and report validation before handing off a change.

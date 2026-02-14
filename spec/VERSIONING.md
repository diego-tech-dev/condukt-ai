# Condukt Contract Versioning

This document defines contract-version rules for Condukt AST/trace interoperability.

## Current Contract Version

- `ast_version`: `1.1`
- `trace_version`: `1.1`

The schema file names (`ast-v1.schema.json`, `trace-v1.schema.json`) track the major line (`v1`).

## Compatibility Rules

1. Patch/minor updates within major `v1`:
- additive fields only
- existing required fields and semantics must remain stable
- old consumers may ignore unknown fields
- bump `AST_VERSION`/`TRACE_VERSION` minor (`1.x -> 1.y`)

2. Breaking changes:
- removing fields
- changing field meaning or requiredness
- changing core execution semantics encoded by trace contracts
- require major bump (`v2` schemas + new major contract version)

3. Change discipline:
- update `condukt/spec.py`
- update JSON schema `const` values
- update conformance tests/goldens
- update Rust bootstrap constants
- record decision in `DECISIONS.md`

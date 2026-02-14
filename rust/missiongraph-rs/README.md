# missiongraph-rs (bootstrap)

Rust bootstrap runtime for MissionGraph contract conformance.

This prototype focuses on AST/trace contract handling:

- validate AST JSON (`check-ast`)
- emit trace skeleton with `trace_version = "1.1"` (`trace-skeleton`)

## Usage

Generate AST from the Python reference runtime:

```bash
python3 -m missiongraph parse examples/ship_release.mgl > /tmp/ship_release.ast.json
```

Validate AST with Rust bootstrap:

```bash
cargo run --manifest-path rust/missiongraph-rs/Cargo.toml -- check-ast /tmp/ship_release.ast.json
```

Emit trace skeleton:

```bash
cargo run --manifest-path rust/missiongraph-rs/Cargo.toml -- trace-skeleton /tmp/ship_release.ast.json
```

Run Rust tests:

```bash
cargo test --manifest-path rust/missiongraph-rs/Cargo.toml
```

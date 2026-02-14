# MissionGraph Foundations

Last updated: 2026-02-14

This document captures foundational language/runtime design decisions.

For each dimension:
- decision state (`decided` or `leaning`)
- rationale
- accepted tradeoffs
- migration path if wrong
- agent-specific constraints

## 1) Type System

State: decided (v1), leaning for v2+

Decision:
- Use gradual, structural typing at orchestration boundaries.
- Keep static validation for declared contracts (`types`, `contracts`, typed artifacts).
- Keep runtime checks for worker payloads.
- Do not require global type inference or global soundness in v1.
- Do not add generics in v1.

Rationale:
- Workers are external/polyglot and cannot be fully typed by the orchestration language.
- Boundary safety gives high value with low complexity.
- Deterministic contract failures are more useful than partial compile-time guarantees that do not cover worker internals.

Tradeoffs:
- Some failures remain runtime-only.
- No generic abstraction yet; reusable schemas may be verbose.
- Not sound as a full-program type system.

Migration path:
- Introduce an edition-gated strict mode.
- Add generic type parameters for named type definitions after module/import semantics are stable.
- Keep v1 contract behavior as compatibility profile.

Agent-specific constraints:
- Agents compose unknown code; robust boundary contracts are more reliable than assuming internal type safety.

## 2) Memory Model And Ownership

State: decided (v1)

Decision:
- No user-visible shared-memory model in the DSL.
- Data exchange is value-style serialized payloads.
- `null` is allowed where schemas permit optional values.
- Thread safety for task internals is delegated to workers.

Rationale:
- MissionGraph orchestrates processes/tasks, not in-process memory mutation.
- Serialized boundaries align with sandboxed/stateless execution.

Tradeoffs:
- Cannot express low-level memory ownership policies.
- Performance overhead from serialization boundaries.

Migration path:
- If a long-lived in-runtime object model is introduced, add explicit ownership/shareability rules in IR and an edition gate.

Agent-specific constraints:
- Stateless execution and remote tool calls favor immutable, serialized handoffs.

## 3) Grammar And Parser Architecture

State: leaning (formalization pending)

Decision:
- Keep block-delimited syntax, not whitespace-sensitive syntax.
- Keep syntax mostly context-free; semantic checks live in validator/planner.
- Preserve deterministic parser behavior over clever syntax.

Rationale:
- Easier for humans and code-generating agents to produce valid programs.
- Lower ambiguity and easier recovery for tooling.

Tradeoffs:
- Current grammar is implementation-defined; no published formal grammar yet.
- Parser evolution may be harder to audit until grammar is formalized.

Migration path:
- Publish formal grammar (EBNF/PEG) and lock with parser conformance fixtures.
- Add a machine-readable grammar artifact for editor/toolchain support.

Agent-specific constraints:
- Agent code generation benefits from explicit delimiters and predictable parse outcomes.

## 4) IR And Compilation Pipeline

State: leaning (v1 direct path, v2 planned IR)

Decision:
- Current flow: parse AST -> validate -> execute.
- Treat versioned AST/trace as interoperability contracts.
- Plan a normalized plan IR as a future middle layer.

Rationale:
- Fast iteration while semantics converge.
- Contracts and goldens already provide stable boundaries across runtimes.

Tradeoffs:
- Fewer optimization hooks today.
- Some semantic logic is duplicated between runtime components.

Migration path:
- Introduce a normalized, explicit execution IR (resolved DAG, policies, contracts).
- Migrate executors to consume IR while preserving AST contract compatibility.

Agent-specific constraints:
- A stable IR will improve explainability, transformation safety, and autonomous refactoring workflows.

## 5) Module System And Visibility

State: leaning (not first-class in v1)

Decision:
- Keep single-program-file authoring model in v1.
- Defer module/import/visibility design until core execution semantics stabilize.

Rationale:
- Early usage is workflow-oriented; single file keeps complexity low.

Tradeoffs:
- Limited namespace hygiene and reuse at scale.
- Large programs can become harder to maintain.

Migration path:
- Add edition-gated `import` semantics, explicit visibility, and deterministic module resolution.
- Define cycle behavior explicitly (likely disallow semantic cycles).

Agent-specific constraints:
- Agents often emit focused programs quickly; module complexity was intentionally deferred, but is required for larger multi-team codebases.

## 6) Error Handling

State: decided (v1)

Decision:
- Use explicit task/result records with normalized `error_code` and `error` text.
- Use fail-fast orchestration semantics on critical violations.
- Avoid exception semantics in DSL.

Rationale:
- Machine-actionable errors are required for retries, policy branching, and observability.
- Error codes create stable automation contracts.

Tradeoffs:
- Less expressive than rich typed error algebra.
- Recovery composability is limited in v1.

Migration path:
- Add structured recovery constructs on top of existing error codes.
- Keep code taxonomy stable and additive.

Agent-specific constraints:
- Agents need deterministic, parseable failure surfaces, not runtime-specific exception formats.

## 7) Concurrency

State: decided (v1 core), leaning for advanced models

Decision:
- Concurrency is first-class via DAG levels, `parallel/sequential`, and `max_parallel`.
- Resilience policy (`timeout`, `retries`, `retry_if`, `backoff`, `jitter`) is first-class at task level.
- No shared-memory concurrency primitives in the DSL.

Rationale:
- The language models orchestration concurrency directly.
- Structured DAG execution avoids ad hoc race patterns.

Tradeoffs:
- No streaming/channel primitives yet.
- Limited fine-grained async control.

Migration path:
- Add explicit stream/channel artifacts and cancellation scopes without breaking DAG safety defaults.

Agent-specific constraints:
- Parallel independent agent steps are common; structured concurrency supports safe fan-out/fan-in.

## 8) Extensibility And Metaprogramming

State: decided (v1 guardrails)

Decision:
- No user macros, compiler plugins, or procedural metaprogramming in v1.
- Extensibility is through workers, schemas, and runtime/tooling APIs.

Rationale:
- Prevent dialect drift and preserve portability across runtimes.

Tradeoffs:
- Less syntactic abstraction power.
- Some repetitive patterns remain manual.

Migration path:
- If needed, add constrained declarative templates first (hygienic and deterministic), edition-gated.

Agent-specific constraints:
- Limiting metaprogramming keeps generated code interoperable and reviewable across autonomous agents.

## 9) ABI And FFI

State: decided (v1)

Decision:
- Primary interoperability boundary is schema-governed JSON and process invocation.
- Do not define a stable binary ABI in v1.

Rationale:
- Polyglot workers and sandbox boundaries are better served by protocol stability than in-process binary coupling.

Tradeoffs:
- Serialization and process overhead.
- Less direct access to low-level native libraries.

Migration path:
- Add optional transport/runtime backends (for example WASM host mode or RPC) behind the same logical contracts.

Agent-specific constraints:
- Agents frequently compose external tools across languages and environments; protocol-level FFI is the practical baseline.

## 10) Tooling

State: leaning (core in place, ecosystem incomplete)

Decision:
- Prioritize deterministic CLI and conformance tooling first.
- Keep schemas/goldens as toolchain truth for parity.
- Formatter/LSP/package manager are planned, not complete.

Rationale:
- Reliability and portability gates were higher priority than editor ergonomics at this stage.

Tradeoffs:
- Slower developer ergonomics for large teams.
- More manual style consistency today.

Migration path:
- Add deterministic formatter and queryable language server APIs over stable AST/IR.
- Add package/module tooling after module semantics are finalized.

Agent-specific constraints:
- Agents benefit immediately from deterministic CLI + JSON outputs; these already exist and are test-gated.

## 11) Evolution Strategy

State: decided (v1), leaning for editions

Decision:
- Use explicit contract versioning with governance (`spec/VERSIONING.md`).
- Treat breaking changes as major-line events.
- Require schema/golden/runtime updates in lockstep.

Rationale:
- Multi-runtime ecosystems require explicit compatibility discipline.

Tradeoffs:
- Higher process overhead for changes.
- Slower adoption of breaking cleanups.

Migration path:
- Introduce editions and migration tooling when first major breaking set appears.
- Keep previous edition behavior supported for a defined window.

Agent-specific constraints:
- Autonomous systems rely on stable contracts for unattended execution; ungoverned breakage is unacceptable.

## 12) Compilation Model

State: leaning (hybrid trajectory)

Decision:
- Keep interpreted/orchestrated execution model in v1.
- Grow Rust runtime incrementally for execution parity.
- Use conformance + parity matrix as runtime acceptance criteria.

Rationale:
- This provides fast feature iteration while progressively hardening a systems-runtime path.

Tradeoffs:
- Less ahead-of-time optimization today.
- Dual-runtime maintenance overhead during migration period.

Migration path:
- Add incremental plan caching/compilation units around normalized IR.
- Expand Rust from single-task prototype to full multi-task execution and trace assembly.

Agent-specific constraints:
- Ephemeral/sandboxed runs favor low-friction execution; cached/compiled pathways can be layered without semantic drift.

## Open Decision Register

Not yet fixed:
- formal grammar publication format and parser generator choice
- module/import syntax and visibility semantics
- generics and stricter typing roadmap details
- package manager and dependency resolution model
- edition mechanics and migration tooling UX

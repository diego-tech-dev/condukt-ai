---
title: "Interface: FailureDiagnosis"
---

[**condukt-ai**](../../readme/)

***

# Interface: FailureDiagnosis

Defined in: [diagnostics.ts:6](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L6)

Flattened diagnosis payload for the first failing task in a pipeline trace.

## Properties

### contract\_paths

> `readonly` **contract\_paths**: readonly `string`[]

Defined in: [diagnostics.ts:13](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L13)

***

### error?

> `readonly` `optional` **error**: `string`

Defined in: [diagnostics.ts:12](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L12)

***

### error\_code?

> `readonly` `optional` **error\_code**: `string`

Defined in: [diagnostics.ts:11](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L11)

***

### failed

> `readonly` **failed**: `boolean`

Defined in: [diagnostics.ts:8](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L8)

***

### failed\_at?

> `readonly` `optional` **failed\_at**: `string`

Defined in: [diagnostics.ts:14](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L14)

***

### pipeline

> `readonly` **pipeline**: `string`

Defined in: [diagnostics.ts:7](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L7)

***

### task?

> `readonly` `optional` **task**: `string`

Defined in: [diagnostics.ts:9](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L9)

***

### task\_index?

> `readonly` `optional` **task\_index**: `number`

Defined in: [diagnostics.ts:10](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L10)

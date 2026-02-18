---
title: "Interface: TaskRetryPolicy"
---

[**condukt-ai**](../../readme/)

***

# Interface: TaskRetryPolicy

Defined in: [pipeline/types.ts:16](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L16)

Retry behavior configuration for a single task.

## Properties

### backoffMs?

> `readonly` `optional` **backoffMs**: `number`

Defined in: [pipeline/types.ts:18](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L18)

***

### jitterMs?

> `readonly` `optional` **jitterMs**: `number`

Defined in: [pipeline/types.ts:19](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L19)

***

### retries?

> `readonly` `optional` **retries**: `number`

Defined in: [pipeline/types.ts:17](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L17)

***

### retryIf?

> `readonly` `optional` **retryIf**: `"error"` \| `"execution_error"` \| `"contract_violation"`

Defined in: [pipeline/types.ts:20](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L20)

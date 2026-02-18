---
title: "Interface: TaskDefinition\\<TOutput, TOutputs, TDependencies, TTaskId\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: TaskDefinition\<TOutput, TOutputs, TDependencies, TTaskId\>

Defined in: [pipeline/types.ts:79](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L79)

Task definition consumed by the pipeline runtime.

## Type Parameters

### TOutput

`TOutput` = `unknown`

Contract-validated output type for the task.

### TOutputs

`TOutputs` *extends* `TaskOutputMap` = `TaskOutputMap`

### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[] = readonly `TaskOutputKey`\<`TOutputs`\>[]

### TTaskId

`TTaskId` *extends* `string` = `string`

## Properties

### after?

> `readonly` `optional` **after**: `TDependencies`

Defined in: [pipeline/types.ts:87](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L87)

***

### description?

> `readonly` `optional` **description**: `string`

Defined in: [pipeline/types.ts:86](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L86)

***

### id

> `readonly` **id**: `TTaskId`

Defined in: [pipeline/types.ts:85](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L85)

***

### output

> `readonly` **output**: `StandardSchemaV1`\<`unknown`, `TOutput`\>

Defined in: [pipeline/types.ts:90](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L90)

***

### retry?

> `readonly` `optional` **retry**: [`TaskRetryPolicy`](taskretrypolicy/)

Defined in: [pipeline/types.ts:89](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L89)

***

### when()?

> `readonly` `optional` **when**: (`context`) => `boolean` \| `Promise`\<`boolean`\>

Defined in: [pipeline/types.ts:88](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L88)

#### Parameters

##### context

[`TaskRuntimeContext`](taskruntimecontext/)\<`TOutputs`, `TDependencies`\>

#### Returns

`boolean` \| `Promise`\<`boolean`\>

## Methods

### run()

> **run**(`context`): `Promise`\<[`TaskExecutionResult`](taskexecutionresult/)\>

Defined in: [pipeline/types.ts:91](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L91)

#### Parameters

##### context

[`TaskRuntimeContext`](taskruntimecontext/)\<`TOutputs`, `TDependencies`\>

#### Returns

`Promise`\<[`TaskExecutionResult`](taskexecutionresult/)\>

---
title: "Interface: TaskRuntimeContext\\<TOutputs, TDependencies\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: TaskRuntimeContext\<TOutputs, TDependencies\>

Defined in: [pipeline/types.ts:49](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L49)

Runtime context exposed to each task at execution time.

## Type Parameters

### TOutputs

`TOutputs` *extends* `TaskOutputMap` = `TaskOutputMap`

Full typed output map accumulated so far.

### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[] = readonly `TaskOutputKey`\<`TOutputs`\>[]

Task ids declared in `after`.

## Properties

### dependencyOutputs

> `readonly` **dependencyOutputs**: `Readonly`\<`Pick`\<`TOutputs`, `TDependencies`\[`number`\]\>\>

Defined in: [pipeline/types.ts:55](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L55)

***

### outputs

> `readonly` **outputs**: `Readonly`\<`TOutputs`\>

Defined in: [pipeline/types.ts:53](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L53)

***

### taskResults

> `readonly` **taskResults**: `Readonly`\<`Record`\<`string`, [`TaskTrace`](tasktrace/)\>\>

Defined in: [pipeline/types.ts:54](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L54)

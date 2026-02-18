---
title: "Function: tanstackChatTask()"
---

[**condukt-ai**](../../readme/)

***

# Function: tanstackChatTask()

> **tanstackChatTask**\<`TOutput`, `TAdapter`, `TOutputs`, `TDependencies`, `TTaskId`\>(`definition`): [`TaskDefinition`](../interfaces/taskdefinition/)\<`TOutput`, `TOutputs`, `TDependencies`, `TTaskId`\>

Defined in: [tanstack.ts:54](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/tanstack.ts#L54)

Builds a Condukt task from a TanStack AI adapter.

## Type Parameters

### TOutput

`TOutput`

### TAdapter

`TAdapter` *extends* `AnyTextAdapter`

### TOutputs

`TOutputs` *extends* `TaskOutputMap`

### TDependencies

`TDependencies` *extends* readonly `Extract`\<keyof `TOutputs`, `string`\>[]

### TTaskId

`TTaskId` *extends* `string`

## Parameters

### definition

[`TanStackChatTaskDefinition`](../interfaces/tanstackchattaskdefinition/)\<`TOutput`, `TAdapter`, `TOutputs`, `TDependencies`, `TTaskId`\>

## Returns

[`TaskDefinition`](../interfaces/taskdefinition/)\<`TOutput`, `TOutputs`, `TDependencies`, `TTaskId`\>

## Remarks

The adapter response is expected to be JSON text that satisfies `output`.

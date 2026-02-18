---
title: "Function: llmTask()"
---

[**condukt-ai**](../../readme/)

***

# Function: llmTask()

> **llmTask**\<`TOutput`, `TModel`, `TSettingsByModel`, `TSelectedModel`, `TOutputs`, `TDependencies`, `TTaskId`\>(`definition`): [`TaskDefinition`](../interfaces/taskdefinition/)\<`TOutput`, `TOutputs`, `TDependencies`, `TTaskId`\>

Defined in: [pipeline/llm.ts:56](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/llm.ts#L56)

Adapts an [LLMTaskDefinition](../type-aliases/llmtaskdefinition/) into a runtime [TaskDefinition](../interfaces/taskdefinition/).

## Type Parameters

### TOutput

`TOutput`

### TModel

`TModel` *extends* `string`

### TSettingsByModel

`TSettingsByModel` *extends* `Record`\<`TModel`, `object`\>

### TSelectedModel

`TSelectedModel` *extends* `string`

### TOutputs

`TOutputs` *extends* `TaskOutputMap`

### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[]

### TTaskId

`TTaskId` *extends* `string`

## Parameters

### definition

[`LLMTaskDefinition`](../type-aliases/llmtaskdefinition/)\<`TOutput`, `TModel`, `TSettingsByModel`, `TSelectedModel`, `TOutputs`, `TDependencies`, `TTaskId`\>

## Returns

[`TaskDefinition`](../interfaces/taskdefinition/)\<`TOutput`, `TOutputs`, `TDependencies`, `TTaskId`\>

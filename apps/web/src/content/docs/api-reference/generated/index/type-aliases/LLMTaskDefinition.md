---
title: "Type Alias: LLMTaskDefinition\\<TOutput, TModel, TSettingsByModel, TSelectedModel, TOutputs, TDependencies, TTaskId\\>"
---

[**condukt-ai**](../../readme/)

***

# Type Alias: LLMTaskDefinition\<TOutput, TModel, TSettingsByModel, TSelectedModel, TOutputs, TDependencies, TTaskId\>

> **LLMTaskDefinition**\<`TOutput`, `TModel`, `TSettingsByModel`, `TSelectedModel`, `TOutputs`, `TDependencies`, `TTaskId`\> = `object` & `LLMTaskModelSettingsField`\<`TSettingsByModel`\[`TSelectedModel`\]\>

Defined in: [pipeline/llm.ts:28](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/llm.ts#L28)

Declarative definition for an LLM-backed task.

## Type Declaration

### after?

> `readonly` `optional` **after**: `TDependencies`

### description?

> `readonly` `optional` **description**: `string`

### id

> `readonly` **id**: `TTaskId`

### model

> `readonly` **model**: `TSelectedModel`

### output

> `readonly` **output**: [`TaskDefinition`](../interfaces/taskdefinition/)\<`TOutput`, `TOutputs`, `TDependencies`, `TTaskId`\>\[`"output"`\]

### prompt()

> `readonly` **prompt**: (`context`) => `string` \| `Promise`\<`string`\>

#### Parameters

##### context

[`TaskRuntimeContext`](../interfaces/taskruntimecontext/)\<`TOutputs`, `TDependencies`\>

#### Returns

`string` \| `Promise`\<`string`\>

### provider

> `readonly` **provider**: [`LLMProvider`](../interfaces/llmprovider/)\<`TModel`, `TSettingsByModel`\>

### retry?

> `readonly` `optional` **retry**: [`TaskRetryPolicy`](../interfaces/taskretrypolicy/)

### system?

> `readonly` `optional` **system**: `string` \| (`context`) => `string` \| `Promise`\<`string`\>

### when?

> `readonly` `optional` **when**: `TaskCondition`\<`TOutputs`, `TDependencies`\>

## Type Parameters

### TOutput

`TOutput` = `unknown`

### TModel

`TModel` *extends* `string` = `string`

### TSettingsByModel

`TSettingsByModel` *extends* `Record`\<`TModel`, `object`\> = `Record`\<`TModel`, `Record`\<`string`, `never`\>\>

### TSelectedModel

`TSelectedModel` *extends* `TModel` = `TModel`

### TOutputs

`TOutputs` *extends* `TaskOutputMap` = `TaskOutputMap`

### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[] = readonly `TaskOutputKey`\<`TOutputs`\>[]

### TTaskId

`TTaskId` *extends* `string` = `string`

## Remarks

`modelSettings` is conditionally required based on the selected model's
required settings type.

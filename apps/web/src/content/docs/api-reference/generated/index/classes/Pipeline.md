---
title: "Class: Pipeline\\<TOutputs\\>"
---

[**condukt-ai**](../../readme/)

***

# Class: Pipeline\<TOutputs\>

Defined in: [pipeline/class.ts:42](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L42)

Fluent pipeline builder and runner.

## Remarks

`Pipeline` preserves task output types across `addTask`/`addLLMTask` calls,
so downstream task contexts and `runDetailed().outputs` stay strongly typed.

## Example

```ts
const pipeline = new Pipeline("demo")
  .addTask({ ... })
  .addLLMTask({ ... });
```

## Type Parameters

### TOutputs

`TOutputs` *extends* `TaskOutputMap` = `Record`\<`never`, `never`\>

## Constructors

### Constructor

> **new Pipeline**\<`TOutputs`\>(`name`, `options?`, `state?`): `Pipeline`\<`TOutputs`\>

Defined in: [pipeline/class.ts:45](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L45)

#### Parameters

##### name

`string`

##### options?

[`PipelineOptions`](../interfaces/pipelineoptions/) = `{}`

##### state?

`PipelineState`

#### Returns

`Pipeline`\<`TOutputs`\>

## Properties

### name

> `readonly` **name**: `string`

Defined in: [pipeline/class.ts:46](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L46)

## Methods

### addLLMTask()

> **addLLMTask**\<`TOutput`, `TModel`, `TSettingsByModel`, `TSelectedModel`, `TDependencies`, `TTaskId`\>(`definition`): `Pipeline`\<`MergeTaskOutputs`\<`TOutputs`, `TTaskId`, `TOutput`\>\>

Defined in: [pipeline/class.ts:69](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L69)

Adds an LLM-backed task with provider/model-aware typing.

#### Type Parameters

##### TOutput

`TOutput`

##### TModel

`TModel` *extends* `string`

##### TSettingsByModel

`TSettingsByModel` *extends* `Record`\<`TModel`, `object`\>

##### TSelectedModel

`TSelectedModel` *extends* `string`

##### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[]

##### TTaskId

`TTaskId` *extends* `string`

#### Parameters

##### definition

`object` & `LLMTaskModelSettingsField`\<`TSettingsByModel`\[`TSelectedModel`\]\> & `DuplicateTaskIdConstraint`\<`TOutputs`, `TTaskId`\>

#### Returns

`Pipeline`\<`MergeTaskOutputs`\<`TOutputs`, `TTaskId`, `TOutput`\>\>

***

### addTask()

> **addTask**\<`TOutput`, `TDependencies`, `TTaskId`\>(`task`): `Pipeline`\<`MergeTaskOutputs`\<`TOutputs`, `TTaskId`, `TOutput`\>\>

Defined in: [pipeline/class.ts:57](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L57)

Adds a task to the pipeline and returns a builder with merged output typing.

#### Type Parameters

##### TOutput

`TOutput`

##### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[]

##### TTaskId

`TTaskId` *extends* `string`

#### Parameters

##### task

[`TaskDefinition`](../interfaces/taskdefinition/)\<`TOutput`, `TOutputs`, `TDependencies`, `TTaskId`\> & `DuplicateTaskIdConstraint`\<`TOutputs`, `TTaskId`\>

#### Returns

`Pipeline`\<`MergeTaskOutputs`\<`TOutputs`, `TTaskId`, `TOutput`\>\>

***

### run()

> **run**(): `Promise`\<[`PipelineTrace`](../interfaces/pipelinetrace/)\>

Defined in: [pipeline/class.ts:101](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L101)

Runs the pipeline and returns only the pipeline trace.

#### Returns

`Promise`\<[`PipelineTrace`](../interfaces/pipelinetrace/)\>

***

### runDetailed()

> **runDetailed**(): `Promise`\<[`PipelineRunResult`](../interfaces/pipelinerunresult/)\<`TOutputs`\>\>

Defined in: [pipeline/class.ts:92](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/class.ts#L92)

Runs the pipeline and returns trace plus typed outputs and task results.

#### Returns

`Promise`\<[`PipelineRunResult`](../interfaces/pipelinerunresult/)\<`TOutputs`\>\>

---
title: "Interface: PipelineRunResult\\<TOutputs\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: PipelineRunResult\<TOutputs\>

Defined in: [pipeline/types.ts:149](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L149)

Detailed result returned by [Pipeline.runDetailed](../classes/pipeline/#rundetailed).

## Type Parameters

### TOutputs

`TOutputs` *extends* `TaskOutputMap`

Typed map of task outputs keyed by task id.

## Properties

### outputs

> `readonly` **outputs**: `Readonly`\<`Partial`\<`TOutputs`\>\>

Defined in: [pipeline/types.ts:151](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L151)

***

### taskResults

> `readonly` **taskResults**: `Readonly`\<`Record`\<`string`, [`TaskTrace`](tasktrace/)\>\>

Defined in: [pipeline/types.ts:152](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L152)

***

### trace

> `readonly` **trace**: [`PipelineTrace`](pipelinetrace/)

Defined in: [pipeline/types.ts:150](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/pipeline/types.ts#L150)

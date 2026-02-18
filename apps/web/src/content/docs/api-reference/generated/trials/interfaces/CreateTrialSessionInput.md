---
title: "Interface: CreateTrialSessionInput"
---

[**condukt-ai**](../../readme/)

***

# Interface: CreateTrialSessionInput

Defined in: [trials/types.ts:45](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L45)

Input payload for starting a trial session.

## Properties

### expected?

> `readonly` `optional` **expected**: `object`

Defined in: [trials/types.ts:50](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L50)

#### contract\_paths?

> `readonly` `optional` **contract\_paths**: readonly `string`[]

#### error\_code?

> `readonly` `optional` **error\_code**: `string`

#### task?

> `readonly` `optional` **task**: `string`

***

### mode

> `readonly` **mode**: [`TrialMode`](../type-aliases/trialmode/)

Defined in: [trials/types.ts:48](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L48)

***

### participant

> `readonly` **participant**: `string`

Defined in: [trials/types.ts:46](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L46)

***

### scenario

> `readonly` **scenario**: `string`

Defined in: [trials/types.ts:47](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L47)

***

### sessionId?

> `readonly` `optional` **sessionId**: `string`

Defined in: [trials/types.ts:55](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L55)

***

### startedAt?

> `readonly` `optional` **startedAt**: `string`

Defined in: [trials/types.ts:56](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L56)

***

### trace?

> `readonly` `optional` **trace**: [`PipelineTrace`](../../index/interfaces/pipelinetrace/)

Defined in: [trials/types.ts:49](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L49)

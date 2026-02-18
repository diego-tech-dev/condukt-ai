---
title: "Interface: TanStackChatTaskDefinition\\<TOutput, TAdapter, TOutputs, TDependencies, TTaskId\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: TanStackChatTaskDefinition\<TOutput, TAdapter, TOutputs, TDependencies, TTaskId\>

Defined in: [tanstack.ts:23](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L23)

Declarative task definition for TanStack AI chat adapters.

## Type Parameters

### TOutput

`TOutput` = `unknown`

### TAdapter

`TAdapter` *extends* `AnyTextAdapter` = `AnyTextAdapter`

### TOutputs

`TOutputs` *extends* `TaskOutputMap` = `TaskOutputMap`

### TDependencies

`TDependencies` *extends* readonly `TaskOutputKey`\<`TOutputs`\>[] = readonly `TaskOutputKey`\<`TOutputs`\>[]

### TTaskId

`TTaskId` *extends* `string` = `string`

## Properties

### adapter

> `readonly` **adapter**: `TAdapter`

Defined in: [tanstack.ts:36](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L36)

***

### after?

> `readonly` `optional` **after**: `TDependencies`

Defined in: [tanstack.ts:32](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L32)

***

### description?

> `readonly` `optional` **description**: `string`

Defined in: [tanstack.ts:31](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L31)

***

### id

> `readonly` **id**: `TTaskId`

Defined in: [tanstack.ts:30](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L30)

***

### options?

> `readonly` `optional` **options**: `TanStackTaskChatOptions`\<`TAdapter`\> \| (`context`) => `MaybePromise`\<`TanStackTaskChatOptions`\<`TAdapter`\>\>

Defined in: [tanstack.ts:41](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L41)

***

### output

> `readonly` **output**: `StandardSchemaV1`\<`unknown`, `TOutput`\>

Defined in: [tanstack.ts:35](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L35)

***

### prompt()

> `readonly` **prompt**: (`context`) => `MaybePromise`\<`string`\>

Defined in: [tanstack.ts:37](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L37)

#### Parameters

##### context

[`TaskRuntimeContext`](taskruntimecontext/)\<`TOutputs`, `TDependencies`\>

#### Returns

`MaybePromise`\<`string`\>

***

### retry?

> `readonly` `optional` **retry**: [`TaskRetryPolicy`](taskretrypolicy/)

Defined in: [tanstack.ts:34](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L34)

***

### system?

> `readonly` `optional` **system**: `string` \| (`context`) => `MaybePromise`\<`string`\>

Defined in: [tanstack.ts:38](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L38)

***

### when()?

> `readonly` `optional` **when**: (`context`) => `MaybePromise`\<`boolean`\>

Defined in: [tanstack.ts:33](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/tanstack.ts#L33)

#### Parameters

##### context

[`TaskRuntimeContext`](taskruntimecontext/)\<`TOutputs`, `TDependencies`\>

#### Returns

`MaybePromise`\<`boolean`\>

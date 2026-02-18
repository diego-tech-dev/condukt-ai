---
title: "Interface: TaskTrace"
---

[**condukt-ai**](../../readme/)

***

# Interface: TaskTrace

Defined in: [pipeline/types.ts:106](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L106)

Full trace entry for a task execution (including retries and contract diagnostics).

## Properties

### attempts?

> `readonly` `optional` **attempts**: readonly `TaskAttemptTrace`[]

Defined in: [pipeline/types.ts:120](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L120)

***

### contract\_issues?

> `readonly` `optional` **contract\_issues**: readonly [`ContractIssue`](contractissue/)[]

Defined in: [pipeline/types.ts:119](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L119)

***

### duration\_ms

> `readonly` **duration\_ms**: `number`

Defined in: [pipeline/types.ts:111](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L111)

***

### error?

> `readonly` `optional` **error**: `string`

Defined in: [pipeline/types.ts:116](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L116)

***

### error\_code?

> `readonly` `optional` **error\_code**: `string`

Defined in: [pipeline/types.ts:117](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L117)

***

### finished\_at

> `readonly` **finished\_at**: `string`

Defined in: [pipeline/types.ts:110](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L110)

***

### input?

> `readonly` `optional` **input**: `unknown`

Defined in: [pipeline/types.ts:112](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L112)

***

### meta?

> `readonly` `optional` **meta**: `Record`\<`string`, `unknown`\>

Defined in: [pipeline/types.ts:115](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L115)

***

### output?

> `readonly` `optional` **output**: `unknown`

Defined in: [pipeline/types.ts:113](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L113)

***

### raw\_output?

> `readonly` `optional` **raw\_output**: `string`

Defined in: [pipeline/types.ts:114](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L114)

***

### skip\_reason?

> `readonly` `optional` **skip\_reason**: `string`

Defined in: [pipeline/types.ts:118](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L118)

***

### started\_at

> `readonly` **started\_at**: `string`

Defined in: [pipeline/types.ts:109](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L109)

***

### status

> `readonly` **status**: `"ok"` \| `"error"` \| `"skipped"`

Defined in: [pipeline/types.ts:108](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L108)

***

### task

> `readonly` **task**: `string`

Defined in: [pipeline/types.ts:107](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/pipeline/types.ts#L107)

---
title: "Interface: TrialRecord"
---

[**condukt-ai**](../../readme/)

***

# Interface: TrialRecord

Defined in: [trials/types.ts:25](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L25)

Completed trial record with measured diagnosis outcome.

## Properties

### diagnosed

> `readonly` **diagnosed**: `object`

Defined in: [trials/types.ts:34](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L34)

#### error\_code?

> `readonly` `optional` **error\_code**: `string`

#### task?

> `readonly` `optional` **task**: `string`

***

### diagnosis\_correct

> `readonly` **diagnosis\_correct**: `boolean`

Defined in: [trials/types.ts:40](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L40)

***

### elapsed\_ms

> `readonly` **elapsed\_ms**: `number`

Defined in: [trials/types.ts:32](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L32)

***

### expected

> `readonly` **expected**: [`TrialExpectation`](trialexpectation/)

Defined in: [trials/types.ts:33](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L33)

***

### finished\_at

> `readonly` **finished\_at**: `string`

Defined in: [trials/types.ts:31](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L31)

***

### matched\_error\_code

> `readonly` **matched\_error\_code**: `boolean` \| `null`

Defined in: [trials/types.ts:39](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L39)

***

### matched\_task

> `readonly` **matched\_task**: `boolean` \| `null`

Defined in: [trials/types.ts:38](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L38)

***

### mode

> `readonly` **mode**: [`TrialMode`](../type-aliases/trialmode/)

Defined in: [trials/types.ts:29](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L29)

***

### notes?

> `readonly` `optional` **notes**: `string`

Defined in: [trials/types.ts:41](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L41)

***

### participant

> `readonly` **participant**: `string`

Defined in: [trials/types.ts:27](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L27)

***

### scenario

> `readonly` **scenario**: `string`

Defined in: [trials/types.ts:28](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L28)

***

### session\_id

> `readonly` **session\_id**: `string`

Defined in: [trials/types.ts:26](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L26)

***

### started\_at

> `readonly` **started\_at**: `string`

Defined in: [trials/types.ts:30](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L30)

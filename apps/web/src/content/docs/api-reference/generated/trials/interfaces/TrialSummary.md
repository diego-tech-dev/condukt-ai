---
title: "Interface: TrialSummary"
---

[**condukt-ai**](../../readme/)

***

# Interface: TrialSummary

Defined in: [trials/types.ts:71](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L71)

Aggregate summary metrics across trial records.

## Properties

### accuracy

> `readonly` **accuracy**: `number`

Defined in: [trials/types.ts:74](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L74)

***

### by\_mode

> `readonly` **by\_mode**: `Record`\<[`TrialMode`](../type-aliases/trialmode/), [`TrialModeSummary`](trialmodesummary/)\>

Defined in: [trials/types.ts:77](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L77)

***

### condukt\_ai\_vs\_baseline\_speedup

> `readonly` **condukt\_ai\_vs\_baseline\_speedup**: `number` \| `null`

Defined in: [trials/types.ts:78](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L78)

***

### correct

> `readonly` **correct**: `number`

Defined in: [trials/types.ts:73](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L73)

***

### median\_elapsed\_ms

> `readonly` **median\_elapsed\_ms**: `number` \| `null`

Defined in: [trials/types.ts:75](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L75)

***

### p90\_elapsed\_ms

> `readonly` **p90\_elapsed\_ms**: `number` \| `null`

Defined in: [trials/types.ts:76](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L76)

***

### paired

> `readonly` **paired**: [`TrialPairSummary`](trialpairsummary/)

Defined in: [trials/types.ts:79](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L79)

***

### total

> `readonly` **total**: `number`

Defined in: [trials/types.ts:72](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/types.ts#L72)

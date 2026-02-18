---
title: "Interface: ContractValidationResult\\<TOutput\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: ContractValidationResult\<TOutput\>

Defined in: [contracts.ts:14](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/contracts.ts#L14)

Result returned by [validateContract](../functions/validatecontract/).

## Type Parameters

### TOutput

`TOutput`

The validated output shape produced by the contract.

## Properties

### issues?

> `readonly` `optional` **issues**: readonly [`ContractIssue`](contractissue/)[]

Defined in: [contracts.ts:17](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/contracts.ts#L17)

***

### ok

> `readonly` **ok**: `boolean`

Defined in: [contracts.ts:15](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/contracts.ts#L15)

***

### value?

> `readonly` `optional` **value**: `TOutput`

Defined in: [contracts.ts:16](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/contracts.ts#L16)

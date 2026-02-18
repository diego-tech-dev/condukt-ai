---
title: "Function: validateContract()"
---

[**condukt-ai**](../../readme/)

***

# Function: validateContract()

> **validateContract**\<`TOutput`\>(`contract`, `value`): `Promise`\<[`ContractValidationResult`](../interfaces/contractvalidationresult/)\<`TOutput`\>\>

Defined in: [contracts.ts:27](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/contracts.ts#L27)

Validates a runtime value against a Standard Schema contract.

## Type Parameters

### TOutput

`TOutput`

## Parameters

### contract

`StandardSchemaV1`\<`unknown`, `TOutput`\>

### value

`unknown`

## Returns

`Promise`\<[`ContractValidationResult`](../interfaces/contractvalidationresult/)\<`TOutput`\>\>

## Remarks

This function normalizes provider-specific issue paths into dotted strings
so traces and diagnostics can render stable failure locations.

---
title: "Function: createTrialSession()"
---

[**condukt-ai**](../../readme/)

***

# Function: createTrialSession()

> **createTrialSession**(`input`): [`TrialSession`](../interfaces/trialsession/)

Defined in: [trials/session.ts:21](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/trials/session.ts#L21)

Starts a diagnosis trial session with normalized expectation metadata.

## Parameters

### input

[`CreateTrialSessionInput`](../interfaces/createtrialsessioninput/)

## Returns

[`TrialSession`](../interfaces/trialsession/)

## Remarks

If `trace` is provided, expectation fields are derived from its first failure
unless explicitly overridden in `expected`.

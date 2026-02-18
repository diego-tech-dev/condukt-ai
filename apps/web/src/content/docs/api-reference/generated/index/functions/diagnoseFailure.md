---
title: "Function: diagnoseFailure()"
---

[**condukt-ai**](../../readme/)

***

# Function: diagnoseFailure()

> **diagnoseFailure**(`trace`): [`FailureDiagnosis`](../interfaces/failurediagnosis/)

Defined in: [diagnostics.ts:23](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/diagnostics.ts#L23)

Extracts a compact failure diagnosis from a pipeline trace.

## Parameters

### trace

[`PipelineTrace`](../interfaces/pipelinetrace/)

## Returns

[`FailureDiagnosis`](../interfaces/failurediagnosis/)

## Remarks

When no task failed, returns `{ failed: false }` with an empty contract path list.

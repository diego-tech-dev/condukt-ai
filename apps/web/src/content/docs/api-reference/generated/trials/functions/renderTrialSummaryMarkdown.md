---
title: "Function: renderTrialSummaryMarkdown()"
---

[**condukt-ai**](../../readme/)

***

# Function: renderTrialSummaryMarkdown()

> **renderTrialSummaryMarkdown**(`summary`, `options?`): `string`

Defined in: [trials/summary.ts:88](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/trials/summary.ts#L88)

Renders a markdown report from a computed trial summary.

## Parameters

### summary

[`TrialSummary`](../interfaces/trialsummary/)

### options?

[`TrialSummaryMarkdownOptions`](../interfaces/trialsummarymarkdownoptions/) = `{}`

## Returns

`string`

## Example

```ts
const markdown = renderTrialSummaryMarkdown(summary, { title: "Trial Report" });
```

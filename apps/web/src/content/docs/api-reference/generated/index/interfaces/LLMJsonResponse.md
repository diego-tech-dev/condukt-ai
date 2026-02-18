---
title: "Interface: LLMJsonResponse\\<TModel\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: LLMJsonResponse\<TModel\>

Defined in: [providers.ts:20](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L20)

Normalized JSON generation response returned by an LLM provider adapter.

## Type Parameters

### TModel

`TModel` *extends* `string` = `string`

## Properties

### data

> `readonly` **data**: `unknown`

Defined in: [providers.ts:24](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L24)

***

### model

> `readonly` **model**: `TModel`

Defined in: [providers.ts:22](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L22)

***

### provider

> `readonly` **provider**: `string`

Defined in: [providers.ts:21](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L21)

***

### rawText

> `readonly` **rawText**: `string`

Defined in: [providers.ts:23](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L23)

***

### responseId?

> `readonly` `optional` **responseId**: `string`

Defined in: [providers.ts:25](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L25)

***

### usage?

> `readonly` `optional` **usage**: `Record`\<`string`, `unknown`\>

Defined in: [providers.ts:26](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L26)

---
title: "Interface: LLMJsonRequest\\<TModel, TSettings\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: LLMJsonRequest\<TModel, TSettings\>

Defined in: [providers.ts:9](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L9)

Provider-agnostic JSON generation request payload.

## Type Parameters

### TModel

`TModel` *extends* `string` = `string`

Model id accepted by the provider.

### TSettings

`TSettings` *extends* `object` = `Record`\<`string`, `never`\>

Model-specific settings type.

## Properties

### model

> `readonly` **model**: `TModel`

Defined in: [providers.ts:13](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L13)

***

### prompt

> `readonly` **prompt**: `string`

Defined in: [providers.ts:14](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L14)

***

### settings?

> `readonly` `optional` **settings**: `TSettings`

Defined in: [providers.ts:16](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L16)

***

### system?

> `readonly` `optional` **system**: `string`

Defined in: [providers.ts:15](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L15)

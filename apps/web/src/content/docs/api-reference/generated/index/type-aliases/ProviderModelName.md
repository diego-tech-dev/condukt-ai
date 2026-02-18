---
title: "Type Alias: ProviderModelName\\<TProvider\\>"
---

[**condukt-ai**](../../readme/)

***

# Type Alias: ProviderModelName\<TProvider\>

> **ProviderModelName**\<`TProvider`\> = `TProvider` *extends* [`LLMProvider`](../interfaces/llmprovider/)\<infer TModel, infer \_TSettingsByModel\> ? `TModel` : `never`

Defined in: [providers.ts:47](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L47)

Extracts provider model names from an [LLMProvider](../interfaces/llmprovider/) type.

## Type Parameters

### TProvider

`TProvider`

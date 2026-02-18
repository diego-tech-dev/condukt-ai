---
title: "Type Alias: ProviderModelSettings\\<TProvider, TModel\\>"
---

[**condukt-ai**](../../readme/)

***

# Type Alias: ProviderModelSettings\<TProvider, TModel\>

> **ProviderModelSettings**\<`TProvider`, `TModel`\> = `TProvider` *extends* [`LLMProvider`](../interfaces/llmprovider/)\<infer \_TProviderModel, infer TSettingsByModel\> ? `TSettingsByModel` *extends* `Record`\<`string`, `object`\> ? `TSettingsByModel`\[`TModel`\] : `never` : `never`

Defined in: [providers.ts:53](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L53)

Resolves model settings type for a provider/model pair.

## Type Parameters

### TProvider

`TProvider`

### TModel

`TModel` *extends* [`ProviderModelName`](providermodelname/)\<`TProvider`\>

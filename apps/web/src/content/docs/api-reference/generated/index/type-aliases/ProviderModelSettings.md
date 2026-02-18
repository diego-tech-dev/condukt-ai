---
title: "Type Alias: ProviderModelSettings\\<TProvider, TModel\\>"
---

[**condukt-ai**](../../readme/)

***

# Type Alias: ProviderModelSettings\<TProvider, TModel\>

> **ProviderModelSettings**\<`TProvider`, `TModel`\> = `TProvider` *extends* [`LLMProvider`](../interfaces/llmprovider/)\<infer \_TProviderModel, infer TSettingsByModel\> ? `TSettingsByModel` *extends* `Record`\<`string`, `object`\> ? `TSettingsByModel`\[`TModel`\] : `never` : `never`

Defined in: [providers.ts:53](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L53)

Resolves model settings type for a provider/model pair.

## Type Parameters

### TProvider

`TProvider`

### TModel

`TModel` *extends* [`ProviderModelName`](providermodelname/)\<`TProvider`\>

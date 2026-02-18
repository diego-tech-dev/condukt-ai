---
title: "Function: createOpenAIProvider()"
---

[**condukt-ai**](../../readme/)

***

# Function: createOpenAIProvider()

> **createOpenAIProvider**(`options?`): [`LLMProvider`](../interfaces/llmprovider/)\<[`OpenAIModel`](../type-aliases/openaimodel/), [`OpenAIModelSettingsByModel`](../type-aliases/openaimodelsettingsbymodel/)\>

Defined in: [providers.ts:145](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L145)

Creates an OpenAI-backed provider that returns parsed JSON payloads.

## Parameters

### options?

[`OpenAIProviderOptions`](../interfaces/openaiprovideroptions/) = `{}`

## Returns

[`LLMProvider`](../interfaces/llmprovider/)\<[`OpenAIModel`](../type-aliases/openaimodel/), [`OpenAIModelSettingsByModel`](../type-aliases/openaimodelsettingsbymodel/)\>

## Example

```ts
const provider = createOpenAIProvider({ apiKey: process.env.OPENAI_API_KEY });
```

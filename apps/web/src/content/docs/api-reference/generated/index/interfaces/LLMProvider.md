---
title: "Interface: LLMProvider\\<TModel, TSettingsByModel\\>"
---

[**condukt-ai**](../../readme/)

***

# Interface: LLMProvider\<TModel, TSettingsByModel\>

Defined in: [providers.ts:35](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L35)

LLM provider contract used by `llmTask`.

## Type Parameters

### TModel

`TModel` *extends* `string` = `string`

Valid model ids.

### TSettingsByModel

`TSettingsByModel` *extends* `Record`\<`TModel`, `object`\> = `Record`\<`TModel`, `Record`\<`string`, `never`\>\>

Settings map keyed by model id.

## Properties

### models

> `readonly` **models**: readonly `TModel`[]

Defined in: [providers.ts:40](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L40)

***

### name

> `readonly` **name**: `string`

Defined in: [providers.ts:39](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L39)

## Methods

### generateJSON()

> **generateJSON**\<`TSelectedModel`\>(`request`): `Promise`\<[`LLMJsonResponse`](llmjsonresponse/)\<`TSelectedModel`\>\>

Defined in: [providers.ts:41](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L41)

#### Type Parameters

##### TSelectedModel

`TSelectedModel` *extends* `string`

#### Parameters

##### request

[`LLMJsonRequest`](llmjsonrequest/)\<`TSelectedModel`, `TSettingsByModel`\[`TSelectedModel`\]\>

#### Returns

`Promise`\<[`LLMJsonResponse`](llmjsonresponse/)\<`TSelectedModel`\>\>

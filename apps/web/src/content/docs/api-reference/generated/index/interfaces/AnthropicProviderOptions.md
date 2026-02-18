---
title: "Interface: AnthropicProviderOptions"
---

[**condukt-ai**](../../readme/)

***

# Interface: AnthropicProviderOptions

Defined in: [providers.ts:70](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L70)

Options for creating an Anthropic JSON provider.

## Properties

### anthropicVersion?

> `readonly` `optional` **anthropicVersion**: `string`

Defined in: [providers.ts:73](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L73)

***

### apiKey?

> `readonly` `optional` **apiKey**: `string`

Defined in: [providers.ts:71](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L71)

***

### baseUrl?

> `readonly` `optional` **baseUrl**: `string`

Defined in: [providers.ts:72](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L72)

***

### fetchFn()?

> `readonly` `optional` **fetchFn**: \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [providers.ts:74](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L74)

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`URL` | `RequestInfo`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

#### Call Signature

> (`input`, `init?`): `Promise`\<`Response`\>

[MDN Reference](https://developer.mozilla.org/docs/Web/API/Window/fetch)

##### Parameters

###### input

`string` | `URL` | `Request`

###### init?

`RequestInit`

##### Returns

`Promise`\<`Response`\>

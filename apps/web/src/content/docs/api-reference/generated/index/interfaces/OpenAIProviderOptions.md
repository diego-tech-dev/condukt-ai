---
title: "Interface: OpenAIProviderOptions"
---

[**condukt-ai**](../../readme/)

***

# Interface: OpenAIProviderOptions

Defined in: [providers.ts:61](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L61)

Options for creating an OpenAI JSON provider.

## Properties

### apiKey?

> `readonly` `optional` **apiKey**: `string`

Defined in: [providers.ts:62](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L62)

***

### baseUrl?

> `readonly` `optional` **baseUrl**: `string`

Defined in: [providers.ts:63](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L63)

***

### fetchFn()?

> `readonly` `optional` **fetchFn**: \{(`input`, `init?`): `Promise`\<`Response`\>; (`input`, `init?`): `Promise`\<`Response`\>; \}

Defined in: [providers.ts:66](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L66)

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

***

### organization?

> `readonly` `optional` **organization**: `string`

Defined in: [providers.ts:64](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L64)

***

### project?

> `readonly` `optional` **project**: `string`

Defined in: [providers.ts:65](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L65)

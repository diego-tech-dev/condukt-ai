---
title: "Type Alias: OpenAIModelSettingsByModel"
---

[**condukt-ai**](../../readme/)

***

# Type Alias: OpenAIModelSettingsByModel

> **OpenAIModelSettingsByModel** = `{ readonly [TModel in OpenAIChatModel]: OpenAIChatModelSettings }` & `{ readonly [TModel in OpenAIReasoningModel]: OpenAIReasoningModelSettings }`

Defined in: [providers.ts:97](https://github.com/diego-tech-dev/condukt-ai/blob/081c57a376a08f1d575dd0dca665084fa696e68f/packages/core/src/providers.ts#L97)

Model-specific OpenAI settings map keyed by model id.

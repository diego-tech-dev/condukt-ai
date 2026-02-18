---
title: "Type Alias: OpenAIModelSettingsByModel"
---

[**condukt-ai**](../../readme/)

***

# Type Alias: OpenAIModelSettingsByModel

> **OpenAIModelSettingsByModel** = `{ readonly [TModel in OpenAIChatModel]: OpenAIChatModelSettings }` & `{ readonly [TModel in OpenAIReasoningModel]: OpenAIReasoningModelSettings }`

Defined in: [providers.ts:97](https://github.com/diego-tech-dev/condukt-ai/blob/main/packages/core/src/providers.ts#L97)

Model-specific OpenAI settings map keyed by model id.

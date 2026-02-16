import { parseJsonText, previewJson } from "./json.js";

export interface LLMJsonRequest<
  TModel extends string = string,
  TSettings extends object = Record<string, never>,
> {
  readonly model: TModel;
  readonly prompt: string;
  readonly system?: string;
  readonly settings?: TSettings;
}

export interface LLMJsonResponse<TModel extends string = string> {
  readonly provider: string;
  readonly model: TModel;
  readonly rawText: string;
  readonly data: unknown;
  readonly responseId?: string;
  readonly usage?: Record<string, unknown>;
}

export interface LLMProvider<
  TModel extends string = string,
  TSettingsByModel extends Record<TModel, object> = Record<TModel, Record<string, never>>,
> {
  readonly name: string;
  readonly models: readonly TModel[];
  generateJSON<TSelectedModel extends TModel>(
    request: LLMJsonRequest<TSelectedModel, TSettingsByModel[TSelectedModel]>,
  ): Promise<LLMJsonResponse<TSelectedModel>>;
}

export type ProviderModelName<TProvider> =
  TProvider extends LLMProvider<infer TModel extends string, infer _TSettingsByModel>
    ? TModel
    : never;

export type ProviderModelSettings<TProvider, TModel extends ProviderModelName<TProvider>> =
  TProvider extends LLMProvider<infer _TProviderModel extends string, infer TSettingsByModel>
    ? TSettingsByModel extends Record<string, object>
      ? TSettingsByModel[TModel]
      : never
    : never;

export interface OpenAIProviderOptions {
  readonly apiKey?: string;
  readonly baseUrl?: string;
  readonly organization?: string;
  readonly project?: string;
  readonly fetchFn?: typeof fetch;
}

export interface AnthropicProviderOptions {
  readonly apiKey?: string;
  readonly baseUrl?: string;
  readonly anthropicVersion?: string;
  readonly fetchFn?: typeof fetch;
}

export interface OpenAIChatModelSettings {
  readonly temperature?: number;
  readonly maxTokens?: number;
}

export interface OpenAIReasoningModelSettings {
  readonly maxTokens?: number;
  readonly reasoningEffort?: "low" | "medium" | "high";
}

export type OpenAIChatModel = "gpt-4.1" | "gpt-4.1-mini" | "gpt-4o" | "gpt-4o-mini";
export type OpenAIReasoningModel = "o3-mini" | "o4-mini";
export type OpenAIModel = OpenAIChatModel | OpenAIReasoningModel;

export type OpenAIModelSettingsByModel = {
  readonly [TModel in OpenAIChatModel]: OpenAIChatModelSettings;
} & {
  readonly [TModel in OpenAIReasoningModel]: OpenAIReasoningModelSettings;
};

export const OPENAI_MODELS: readonly OpenAIModel[] = [
  "gpt-4.1",
  "gpt-4.1-mini",
  "gpt-4o",
  "gpt-4o-mini",
  "o3-mini",
  "o4-mini",
] as const;

export interface AnthropicModelSettings {
  readonly maxTokens?: number;
  readonly temperature?: number;
}

export type AnthropicModel =
  | "claude-opus-4-1-20250805"
  | "claude-sonnet-4-5-20250929"
  | "claude-3-5-haiku-latest";

export type AnthropicModelSettingsByModel = {
  readonly [TModel in AnthropicModel]: AnthropicModelSettings;
};

export const ANTHROPIC_MODELS: readonly AnthropicModel[] = [
  "claude-opus-4-1-20250805",
  "claude-sonnet-4-5-20250929",
  "claude-3-5-haiku-latest",
] as const;

export function createOpenAIProvider(
  options: OpenAIProviderOptions = {},
): LLMProvider<OpenAIModel, OpenAIModelSettingsByModel> {
  const apiKey = options.apiKey ?? process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is required for OpenAI provider");
  }

  const baseUrl = options.baseUrl ?? "https://api.openai.com";
  const fetchFn = options.fetchFn ?? fetch;

  return {
    name: "openai",
    models: OPENAI_MODELS,
    async generateJSON<TSelectedModel extends OpenAIModel>(
      request: LLMJsonRequest<TSelectedModel, OpenAIModelSettingsByModel[TSelectedModel]>,
    ) {
      const body: Record<string, unknown> = {
        model: request.model,
        messages: buildMessages(request.system, request.prompt),
        response_format: { type: "json_object" },
      };

      const settings = request.settings;
      if (typeof settings?.maxTokens === "number") {
        body.max_tokens = settings.maxTokens;
      }

      if (isOpenAIReasoningModel(request.model)) {
        const reasoningSettings = settings as OpenAIReasoningModelSettings | undefined;
        if (reasoningSettings?.reasoningEffort) {
          body.reasoning_effort = reasoningSettings.reasoningEffort;
        }
      } else {
        const chatSettings = settings as OpenAIChatModelSettings | undefined;
        if (typeof chatSettings?.temperature === "number") {
          body.temperature = chatSettings.temperature;
        }
      }

      const headers: Record<string, string> = {
        "content-type": "application/json",
        authorization: `Bearer ${apiKey}`,
      };
      if (options.organization) {
        headers["OpenAI-Organization"] = options.organization;
      }
      if (options.project) {
        headers["OpenAI-Project"] = options.project;
      }

      const response = await fetchFn(`${baseUrl}/v1/chat/completions`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(`OpenAI request failed (${response.status}): ${previewJson(payload)}`);
      }

      const content = payload?.choices?.[0]?.message?.content;
      const rawText = extractContentText(content, "openai");
      return {
        provider: "openai",
        model: request.model,
        rawText,
        data: parseJsonText(rawText, { provider: "openai" }),
        responseId: payload?.id,
        usage: payload?.usage,
      };
    },
  };
}

export function createAnthropicProvider(
  options: AnthropicProviderOptions = {},
): LLMProvider<AnthropicModel, AnthropicModelSettingsByModel> {
  const apiKey = options.apiKey ?? process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY is required for Anthropic provider");
  }

  const baseUrl = options.baseUrl ?? "https://api.anthropic.com";
  const anthropicVersion = options.anthropicVersion ?? "2023-06-01";
  const fetchFn = options.fetchFn ?? fetch;

  return {
    name: "anthropic",
    models: ANTHROPIC_MODELS,
    async generateJSON<TSelectedModel extends AnthropicModel>(
      request: LLMJsonRequest<TSelectedModel, AnthropicModelSettingsByModel[TSelectedModel]>,
    ) {
      const body: Record<string, unknown> = {
        model: request.model,
        max_tokens: request.settings?.maxTokens ?? 1024,
        messages: [{ role: "user", content: request.prompt }],
      };

      if (request.system) {
        body.system = request.system;
      }
      if (typeof request.settings?.temperature === "number") {
        body.temperature = request.settings.temperature;
      }

      const response = await fetchFn(`${baseUrl}/v1/messages`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": apiKey,
          "anthropic-version": anthropicVersion,
        },
        body: JSON.stringify(body),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(`Anthropic request failed (${response.status}): ${previewJson(payload)}`);
      }

      const blocks: unknown[] = Array.isArray(payload?.content) ? payload.content : [];
      const rawText = blocks
        .filter(
          (block): block is { type?: unknown; text?: unknown } =>
            typeof block === "object" &&
            block !== null &&
            (block as { type?: unknown }).type === "text",
        )
        .map((block) => String(block.text ?? ""))
        .join("\n")
        .trim();

      if (!rawText) {
        throw new Error("Anthropic response did not contain text content");
      }

      return {
        provider: "anthropic",
        model: request.model,
        rawText,
        data: parseJsonText(rawText, { provider: "anthropic" }),
        responseId: payload?.id,
        usage: payload?.usage,
      };
    },
  };
}

function isOpenAIReasoningModel(model: OpenAIModel): model is OpenAIReasoningModel {
  return model === "o3-mini" || model === "o4-mini";
}

function buildMessages(system: string | undefined, prompt: string): Array<Record<string, string>> {
  if (!system) {
    return [{ role: "user", content: prompt }];
  }

  return [
    { role: "system", content: system },
    { role: "user", content: prompt },
  ];
}

function extractContentText(content: unknown, provider: string): string {
  if (typeof content === "string") {
    return content.trim();
  }

  if (Array.isArray(content)) {
    const fragments = content
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (typeof item === "object" && item && "text" in item) {
          return String((item as { text?: unknown }).text ?? "");
        }
        return "";
      })
      .join("\n")
      .trim();
    if (fragments) {
      return fragments;
    }
  }

  throw new Error(`${provider} response did not contain text content`);
}

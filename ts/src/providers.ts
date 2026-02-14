export interface LLMJsonRequest {
  readonly model: string;
  readonly prompt: string;
  readonly system?: string;
  readonly temperature?: number;
  readonly maxTokens?: number;
}

export interface LLMJsonResponse {
  readonly provider: string;
  readonly model: string;
  readonly rawText: string;
  readonly data: unknown;
  readonly responseId?: string;
  readonly usage?: Record<string, unknown>;
}

export interface LLMProvider {
  readonly name: string;
  generateJSON(request: LLMJsonRequest): Promise<LLMJsonResponse>;
}

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

export function createOpenAIProvider(options: OpenAIProviderOptions = {}): LLMProvider {
  const apiKey = options.apiKey ?? process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is required for OpenAI provider");
  }

  const baseUrl = options.baseUrl ?? "https://api.openai.com";
  const fetchFn = options.fetchFn ?? fetch;

  return {
    name: "openai",
    async generateJSON(request) {
      const body: Record<string, unknown> = {
        model: request.model,
        messages: buildMessages(request.system, request.prompt),
        response_format: { type: "json_object" },
      };

      if (typeof request.temperature === "number") {
        body.temperature = request.temperature;
      }
      if (typeof request.maxTokens === "number") {
        body.max_tokens = request.maxTokens;
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
        throw new Error(`OpenAI request failed (${response.status}): ${jsonPreview(payload)}`);
      }

      const content = payload?.choices?.[0]?.message?.content;
      const rawText = extractContentText(content, "openai");
      return {
        provider: "openai",
        model: request.model,
        rawText,
        data: parseJsonText(rawText, "openai"),
        responseId: payload?.id,
        usage: payload?.usage,
      };
    },
  };
}

export function createAnthropicProvider(options: AnthropicProviderOptions = {}): LLMProvider {
  const apiKey = options.apiKey ?? process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY is required for Anthropic provider");
  }

  const baseUrl = options.baseUrl ?? "https://api.anthropic.com";
  const anthropicVersion = options.anthropicVersion ?? "2023-06-01";
  const fetchFn = options.fetchFn ?? fetch;

  return {
    name: "anthropic",
    async generateJSON(request) {
      const body: Record<string, unknown> = {
        model: request.model,
        max_tokens: request.maxTokens ?? 1024,
        messages: [{ role: "user", content: request.prompt }],
      };
      if (request.system) {
        body.system = request.system;
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
        throw new Error(
          `Anthropic request failed (${response.status}): ${jsonPreview(payload)}`,
        );
      }

      const blocks: unknown[] = Array.isArray(payload?.content) ? payload.content : [];
      const rawText = blocks
        .filter(
          (block): block is { type?: unknown; text?: unknown } =>
            typeof block === "object" && block !== null && (block as { type?: unknown }).type === "text",
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
        data: parseJsonText(rawText, "anthropic"),
        responseId: payload?.id,
        usage: payload?.usage,
      };
    },
  };
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

function parseJsonText(text: string, provider: string): unknown {
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(
      `${provider} response is not valid JSON: ${(error as Error).message}; content=${previewText(text)}`,
    );
  }
}

function previewText(value: string): string {
  const compact = value.replace(/\s+/g, " ").trim();
  if (compact.length <= 180) {
    return compact;
  }
  return `${compact.slice(0, 177)}...`;
}

function jsonPreview(value: unknown): string {
  try {
    const text = JSON.stringify(value);
    return previewText(text);
  } catch {
    return "<unserializable-response>";
  }
}

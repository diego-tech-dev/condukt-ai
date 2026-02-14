import assert from "node:assert/strict";
import test from "node:test";

import { createAnthropicProvider, createOpenAIProvider } from "../src/index.js";

test("openai provider parses JSON chat completion responses", async () => {
  const provider = createOpenAIProvider({
    apiKey: "test-key",
    fetchFn: async () =>
      new Response(
        JSON.stringify({
          id: "resp_123",
          choices: [
            {
              message: {
                content: "{\"ok\":true,\"issues\":[]}",
              },
            },
          ],
          usage: { total_tokens: 123 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
  });

  const result = await provider.generateJSON({
    model: "gpt-4.1-mini",
    prompt: "Return JSON",
  });

  assert.equal(result.provider, "openai");
  assert.equal(result.model, "gpt-4.1-mini");
  assert.deepEqual(result.data, { ok: true, issues: [] });
  assert.equal(result.responseId, "resp_123");
});

test("anthropic provider parses JSON text blocks", async () => {
  const provider = createAnthropicProvider({
    apiKey: "test-key",
    fetchFn: async () =>
      new Response(
        JSON.stringify({
          id: "msg_123",
          content: [{ type: "text", text: "{\"verified\":false,\"issues\":[\"missing source\"]}" }],
          usage: { input_tokens: 10, output_tokens: 20 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
  });

  const result = await provider.generateJSON({
    model: "claude-sonnet-4-5-20250929",
    prompt: "Return JSON",
  });

  assert.equal(result.provider, "anthropic");
  assert.equal(result.model, "claude-sonnet-4-5-20250929");
  assert.deepEqual(result.data, {
    verified: false,
    issues: ["missing source"],
  });
  assert.equal(result.responseId, "msg_123");
});

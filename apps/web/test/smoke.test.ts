import { describe, expect, test } from "vitest";

import { createWebsiteConfig } from "../src/index.js";

describe("createWebsiteConfig", () => {
  test("returns a stable config object", () => {
    const config = createWebsiteConfig("Condukt AI");

    expect(config).toEqual({ title: "Condukt AI" });
  });
});

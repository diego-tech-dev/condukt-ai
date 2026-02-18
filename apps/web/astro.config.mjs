import { defineConfig, passthroughImageService } from "astro/config";
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import starlight from "@astrojs/starlight";
import starlightConfig from "./starlight.config.mjs";

export default defineConfig({
  site: "https://condukt-ai.dev",
  image: {
    service: passthroughImageService(),
  },
  integrations: [react(), starlight(starlightConfig), mdx()],
});

const starlightConfig = {
  title: "condukt-ai",
  description: "TypeScript-first orchestration runtime with contract boundaries and trace-first diagnosis.",
  logo: {
    src: "./src/assets/brand/logo-condukt-ai.svg",
    alt: "condukt-ai",
  },
  social: [
    {
      icon: "github",
      label: "GitHub",
      href: "https://github.com/diego-tech-dev/condukt-ai",
    },
  ],
  customCss: ["./src/styles/custom.css"],
  sidebar: [
    {
      label: "Start",
      items: [
        { label: "Overview", link: "/" },
        { label: "Getting Started", link: "/getting-started/" },
      ],
    },
    {
      label: "Guides",
      autogenerate: { directory: "guides" },
    },
    {
      label: "API Reference",
      items: [
        { label: "Overview", link: "/api-reference/" },
        {
          label: "Generated API",
          autogenerate: { directory: "api-reference/generated" },
        },
      ],
    },
    {
      label: "Architecture",
      autogenerate: { directory: "architecture" },
    },
    {
      label: "Trials",
      autogenerate: { directory: "trials" },
    },
    {
      label: "Migration",
      autogenerate: { directory: "migration-history" },
    },
  ],
};

export default starlightConfig;

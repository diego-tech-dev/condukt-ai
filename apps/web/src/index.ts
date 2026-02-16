export interface WebsiteConfig {
  readonly title: string;
}

export function createWebsiteConfig(title: string): WebsiteConfig {
  return { title };
}

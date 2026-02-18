import { readdir, readFile } from "node:fs/promises";
import { join, posix, relative, resolve } from "node:path";

const distDir = resolve(process.cwd(), "dist");

const distFiles = await collectFiles(distDir);
const htmlFiles = distFiles.filter((file) => file.endsWith(".html"));
const fileSet = new Set(distFiles.map((file) => normalizePath(relative(distDir, file))));
const htmlSet = new Set([...fileSet].filter((file) => file.endsWith(".html")));
const errors = [];

for (const htmlFile of htmlFiles) {
  const pagePath = normalizePath(relative(distDir, htmlFile));
  if (pagePath.startsWith("/api-reference/generated/")) {
    continue;
  }

  const content = await readFile(htmlFile, "utf8");
  const links = extractHrefs(content);
  const pageDir = pagePath.endsWith("/index.html")
    ? pagePath.slice(0, -"index.html".length)
    : pagePath.slice(0, pagePath.lastIndexOf("/") + 1);

  for (const href of links) {
    if (
      href.startsWith("http://") ||
      href.startsWith("https://") ||
      href.startsWith("mailto:") ||
      href.startsWith("tel:") ||
      href.startsWith("#")
    ) {
      continue;
    }

    const [pathOnly] = href.split(/[?#]/);
    if (!pathOnly) {
      continue;
    }

    const resolvedPath = resolveLink(pageDir, pathOnly);
    const htmlPath = normalizeHtmlPath(resolvedPath);
    if (!fileSet.has(resolvedPath) && !htmlSet.has(htmlPath)) {
      errors.push(`${relative(distDir, htmlFile)} -> ${href}`);
    }
  }
}

if (errors.length > 0) {
  console.error("Broken internal links detected:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exitCode = 1;
} else {
  console.log("Internal link check passed.");
}

async function collectFiles(root) {
  const output = [];
  await walk(root, output);
  return output;
}

async function walk(dir, output) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(fullPath, output);
      continue;
    }

    if (entry.isFile()) {
      output.push(fullPath);
    }
  }
}

function extractHrefs(content) {
  const hrefs = [];
  const hrefPattern = /href=["']([^"']+)["']/g;
  let match = hrefPattern.exec(content);
  while (match) {
    hrefs.push(match[1]);
    match = hrefPattern.exec(content);
  }
  return hrefs;
}

function resolveLink(pageDir, linkPath) {
  if (linkPath.startsWith("/")) {
    return normalizePath(linkPath);
  }

  const combined = posix.join(pageDir, linkPath);
  return normalizePath(combined);
}

function normalizePath(rawPath) {
  const slashPath = rawPath.replaceAll("\\", "/");
  const absolutePath = slashPath.startsWith("/") ? slashPath : `/${slashPath}`;
  return posix.normalize(absolutePath);
}

function normalizeHtmlPath(rawPath) {
  const path = normalizePath(rawPath);

  if (path.endsWith(".html")) {
    return path;
  }

  if (path.endsWith("/")) {
    return `${path}index.html`;
  }

  const basename = path.split("/").pop() ?? "";
  if (basename.includes(".")) {
    return path;
  }

  return `${path}/index.html`;
}

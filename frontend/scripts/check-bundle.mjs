import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { gzipSync } from "node:zlib";

// Follow static imports from each HTML entry. Lazy imports aren't initial JS.
const root = resolve(import.meta.dirname, "../dist");
const seen = new Set();
function visit(path) {
  if (seen.has(path)) return;
  seen.add(path);
  const source = readFileSync(resolve(root, path), "utf8");
  for (const match of source.matchAll(/(?:from\s*|import\s*)["']([^"']+\.js)["']/g)) {
    const target = resolve(root, path, "..", match[1]);
    visit(target.slice(root.length + 1));
  }
}
for (const file of readdirSync(root).filter((name) => name.endsWith(".html"))) {
  const html = readFileSync(resolve(root, file), "utf8");
  for (const match of html.matchAll(/(?:src|href)="\/([^"?]+\.js)"/g)) visit(match[1]);
}
if (!seen.size) throw new Error("No initial JavaScript found");
const bytes = [...seen].reduce((sum, path) => sum + gzipSync(readFileSync(resolve(root, path))).length, 0);
console.log(`Initial JavaScript: ${bytes} gzip bytes / 200000`);
if (bytes >= 200000) process.exitCode = 1;

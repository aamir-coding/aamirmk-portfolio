import { writeFileSync } from "node:fs";

const revision = process.env.VERCEL_GIT_COMMIT_SHA ?? process.env.GITHUB_SHA ?? null;
if (revision !== null && !/^[a-f0-9]{40}$/.test(revision)) {
  throw new Error("Invalid release revision");
}
writeFileSync(new URL("../dist/release.json", import.meta.url), JSON.stringify({ revision }) + "\n");
console.log(`Frontend release receipt: ${revision ?? "local/unknown"}`);

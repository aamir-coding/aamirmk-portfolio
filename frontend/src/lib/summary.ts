import { z } from "zod";
import { getApiBaseUrl } from "./api";
import { getSessionId } from "./session";

const ProjectId = z.enum([
  "entropy-oj", "ai-digital-assistant", "health-tracker", "health-premium-predictor",
]);
export type SummaryProjectId = z.infer<typeof ProjectId>;
const receiptPrefixes: Record<SummaryProjectId, string> = {
  "entropy-oj": "proj-entropy-oj-",
  "ai-digital-assistant": "proj-ai-assistant-",
  "health-tracker": "proj-healthtracker-",
  "health-premium-predictor": "proj-health-premium-",
};

export function summaryProjectIds(hints: readonly string[]): SummaryProjectId[] {
  const selected = new Set<SummaryProjectId>();
  for (const hint of hints) {
    const project = ProjectId.options.find(id => hint === id || hint.startsWith(receiptPrefixes[id]));
    if (project) selected.add(project);
  }
  return [...selected];
}

const Token = z.string().regex(/^[A-Za-z0-9_-]{43}$/);
const ExpiresAt = z.iso.datetime({ offset: true });
const Evidence = z.object({
  title: z.string().min(1),
  description: z.string().min(1),
  source: z.enum(["Technical Skills", "Experience", "Technical Projects"]),
});

const Created = z.object({ token: Token, expires_at: ExpiresAt });
const Shared = z.object({
  summary: z.object({
    name: z.string().min(1),
    headline: z.string().min(1),
    strengths: z.array(Evidence).length(3),
    projects: z.array(Evidence.extend({ id: ProjectId })).min(1).max(2),
    gaps: z.string().min(1),
    availability: z.string().min(1),
    contact_email: z.email(),
  }),
  expires_at: ExpiresAt,
});

export type CreatedSummary = z.infer<typeof Created>;
export type SharedSummary = z.infer<typeof Shared>;

export function isSummaryToken(token: string): boolean {
  return Token.safeParse(token).success;
}

export async function createSummary(
  projectIds: readonly SummaryProjectId[], signal: AbortSignal,
): Promise<CreatedSummary> {
  const response = await fetch(`${getApiBaseUrl()}/api/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": getSessionId() },
    body: JSON.stringify({ project_ids: projectIds }),
    cache: "no-store",
    credentials: "omit",
    signal,
  });
  if (response.status === 429) throw new Error("The summary limit was reached. Try again later.");
  if (!response.ok) throw new Error("The summary could not be created. Try again.");
  const result = Created.safeParse(await response.json());
  if (!result.success) throw new Error("The summary link could not be confirmed.");
  return result.data;
}

export async function fetchSharedSummary(
  token: string, signal: AbortSignal,
): Promise<SharedSummary | null> {
  if (!isSummaryToken(token)) return null;
  const response = await fetch(`${getApiBaseUrl()}/api/summary/${token}`, {
    cache: "no-store",
    credentials: "omit",
    referrerPolicy: "no-referrer",
    redirect: "error",
    signal,
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("The summary could not be loaded.");
  const result = Shared.safeParse(await response.json());
  if (!result.success) throw new Error("The summary could not be read.");
  return result.data;
}

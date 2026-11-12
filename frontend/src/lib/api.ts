import type { ChatHistoryMessage, FeedbackRating, SampleJobDescription } from "./types";
import { SampleJobDescriptionSchema } from "./contracts";
import { getSessionId } from "./session";
import { z } from "zod";

export interface HealthStatus {
  status: string;
  ready: boolean;
  assistant_state?: "ready" | "resting";
}

const HealthStatusSchema = z.object({
  status: z.literal("ok"), ready: z.literal(true),
  assistant_state: z.enum(["ready", "resting"]).optional(),
});

const CompanyContextSchema = z.object({
  slug: z.string().max(64).regex(/^[a-z0-9]+(?:-[a-z0-9]+)*-[a-f0-9]{4,}$/),
  greeting: z.string().min(1).max(180),
  why_us: z.string().min(1).max(400),
  suggested_questions: z.array(z.string().min(1).max(180)).length(3),
  highlighted_projects: z.array(z.object({
    id: z.string().min(1),
    title: z.string().min(1),
  })).min(1).max(4),
});
const ContextResponseSchema = z.object({ company: CompanyContextSchema.nullable() });
export type CompanyContext = z.infer<typeof CompanyContextSchema>;

export const getApiBaseUrl = (): string => {
  const url = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  return url.replace(/\/+$/, "");
};

export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/health`, {
    method: "GET",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed with HTTP ${response.status}`);
  }

  const data = (await response.json()) as unknown;
  const parsed = HealthStatusSchema.safeParse(data);
  if (parsed.success) return parsed.data;

  throw new Error("Invalid response schema from health endpoint");
}

export async function fetchCompanyContext(
  slug: string, signal: AbortSignal,
): Promise<CompanyContext | null> {
  const params = new URLSearchParams({ for: slug });
  const response = await fetch(`${getApiBaseUrl()}/api/context?${params}`, {
    signal,
    headers: { "X-Session-ID": getSessionId() },
  });
  if (!response.ok) return null;
  const { company } = ContextResponseSchema.parse(await response.json());
  return company?.slug === slug ? company : null;
}

interface HandoffSubmission {
  id: string;
  consent: true;
  website: string;
  reply_email: string | null;
  transcript: readonly ChatHistoryMessage[];
}

const HandoffAcceptedSchema = z.object({
  id: z.string().uuid(),
  status: z.literal("accepted"),
});

export async function submitHandoff(payload: HandoffSubmission, signal: AbortSignal): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/handoff`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": getSessionId() },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    const messages: Record<number, string> = {
      409: "This request was already submitted. Contact Aamir directly to add details.",
      413: "This transcript is too large. Start a shorter chat and try again.",
      422: "Check the reply email and try again.",
      429: "The handoff limit was reached. Try again later or contact Aamir directly.",
    };
    throw new Error(messages[response.status] ?? "Handoff is unavailable. Try again or contact Aamir directly.");
  }
  const accepted = HandoffAcceptedSchema.safeParse(await response.json());
  if (!accepted.success || accepted.data.id !== payload.id) {
    throw new Error("The handoff could not be confirmed.");
  }
}

const FeedbackSavedSchema = z.object({ rating: z.enum(["up", "down"]) });

export async function submitFeedback(
  answerId: string, rating: FeedbackRating, reason: string | null, signal: AbortSignal,
): Promise<FeedbackRating> {
  const response = await fetch(`${getApiBaseUrl()}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": getSessionId() },
    body: JSON.stringify({ answer_id: answerId, rating, reason }),
    signal,
  });
  if (!response.ok) {
    if (response.status === 404) throw new Error("Feedback is unavailable for this answer.");
    if (response.status === 429) throw new Error("Feedback limit reached. Try again in a minute.");
    throw new Error("Feedback could not be saved. Try again.");
  }
  const saved = FeedbackSavedSchema.safeParse(await response.json());
  if (!saved.success) throw new Error("Feedback could not be confirmed. Try again.");
  return saved.data.rating;
}

export async function fetchFitPresets(signal?: AbortSignal): Promise<SampleJobDescription[]> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/api/fit/presets`, {
    method: "GET",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch fit presets: HTTP ${response.status}`);
  }

  const data = (await response.json()) as unknown;
  return z.array(SampleJobDescriptionSchema).parse(data);
}

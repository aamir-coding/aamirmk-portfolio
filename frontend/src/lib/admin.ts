import { z } from "zod";
import { getApiBaseUrl } from "./api";

const count = z.number().int().nonnegative();
const date = z.iso.date();
const timestamp = z.iso.datetime({ offset: true });
const recentQuestion = z.object({
  id: z.uuid(), question: z.string(), created_at: timestamp,
});
const feedback = recentQuestion.extend({
  rating: z.enum(["up", "down"]), reason: z.string().nullable(),
});

const DashboardSchema = z.object({
  start_date: date,
  end_date: date,
  question_count: count,
  classified_questions: count,
  unanswered_count: count,
  average_latency_ms: z.number().nonnegative().nullable(),
  fit_reports: count,
  handoff_count: count,
  candidate_count: count,
  daily_token_ceiling: count,
  usage: z.array(z.object({
    day: date, known_tokens: count, unknown_runs: count, fit_reports: count,
  })),
  company_opens: z.array(z.object({ slug: z.string(), count })),
  top_questions: z.array(z.object({ question: z.string(), count })),
  unanswered: z.array(recentQuestion),
  handoffs: z.array(z.object({
    id: z.uuid(),
    question: z.string().nullable(),
    reply_email: z.string().nullable(),
    delivery_status: z.enum(["pending", "sent", "failed"]),
    created_at: timestamp,
  })),
  feedback: z.array(feedback),
  candidates: z.array(feedback),
});

export type Dashboard = z.infer<typeof DashboardSchema>;

export class AdminRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function fetchDashboard(token: string, signal: AbortSignal): Promise<Dashboard> {
  const response = await fetch(`${getApiBaseUrl()}/api/admin/dashboard`, {
    headers: { Authorization: `Bearer ${token}` },
    credentials: "omit",
    cache: "no-store",
    redirect: "error",
    signal,
  });
  if (!response.ok) {
    const messages: Record<number, string> = {
      401: "The admin token was rejected.",
      404: "The admin dashboard is unavailable.",
      429: "Too many requests. Try again in a minute.",
    };
    throw new AdminRequestError(response.status, messages[response.status] ?? "The dashboard could not be loaded.");
  }
  const result = DashboardSchema.safeParse(await response.json());
  if (!result.success) throw new Error("The dashboard response could not be read.");
  return result.data;
}

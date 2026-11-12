import type { SampleJobDescription } from "./types";
import { SampleJobDescriptionSchema } from "./contracts";
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
  const response = await fetch(`${getApiBaseUrl()}/api/context?${params}`, { signal });
  if (!response.ok) return null;
  const { company } = ContextResponseSchema.parse(await response.json());
  return company?.slug === slug ? company : null;
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

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

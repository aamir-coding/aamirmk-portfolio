import { useEffect, useState } from "react";
import { z } from "zod";
import { getApiBaseUrl } from "./api";

const Count = z.object({ passed: z.number().int().nonnegative(), total: z.number().int().positive() })
  .refine((value) => value.passed <= value.total);
const Report = z.object({
  kind: z.literal("offline_engineering_checks"),
  generated_at: z.string(), source_commit: z.string(), source_dirty: z.boolean(),
  source_result_sha256: z.string(), runtime_sha256: z.string(),
  replay: Count,
  categories: z.array(z.object({ category: z.string(), passed: z.number().int().nonnegative(), total: z.number().int().nonnegative(), skipped: z.number().int().nonnegative() })),
  retrieval: z.array(z.object({ suite: z.string(), metric: z.string(), numerator: z.number().nonnegative(), denominator: z.number().int().nonnegative() })),
  failed_checks: z.array(z.string()), held_out_reserved: z.number().int().positive(),
  held_out_executed: z.literal(false), draft_chunks: z.number().int().nonnegative(),
  generation_accuracy_available: z.literal(false),
  development_without_recordings: z.number().int().nonnegative(),
  judge_validation: z.object({ kind: z.literal("judge_human_agreement"), status: z.enum(["failed", "passed"]),
    model: z.literal("openai/gpt-oss-20b"), artifact_sha256: z.string(), rubric_sha256: z.string(),
    axes: z.object({ support: Count, completeness: Count, behavior: Count, tone: Count }),
    failures_by_axis: z.record(z.string(), z.number().int().nonnegative()),
    disagreements: z.array(z.object({ item_id: z.string(), axis: z.string(), human: z.string(), judge: z.string() })),
  }),
});

export const EvalSummarySchema = z.object({
  status: z.enum(["available", "unavailable", "stale"]), badge: z.string(),
  report: Report.nullable(), reason: z.string().nullable(),
}).refine((value) => value.status === "available"
  ? value.report !== null && value.badge === `Replay checks: ${value.report.replay.passed}/${value.report.replay.total} (offline)`
  : value.report === null);

export type EvalSummary = z.infer<typeof EvalSummarySchema>;

export function useEvalSummary() {
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/eval-summary`, { signal: controller.signal });
        if (!response.ok) throw new Error("Evaluation results unavailable");
        const result = EvalSummarySchema.parse(await response.json());
        if (!controller.signal.aborted) setSummary(result);
      } catch {
        if (!controller.signal.aborted) setError(true);
      }
    }
    void load();
    return () => controller.abort();
  }, []);
  return { summary, error };
}

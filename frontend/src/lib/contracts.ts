/**
 * Zod runtime contract validation schemas for backend API and SSE event frames.
 *
 * Enforces strict boundary verification between FastAPI and React in accordance with
 * AGENTS.md Engineering Standards and Phase 3 & 6 typed contract specifications.
 */

import { z } from "zod";

export const SourceCitationSchema = z.object({
  chunk_id: z.string().min(1),
  title: z.string().min(1),
  type: z.string().min(1),
  source_section: z.string().optional(),
  source_url: z.string().nullable().optional(),
});

export const ProjectCardDataSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  subtitle: z.string(),
  summary: z.string(),
  role: z.string(),
  tech_stack: z.array(z.string()),
  highlights: z.array(z.string()),
  metrics: z.record(z.string(), z.string()),
  github_url: z.string().nullable().optional(),
  live_url: z.string().nullable().optional(),
  source_sections: z.array(z.string()),
  architecture_details: z.string(),
});

export const SourcesEventPayloadSchema = z.object({
  sources: z.array(SourceCitationSchema),
});

export const CardEventPayloadSchema = z.object({
  card: ProjectCardDataSchema,
});

export const TokenEventPayloadSchema = z.object({
  token: z.string(),
});

export const DoneEventPayloadSchema = z.object({
  conversation_id: z.string().min(1),
  sources: z.array(SourceCitationSchema).optional(),
  cards: z.array(ProjectCardDataSchema).optional(),
});

export const ErrorEventPayloadSchema = z.object({
  detail: z.string().min(1),
});

// ── Phase 6 Fit Report Schemas ──────────────────────────────────────────

export const FitRequirementSchema = z.object({
  id: z.string().min(1),
  text: z.string().min(1),
  importance: z.enum(["must_have", "nice_to_have"]),
  type: z.enum(["skill", "experience", "education", "soft"]),
});

export const JudgedRequirementSchema = z.object({
  requirement: FitRequirementSchema,
  verdict: z.enum(["strong", "partial", "gap"]),
  evidence_chunk_ids: z.array(z.string()),
  explanation: z.string().min(1),
  ramp_up: z.string().nullable().optional(),
  downgraded: z.boolean().optional(),
});

export const FitScoreSummarySchema = z.object({
  must_have_total: z.number().int().nonnegative(),
  must_have_strong: z.number().int().nonnegative(),
  must_have_partial: z.number().int().nonnegative(),
  must_have_gap: z.number().int().nonnegative(),
  nice_to_have_total: z.number().int().nonnegative(),
  nice_to_have_strong: z.number().int().nonnegative(),
  nice_to_have_partial: z.number().int().nonnegative(),
  nice_to_have_gap: z.number().int().nonnegative(),
  total_requirements: z.number().int().nonnegative(),
  overall_fit: z.enum(["Strong Match", "Partial Match", "Low Match"]),
  headline: z.string().min(1),
});

export const FitReportSchema = z.object({
  role_title: z.string().min(1),
  jd_hash: z.string().length(64),
  score: FitScoreSummarySchema,
  requirements: z.array(JudgedRequirementSchema),
  summary: z.string().min(1),
  cached: z.boolean().optional(),
});

export const FitProgressDataSchema = z.object({
  step: z.string().min(1),
  message: z.string().min(1),
  percent: z.number().min(0).max(100),
});

export const FitErrorPayloadSchema = z.object({
  code: z.string().min(1),
  message: z.string().min(1),
});

export const SampleJobDescriptionSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  company: z.string().optional().default(""),
  match_expectation: z.string(),
  text: z.string().min(1),
  report: FitReportSchema.nullable().optional(),
});

export type ValidatedSourceCitation = z.infer<typeof SourceCitationSchema>;
export type ValidatedProjectCardData = z.infer<typeof ProjectCardDataSchema>;
export type ValidatedDonePayload = z.infer<typeof DoneEventPayloadSchema>;
export type ValidatedFitReport = z.infer<typeof FitReportSchema>;
export type ValidatedFitProgressData = z.infer<typeof FitProgressDataSchema>;
export type ValidatedSampleJobDescription = z.infer<typeof SampleJobDescriptionSchema>;

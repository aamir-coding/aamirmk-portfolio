/**
 * Zod runtime contract validation schemas for backend API and SSE event frames.
 *
 * Enforces strict boundary verification between FastAPI and React in accordance with
 * AGENTS.md Engineering Standards and Phase 3 typed contract specifications.
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

export type ValidatedSourceCitation = z.infer<typeof SourceCitationSchema>;
export type ValidatedProjectCardData = z.infer<typeof ProjectCardDataSchema>;
export type ValidatedDonePayload = z.infer<typeof DoneEventPayloadSchema>;

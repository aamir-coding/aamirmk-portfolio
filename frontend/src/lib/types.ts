/**
 * Core TypeScript domain models for the AI Digital Assistant Portfolio.
 */

export interface SourceCitation {
  chunk_id: string;
  title: string;
  type: string;
  source_section?: string;
  source_url?: string | null;
}

export interface ProjectCardData {
  id: string;
  title: string;
  subtitle: string;
  summary: string;
  role: string;
  tech_stack: string[];
  highlights: string[];
  metrics: Record<string, string>;
  github_url?: string | null;
  live_url?: string | null;
  source_sections: string[];
  architecture_details: string;
}

export interface InstantAnswer {
  reply: string;
  sources?: SourceCitation[];
  cards?: ProjectCardData[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "pending" | "streaming" | "done" | "error";
  timestamp: string;
  sources?: SourceCitation[];
  cards?: ProjectCardData[];
}

// ── Phase 6 Fit Report Types ────────────────────────────────────────────

export interface FitRequirement {
  id: string;
  text: string;
  importance: "must_have" | "nice_to_have";
  type: "skill" | "experience" | "education" | "soft";
}

export interface JudgedRequirement {
  requirement: FitRequirement;
  verdict: "strong" | "partial" | "gap";
  evidence_chunk_ids: string[];
  explanation: string;
  ramp_up?: string | null;
  downgraded?: boolean;
}

export interface FitScoreSummary {
  must_have_total: number;
  must_have_strong: number;
  must_have_partial: number;
  must_have_gap: number;
  nice_to_have_total: number;
  nice_to_have_strong: number;
  nice_to_have_partial: number;
  nice_to_have_gap: number;
  total_requirements: number;
  overall_fit: "Strong Match" | "Partial Match" | "Low Match";
  headline: string;
}

export interface FitReport {
  role_title: string;
  jd_hash: string;
  score: FitScoreSummary;
  requirements: JudgedRequirement[];
  summary: string;
  cached?: boolean;
}

export interface FitProgressData {
  step: string;
  message: string;
  percent: number;
}

export interface SampleJobDescription {
  id: string;
  title: string;
  company: string;
  match_expectation: string;
  text: string;
  report?: FitReport | null;
}

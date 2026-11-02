import { describe, it, expect } from "vitest";
import {
  SourceCitationSchema,
  ProjectCardDataSchema,
  SourcesEventPayloadSchema,
  CardEventPayloadSchema,
  TokenEventPayloadSchema,
  DoneEventPayloadSchema,
  ErrorEventPayloadSchema,
  FitReportSchema,
  FitProgressDataSchema,
  FitRequirementSchema,
  JudgedRequirementSchema,
} from "./contracts";

describe("Runtime API Contracts (Zod Validation)", () => {
  it("validates a compliant SourceCitation", () => {
    const valid = {
      chunk_id: "proj-entropy-oj-pitch",
      title: "Entropy-OJ Flagship Online Judge",
      type: "project",
      source_section: "J1",
      source_url: "https://github.com/aamir-coding/entropy-oj",
    };

    const parsed = SourceCitationSchema.safeParse(valid);
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.chunk_id).toBe("proj-entropy-oj-pitch");
    }
  });

  it("rejects an invalid SourceCitation missing required fields", () => {
    const invalid = {
      title: "Missing chunk_id and type",
    };

    const parsed = SourceCitationSchema.safeParse(invalid);
    expect(parsed.success).toBe(false);
  });

  it("validates a full ProjectCardData record from disk", () => {
    const validCard = {
      id: "entropy-oj",
      title: "Entropy Online Judge",
      subtitle: "Competitive Programming & DSA Platform",
      summary: "Evaluates code in Linux sandbox.",
      role: "Solo Author",
      tech_stack: ["React 19", "Node.js", "Redis"],
      highlights: ["BullMQ asynchronous judging"],
      metrics: { Worker: "Dedicated VM", Concurrency: "10" },
      github_url: "https://github.com/aamir-coding/entropy-oj",
      live_url: "https://entropy-oj.vercel.app",
      source_sections: ["J1", "J2"],
      architecture_details: "System uses Redis queue and Linux runner.",
    };

    const parsed = ProjectCardDataSchema.safeParse(validCard);
    expect(parsed.success).toBe(true);
  });

  it("validates backend 'event: sources' payload", () => {
    const payload = {
      sources: [
        {
          chunk_id: "proj-entropy-oj-pitch",
          title: "Entropy Online Judge",
          type: "project",
          source_section: "J1",
        },
      ],
    };

    const parsed = SourcesEventPayloadSchema.safeParse(payload);
    expect(parsed.success).toBe(true);
  });

  it("validates backend 'event: card' payload", () => {
    const payload = {
      card: {
        id: "entropy-oj",
        title: "Entropy Online Judge",
        subtitle: "CP Platform",
        summary: "Evaluates code in Linux sandbox.",
        role: "Solo Author",
        tech_stack: ["React", "Redis"],
        highlights: ["BullMQ asynchronous judging"],
        metrics: { Latency: "120ms" },
        source_sections: ["J1"],
        architecture_details: "Architecture details.",
      },
    };

    const parsed = CardEventPayloadSchema.safeParse(payload);
    expect(parsed.success).toBe(true);
  });

  it("validates backend 'event: token' payload", () => {
    const payload = { token: "Hello world" };
    const parsed = TokenEventPayloadSchema.safeParse(payload);
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.token).toBe("Hello world");
    }
  });

  it("validates backend 'event: done' terminal payload", () => {
    const payload = {
      conversation_id: "conv-done-999",
      sources: [],
      cards: [],
    };

    const parsed = DoneEventPayloadSchema.safeParse(payload);
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.conversation_id).toBe("conv-done-999");
    }
  });

  it("validates backend 'event: error' payload", () => {
    const payload = {
      detail: "Rate limit reached. Please try again in 15 seconds.",
    };

    const parsed = ErrorEventPayloadSchema.safeParse(payload);
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.detail).toContain("Rate limit reached");
    }
  });

  // ── Phase 6 Fit Report Tests ──────────────────────────────────────────

  it("validates a compliant FitRequirement", () => {
    const req = {
      id: "req-1",
      text: "FastAPI development",
      importance: "must_have",
      type: "skill",
    };
    const parsed = FitRequirementSchema.safeParse(req);
    expect(parsed.success).toBe(true);
  });

  it("validates a JudgedRequirement with valid citations", () => {
    const judged = {
      requirement: {
        id: "req-1",
        text: "FastAPI development",
        importance: "must_have",
        type: "skill",
      },
      verdict: "strong",
      evidence_chunk_ids: ["chunk-fastapi"],
      explanation: "Built async FastAPI backend.",
      ramp_up: null,
      downgraded: false,
    };
    const parsed = JudgedRequirementSchema.safeParse(judged);
    expect(parsed.success).toBe(true);
  });

  it("validates a full FitReport payload", () => {
    const report = {
      role_title: "Full-Stack AI Engineer",
      jd_hash: "a".repeat(64),
      score: {
        must_have_total: 2,
        must_have_strong: 2,
        must_have_partial: 0,
        must_have_gap: 0,
        nice_to_have_total: 1,
        nice_to_have_strong: 1,
        nice_to_have_partial: 0,
        nice_to_have_gap: 0,
        total_requirements: 3,
        overall_fit: "Strong Match",
        headline: "Covers 2 of 2 must-haves, 1 of 1 nice-to-haves",
      },
      requirements: [
        {
          requirement: {
            id: "req-1",
            text: "FastAPI",
            importance: "must_have",
            type: "skill",
          },
          verdict: "strong",
          evidence_chunk_ids: ["chunk-fastapi"],
          explanation: "Built API.",
        },
      ],
      summary: "Aamir is a strong match for this role.",
      cached: false,
    };
    const parsed = FitReportSchema.safeParse(report);
    expect(parsed.success).toBe(true);
  });

  it("validates a FitProgressData progress event", () => {
    const progress = {
      step: "retrieving_evidence",
      message: "Cross-referencing facts...",
      percent: 50,
    };
    const parsed = FitProgressDataSchema.safeParse(progress);
    expect(parsed.success).toBe(true);
  });
});

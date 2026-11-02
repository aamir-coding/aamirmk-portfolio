import { describe, it, expect } from "vitest";
import {
  SourceCitationSchema,
  ProjectCardDataSchema,
  SourcesEventPayloadSchema,
  CardEventPayloadSchema,
  TokenEventPayloadSchema,
  DoneEventPayloadSchema,
  ErrorEventPayloadSchema,
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
          chunk_id: "skill-python",
          title: "Python Experience",
          type: "skill",
          source_section: "S1",
          source_url: null,
        },
      ],
    };

    const parsed = SourcesEventPayloadSchema.safeParse(payload);
    expect(parsed.success).toBe(true);
    if (parsed.success) {
      expect(parsed.data.sources).toHaveLength(1);
    }
  });

  it("validates backend 'event: card' payload", () => {
    const payload = {
      card: {
        id: "vayusetu",
        title: "VayuSetu",
        subtitle: "Clean Air Intelligence",
        summary: "IoT AQI telemetry.",
        role: "Solo Author",
        tech_stack: ["FastAPI", "React"],
        highlights: ["Google Cloud Hackathon 2nd Runner-Up"],
        metrics: { Latency: "<100ms" },
        github_url: null,
        live_url: null,
        source_sections: ["AC3"],
        architecture_details: "Predictive dispersion models.",
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
});

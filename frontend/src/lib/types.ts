/**
 * Domain types for conversational messages, citations, and generative UI cards.
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

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "pending" | "streaming" | "done" | "error";
  timestamp: string;
  sources?: SourceCitation[];
  cards?: ProjectCardData[];
}

export interface InstantAnswer {
  reply: string;
  sources?: SourceCitation[];
}

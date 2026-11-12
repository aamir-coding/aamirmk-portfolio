import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import App from "./App";
import * as api from "./lib/api";
import * as sse from "./lib/sse";

describe("<App />", () => {
  it("recovers from a chat resting response when service status is retried", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onState?.("resting");
      opts.callbacks.onError("Resting for this request");
    });
    render(<App />);
    await screen.findByText("Ready");
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "A custom inquiry" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByLabelText("Server status: live answers resting");
    fireEvent.click(screen.getByRole("button", { name: "Check service status" }));
    await screen.findByText("Ready");
  });
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
    vi.spyOn(api, "fetchFitPresets").mockResolvedValue([]);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      status: "unavailable", report: null, reason: "Test fixture", badge: "Evaluation results unavailable",
    }))));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    sessionStorage.clear();
    window.history.replaceState(null, "", "/");
  });

  it("shows Ecolab suggestions and carries the resolved slug into chat", async () => {
    window.history.replaceState(null, "", "/?for=ecolab-5a2b");
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.mocked(fetch).mockImplementation(async (url) => {
      if (!String(url).includes("/api/context?for=ecolab-5a2b")) {
        return new Response(null, { status: 503 });
      }
      return Response.json({
        company: {
          slug: "ecolab-5a2b",
          greeting: "Welcome, Ecolab recruiting team.",
          why_us: "Explore Aamir’s work on reliable software.",
          suggested_questions: ["How does the judge queue work?", "How are answers grounded?", "What did Aamir build?"],
          highlighted_projects: [{ id: "entropy-oj", title: "Entropy Online Judge" }],
        },
      });
    });
    const stream = vi.spyOn(sse, "streamChat").mockResolvedValue();
    render(<App />);
    expect(await screen.findByText("Welcome, Ecolab recruiting team.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entropy Online Judge" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "How are answers grounded?" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "How does the judge queue work?" }));
    expect(stream).toHaveBeenCalledWith(expect.objectContaining({
      message: "How does the judge queue work?",
      companySlug: "ecolab-5a2b",
    }));
  });

  it("keeps the default cover and chat for an unknown company", async () => {
    window.history.replaceState(null, "", "/?for=unknown-company");
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.mocked(fetch).mockImplementation(async () => Response.json({ company: null }));
    const stream = vi.spyOn(sse, "streamChat").mockResolvedValue();
    render(<App />);
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/context?for=unknown-company"), expect.anything(),
    ));
    fireEvent.click(screen.getByRole("button", { name: "What are Aamir's core technical strengths?" }));
    expect(stream).toHaveBeenCalledOnce();
    expect(stream.mock.lastCall?.[0].companySlug).toBeUndefined();
  });

  it("previews an offered handoff and shares it only after consent", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async ({ callbacks }) => {
      callbacks.onToken("I don’t have verified information about that.");
      callbacks.onDone({ conversation_id: "handoff-chat", handoff: true });
    });
    const handoffRequests: RequestInit[] = [];
    vi.mocked(fetch).mockImplementation(async (url, init) => {
      if (!String(url).endsWith("/api/handoff")) return new Response(null, { status: 503 });
      handoffRequests.push(init ?? {});
      const { id } = JSON.parse(String(init?.body)) as { id: string };
      return Response.json({ id, status: "accepted" }, { status: 202 });
    });
    render(<App />);
    await screen.findByText("Ready");
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "A question for Aamir" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    const send = await screen.findByRole("button", { name: "Send to Aamir" });
    expect(send).toBeDisabled();
    expect(screen.getByText("Preview messages to share")).toBeInTheDocument();
    expect(handoffRequests).toHaveLength(0);
    fireEvent.change(screen.getByLabelText("Reply email (optional)"), { target: { value: "recruiter@example.test" } });
    fireEvent.click(screen.getByRole("checkbox", { name: /agree to share/i }));
    fireEvent.click(send);
    await screen.findByText("Request received.");
    expect(JSON.parse(String(handoffRequests[0]?.body)) as unknown).toMatchObject({
      consent: true,
      reply_email: "recruiter@example.test",
      transcript: [
        { role: "user", content: "A question for Aamir" },
        { role: "assistant", content: "I don’t have verified information about that." },
      ],
    });
  });

  it("saves a downvote and optional reason for a recorded answer", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    const id = "0582803f-86e7-4ec0-b182-0901c1838567";
    vi.spyOn(sse, "streamChat").mockImplementation(async ({ callbacks }) => {
      callbacks.onToken("A reply with sources.");
      callbacks.onDone({ conversation_id: "feedback-chat", feedback_id: id });
    });
    const writes: unknown[] = [];
    vi.mocked(fetch).mockImplementation(async (url, init) => {
      if (!String(url).endsWith("/api/feedback")) return new Response(null, { status: 503 });
      writes.push(JSON.parse(String(init?.body)));
      return Response.json({ rating: "down" });
    });
    render(<App />);
    await screen.findByText("Ready");
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "A question for Aamir" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    fireEvent.click(await screen.findByRole("button", { name: "Not helpful" }));
    expect(writes).toHaveLength(0);
    fireEvent.change(screen.getByLabelText("Reason (optional)"), { target: { value: "Needs an example" } });
    fireEvent.click(screen.getByRole("button", { name: "Send feedback" }));
    await screen.findByText("Feedback saved.");
    expect(writes).toEqual([{ answer_id: id, rating: "down", reason: "Needs an example" }]);
  });

  it("loads the admin dashboard with an in-memory bearer and clears it on sign out", async () => {
    window.history.replaceState(null, "", "/admin");
    const token = "admin-test-token";
    vi.mocked(fetch).mockImplementation(async () => Response.json({
      start_date: "2026-11-06", end_date: "2026-11-12",
      question_count: 1, classified_questions: 1, unanswered_count: 1,
      average_latency_ms: 100, fit_reports: 0, handoff_count: 0, candidate_count: 1,
      daily_token_ceiling: 160000, usage: [], company_opens: [], top_questions: [],
      unanswered: [], handoffs: [], feedback: [], candidates: [{
        id: "0582803f-86e7-4ec0-b182-0901c1838567",
        question: "Where did the claim come from?",
        created_at: "2026-11-12T00:20:00Z",
        rating: "down",
        reason: "Needs a source",
      }],
    }));
    render(<App />);
    const input = await screen.findByLabelText("Admin token");
    expect(fetch).not.toHaveBeenCalled();
    fireEvent.change(input, { target: { value: token } });
    fireEvent.click(screen.getByRole("button", { name: "Open dashboard" }));
    await screen.findByRole("heading", { name: "Candidate eval cases" });
    expect(screen.getByRole("cell", { name: "Where did the claim come from?" })).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/admin/dashboard"),
      expect.objectContaining({
        headers: { Authorization: `Bearer ${token}` },
        credentials: "omit",
        cache: "no-store",
      }),
    );
    expect(JSON.stringify(localStorage)).not.toContain(token);
    expect(JSON.stringify(sessionStorage)).not.toContain(token);
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(screen.getByLabelText("Admin token")).toHaveValue("");
    expect(screen.queryByRole("heading", { name: "Candidate eval cases" })).not.toBeInTheDocument();
  });

  it("creates a team summary with project IDs only", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async ({ callbacks }) => {
      callbacks.onToken("An answer about Aamir.");
      callbacks.onDone({
        conversation_id: "summary-chat",
        sources: [{ chunk_id: "proj-healthtracker-overview", title: "HealthTracker", type: "project" }],
      });
    });
    const token = "A".repeat(43);
    const writes: unknown[] = [];
    vi.mocked(fetch).mockImplementation(async (url, init) => {
      if (!String(url).endsWith("/api/summary")) return new Response(null, { status: 503 });
      writes.push(JSON.parse(String(init?.body)));
      return Response.json({ token, expires_at: "2026-12-12T00:00:00Z" }, { status: 201 });
    });
    render(<App />);
    await screen.findByText("Ready");
    expect(screen.queryByRole("button", { name: "Summarize for my team" })).not.toBeInTheDocument();
    for (const query of ["PRIVATE RECRUITER QUESTION", "PRIVATE RECRUITER FOLLOW-UP"]) {
      fireEvent.change(screen.getByRole("textbox"), { target: { value: query } });
      fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    }
    fireEvent.click(await screen.findByRole("button", { name: "Summarize for my team" }));
    const link = await screen.findByRole("link", { name: "Open team summary" });
    expect(link).toHaveAttribute("href", `/s/${token}`);
    expect(writes).toEqual([{ project_ids: ["health-tracker"] }]);
  });

  it("opens a shared summary without a login and marks the page noindex", async () => {
    const token = "B".repeat(43);
    window.history.replaceState(null, "", `/s/${token}`);
    vi.mocked(fetch).mockResolvedValue(Response.json({
      summary: {
        name: "Aamir Mohammed Khan",
        headline: "Full-stack and AI application development",
        strengths: [
          { title: "Full-stack applications", description: "React and FastAPI.", source: "Technical Skills" },
          { title: "Grounded answers", description: "Hybrid retrieval and citations.", source: "Technical Projects" },
          { title: "Async workloads", description: "Worker queues and execution limits.", source: "Experience" },
        ],
        projects: [{ id: "entropy-oj", title: "Entropy-OJ", description: "Asynchronous judging.", source: "Experience" }],
        gaps: "Confirm role-specific requirements directly.",
        availability: "Confirm availability with Aamir.",
        contact_email: "aamir@example.test",
      },
      expires_at: "2026-12-12T00:00:00Z",
    }));
    render(<App />);
    await screen.findByRole("heading", { name: "Aamir Mohammed Khan" });
    expect(screen.getByRole("heading", { name: "Entropy-OJ" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to chat" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("button", { name: "Print or save as PDF" })).toBeInTheDocument();
    expect(document.head.querySelector('meta[name="robots"]')).toHaveAttribute("content", "noindex, nofollow");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/api/summary/${token}`),
      expect.objectContaining({ credentials: "omit", cache: "no-store", referrerPolicy: "no-referrer" }),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("renders header, status indicator, and starter chips on mount", async () => {
    vi.spyOn(api, "fetchHealth").mockReturnValue(new Promise(() => {}));
    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: /Aamir Mohammed Khan/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/Suggested Inquiries/i)).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Evaluation results unavailable" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /What is Aamir's experience with FastAPI and LLM systems\?/i,
      })
    ).toBeInTheDocument();
  });

  it("transitions status pill to 'Ready' when health check succeeds", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });
  });

  it("keeps authored starter answers available while live answers rest", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({
      status: "ok", ready: true, assistant_state: "resting",
    });
    const stream = vi.spyOn(sse, "streamChat");
    render(<App />);
    expect(await screen.findByText("Live answers resting")).toBeInTheDocument();
    expect(screen.getByRole("link", {name: "View professional profile"})).toBeInTheDocument();
    const starter = screen.getByRole("button", {name: /What is Aamir's experience with FastAPI and LLM systems/i});
    fireEvent.click(starter);
    expect(stream).not.toHaveBeenCalled();
  });

  it("transitions status pill to 'Offline' when health check fails", async () => {
    vi.spyOn(api, "fetchHealth").mockRejectedValue(new Error("Connection refused"));
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Offline")).toBeInTheDocument();
    });
  });

  it("allows user to type a question and stream assistant answer", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onToken("Aamir has 3+ years ");
      opts.callbacks.onToken("building AI apps.");
      opts.callbacks.onDone({ conversation_id: "conv-app-1" });
    });

    render(<App />);

    const textarea = screen.getByPlaceholderText(/Ask about Aamir's experience/i);
    fireEvent.change(textarea, {
      target: { value: "Tell me about his experience" },
    });

    const sendBtn = screen.getByRole("button", { name: /Send message/i });
    fireEvent.click(sendBtn);

    // Verify user message appears in list
    expect(screen.getByText("Tell me about his experience")).toBeInTheDocument();

    // Verify streamed assistant reply appears
    await waitFor(() => {
      expect(
        screen.getByText("Aamir has 3+ years building AI apps.")
      ).toBeInTheDocument();
    });
  });

  it("allows clicking a starter inquiry to start chat", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onToken("Core strengths include FastAPI and ONNX.");
      opts.callbacks.onDone({ conversation_id: "conv-app-2" });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    const chip = screen.getByRole("button", {
      name: /What are Aamir's core technical strengths\?/i,
    });
    fireEvent.click(chip);

    await waitFor(() => {
      expect(
        screen.getByText("Core strengths include FastAPI and ONNX.")
      ).toBeInTheDocument();
    });
  });

  it("delivers instant offline answer when starter chip is clicked while warming", async () => {
    vi.spyOn(api, "fetchHealth").mockReturnValue(new Promise(() => {})); // Never resolves (simulating cold start)
    render(<App />);

    const chip = screen.getByRole("button", {
      name: /What are Aamir's core technical strengths\?/i,
    });
    fireEvent.click(chip);

    await waitFor(() => {
      expect(
        screen.getByText(/Aamir's technical strengths center on pragmatic full-stack/i)
      ).toBeInTheDocument();
    });
  });

  it("shows '← Dossier Overview' button during active chat and resets to CoverState on click", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onToken("Aamir is specialized in distributed LLM architectures.");
      opts.callbacks.onDone({ conversation_id: "conv-app-3" });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    // Initially in Cover State
    expect(screen.getByText("CANDIDATE DOSSIER")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Return to candidate dossier overview/i })
    ).not.toBeInTheDocument();

    // Trigger an inquiry
    const chip = screen.getByRole("button", {
      name: /What is Aamir's experience with FastAPI and LLM systems\?/i,
    });
    fireEvent.click(chip);

    // Wait for message to stream in and reset button to appear
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Return to candidate dossier overview/i })
      ).toBeInTheDocument();
    });

    // Click the dossier overview navigation button
    const dossierBtn = screen.getByRole("button", {
      name: /Return to candidate dossier overview/i,
    });
    fireEvent.click(dossierBtn);

    // Should return to Cover State non-destructively
    expect(screen.getByText("CANDIDATE DOSSIER")).toBeInTheDocument();

    // Resume Chat button is now available to jump back
    const resumeBtn = screen.getByRole("button", {
      name: /Resume active chat conversation/i,
    });
    expect(resumeBtn).toBeInTheDocument();

    // Click Resume Chat -> returns back to active transcript with messages preserved
    fireEvent.click(resumeBtn);
    expect(
      screen.getByText("Aamir is specialized in distributed LLM architectures.")
    ).toBeInTheDocument();

    // Now click Clear Chat -> completely wipes session
    const clearBtn = screen.getByRole("button", {
      name: /Clear active conversation and reset/i,
    });
    fireEvent.click(clearBtn);

    expect(screen.getByText("CANDIDATE DOSSIER")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Resume active chat conversation/i })
    ).not.toBeInTheDocument();
  });

  it("renders summoned project card and opens architecture modal on click", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true, assistant_state: "ready" });
    vi.spyOn(sse, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onCard?.({
        id: "entropy-oj",
        title: "Entropy Online Judge",
        subtitle: "Competitive Programming & DSA Platform",
        summary: "Evaluates code in Linux sandbox.",
        role: "Solo Author",
        tech_stack: ["React 19", "Redis"],
        highlights: ["BullMQ asynchronous judging"],
        metrics: { Worker: "Dedicated VM" },
        github_url: "https://github.com/aamir-coding/entropy-oj",
        live_url: "https://entropy-oj.vercel.app",
        source_sections: ["J1", "J2"],
        architecture_details: "System uses Redis queue and Linux runner.",
      });
      opts.callbacks.onToken("Here is an overview of Entropy-OJ.");
      opts.callbacks.onDone({ conversation_id: "conv-card-1" });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Ask about Aamir's experience/i);
    fireEvent.change(textarea, { target: { value: "Tell me about Entropy-OJ" } });
    fireEvent.click(screen.getByRole("button", { name: /Send message/i }));

    // Wait for ProjectCard to render
    await waitFor(() => {
      expect(screen.getByText("Entropy Online Judge")).toBeInTheDocument();
    });

    // Click Inspect Architecture Blueprint button
    const inspectBtn = screen.getByRole("button", {
      name: /Inspect Architecture/i,
    });
    fireEvent.click(inspectBtn);

    // Verify modal is open and shows architecture details
    await waitFor(() => {
      expect(
        screen.getByRole("dialog", { name: /Entropy Online Judge/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText("System uses Redis queue and Linux runner.")
      ).toBeInTheDocument();
    });

    // Close modal via Close button
    const closeBtn = screen.getByRole("button", {
      name: /Close architecture modal/i,
    });
    fireEvent.click(closeBtn);

    // Verify modal is dismissed
    await waitFor(() => {
      expect(
        screen.queryByRole("dialog", { name: /Entropy Online Judge/i })
      ).not.toBeInTheDocument();
    });
  });

  it("opens Job Description Fit Report modal when '⚡ Role Fit' is clicked", async () => {
    vi.spyOn(api, "fetchHealth").mockReturnValue(new Promise(() => {}));
    vi.spyOn(api, "fetchFitPresets").mockResolvedValue([]);
    render(<App />);

    const fitBtn = screen.getByRole("button", {
      name: /Evaluate Job Description Alignment/i,
    });
    fireEvent.click(fitBtn);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Job Description Fit Report")).toBeInTheDocument();
    });
  });
});

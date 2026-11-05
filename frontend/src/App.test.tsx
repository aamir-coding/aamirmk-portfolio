import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import App from "./App";
import * as api from "./lib/api";
import * as sse from "./lib/sse";

describe("<App />", () => {
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
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true });
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });
  });

  it("transitions status pill to 'Offline' when health check fails", async () => {
    vi.spyOn(api, "fetchHealth").mockRejectedValue(new Error("Connection refused"));
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Offline")).toBeInTheDocument();
    });
  });

  it("allows user to type a question and stream assistant answer", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true });
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
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true });
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
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true });
    vi.spyOn(sse, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onToken("Aamir is specialized in distributed LLM architectures.");
      opts.callbacks.onDone({ conversation_id: "conv-app-3" });
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    // Initially in Cover State
    expect(screen.getByText("VERIFIED DOSSIER")).toBeInTheDocument();
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
    expect(screen.getByText("VERIFIED DOSSIER")).toBeInTheDocument();

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

    expect(screen.getByText("VERIFIED DOSSIER")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Resume active chat conversation/i })
    ).not.toBeInTheDocument();
  });

  it("renders summoned project card and opens architecture modal on click", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true });
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

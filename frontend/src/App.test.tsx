import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import App from "./App";
import * as api from "./lib/api";
import * as sse from "./lib/sse";

describe("<App />", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders header, status indicator, and starter chips on mount", () => {
    vi.spyOn(api, "fetchHealth").mockReturnValue(new Promise(() => {}));
    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: /Aamir Mohammed Khan/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/Suggested Inquiries/i)).toBeInTheDocument();
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

    // Verify user message appears
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
});

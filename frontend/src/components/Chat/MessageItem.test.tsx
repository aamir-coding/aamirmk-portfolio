import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MessageItem } from "./MessageItem";
import type { ChatMessage } from "../../lib/types";

describe("<MessageItem />", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders user inquiry message without copy button", () => {
    const userMsg: ChatMessage = {
      id: "u1",
      role: "user",
      content: "What is Aamir's primary stack?",
      timestamp: "12:00 PM",
      status: "done",
    };

    render(<MessageItem message={userMsg} />);

    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.getByText("What is Aamir's primary stack?")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Copy/i })).not.toBeInTheDocument();
  });

  it("renders assistant dispatch message with copy button and copies text", async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    const assistantMsg: ChatMessage = {
      id: "a1",
      role: "assistant",
      content: "Aamir is specialized in FastAPI, Python, Groq, and React.",
      timestamp: "12:01 PM",
      status: "done",
    };

    render(<MessageItem message={assistantMsg} />);

    expect(screen.getByText("AI assistant")).toBeInTheDocument();

    const copyBtn = screen.getByRole("button", { name: /Copy response text/i });
    expect(copyBtn).toBeInTheDocument();

    fireEvent.click(copyBtn);

    expect(writeTextMock).toHaveBeenCalledWith(
      "Aamir is specialized in FastAPI, Python, Groq, and React."
    );

    await waitFor(() => {
      expect(screen.getByText("Copied ✓")).toBeInTheDocument();
    });
  });

  it("renders streaming cursor when status is streaming", () => {
    const streamingMsg: ChatMessage = {
      id: "a2",
      role: "assistant",
      content: "Generating response",
      timestamp: "12:02 PM",
      status: "streaming",
    };

    render(<MessageItem message={streamingMsg} />);
    expect(screen.getByTestId("streaming-cursor")).toBeInTheDocument();
  });

  it("shows early citations only below the completed answer", () => {
    const message: ChatMessage = {
      id: "a3",
      role: "assistant",
      content: "",
      timestamp: "12:03 PM",
      status: "streaming",
      sources: [{
        chunk_id: "project",
        title: "Entropy project",
        type: "project",
        source_url: "https://entropy-oj.vercel.app/",
      }],
    };
    const { rerender } = render(<MessageItem message={message} />);
    expect(screen.getByText(/Preparing an answer/)).toBeVisible();
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();

    const answered = { ...message, content: "Aamir built Entropy’s coding workspace." };
    rerender(<MessageItem message={answered} />);
    expect(screen.getByText(answered.content)).toBeVisible();
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();

    rerender(<MessageItem message={{ ...answered, status: "done" }} />);
    const source = screen.getByRole("link", { name: /Entropy project/ });
    const answer = screen.getByText(answered.content);
    expect(source).toBeVisible();
    expect(answer.compareDocumentPosition(source) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    rerender(<MessageItem message={{ ...answered, status: "done", delivery: "cancelled" }} />);
    expect(screen.getByText("Stopped")).toBeVisible();
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();

    rerender(<MessageItem message={{ ...answered, status: "error" }} />);
    expect(screen.getByText("Interrupted")).toBeVisible();
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();

    rerender(<MessageItem message={{ ...answered, status: "done", delivery: "instant" }} />);
    expect(screen.getByText("Saved answer")).toBeVisible();
    expect(screen.getByRole("link", { name: /Entropy project/ })).toBeVisible();
  });
});

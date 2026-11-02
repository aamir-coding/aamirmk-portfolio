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

    expect(screen.getByText("INQUIRY")).toBeInTheDocument();
    expect(screen.getByText("Recruiter")).toBeInTheDocument();
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

    expect(screen.getByText("DISPATCH")).toBeInTheDocument();
    expect(screen.getByText("Aamir.AI")).toBeInTheDocument();

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
});

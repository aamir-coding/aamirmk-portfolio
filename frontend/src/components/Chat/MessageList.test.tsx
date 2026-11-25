import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type { ChatMessage } from "../../lib/types";
import { MessageList } from "./MessageList";

it("leaves the reader's position alone as a follow-up streams and gains sources", () => {
  const question: ChatMessage = { id: "q", role: "user", content: "What did Aamir build?", timestamp: "", status: "done" };
  const answer: ChatMessage = { id: "a", role: "assistant", content: "First answer.", timestamp: "", status: "done" };
  const history = [question, answer, { ...question, id: "q2", content: "How did he build it?" }];
  const pending: ChatMessage = { ...answer, id: "a2", content: "", status: "streaming" };
  const { rerender } = render(<MessageList messages={[...history, pending]} />);
  const log = screen.getByRole("region", { name: "Conversation history" });
  Object.defineProperty(log, "scrollHeight", { value: 2400 });
  log.scrollTop = 320;
  const writing = { ...pending, content: "He built it with React." };
  rerender(<MessageList messages={[...history, writing]} />);
  expect(log.scrollTop).toBe(320);
  log.scrollTop = 145;
  rerender(<MessageList messages={[...history, { ...writing, status: "done",
    sources: [{ chunk_id: "project", title: "Project", type: "project" }] }]} />);
  expect(log.scrollTop).toBe(145);
});

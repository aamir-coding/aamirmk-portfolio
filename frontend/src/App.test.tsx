import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";
import * as api from "./lib/api";

describe("<App />", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders header and initial checking status", () => {
    vi.spyOn(api, "fetchHealth").mockReturnValue(new Promise(() => {}));
    render(<App />);

    expect(screen.getByRole("heading", { name: /Aamir Mohammed Khan/i })).toBeInTheDocument();
    expect(screen.getByText(/Checking backend connectivity\.\.\./i)).toBeInTheDocument();
  });

  it("renders backend status when health check succeeds", async () => {
    vi.spyOn(api, "fetchHealth").mockResolvedValue({ status: "ok", ready: true });
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Status:/i)).toBeInTheDocument();
      expect(screen.getByText(/OK/i)).toBeInTheDocument();
    });
  });

  it("renders error notice when health check fails", async () => {
    vi.spyOn(api, "fetchHealth").mockRejectedValue(new Error("Network timeout"));
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Connection notice:/i)).toBeInTheDocument();
      expect(screen.getByText(/Network timeout/i)).toBeInTheDocument();
    });
  });
});

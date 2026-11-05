import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { z } from "zod";
import { EvalSummarySchema } from "../../lib/evals";
import EvalPage from "./EvalPage";
import { EvalBadge } from "./EvalBadge";

const artifact = z.object({ report: z.unknown() }).parse(JSON.parse(readFileSync(resolve(process.cwd(),
  "../backend/app/data/eval-summary.json"), "utf8")));
const report = artifact.report as { replay: { passed: number; total: number } };
const body = { status: "available", reason: null, report,
  badge: `Replay checks: ${report.replay.passed}/${report.replay.total} (offline)` };

afterEach(() => vi.unstubAllGlobals());

it("uses the exact backend badge and links to the public record", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body))));
  render(<EvalBadge />);
  const badge = await screen.findByRole("link", { name: body.badge });
  expect(badge).toHaveAttribute("href", "/evals");
});

it("shows the failed validation and five disagreements without accuracy claims", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body))));
  render(<EvalPage />);
  expect(await screen.findByRole("heading", { name: body.badge })).toBeInTheDocument();
  expect(screen.getByText("failed", { exact: true })).toBeInTheDocument();
  expect(screen.getByText(/Model accuracy: unavailable/)).toBeInTheDocument();
  expect(screen.getAllByText(/validation-0[68]:/)).toHaveLength(5);
  expect(screen.getByRole("table", { name: /validation agreement/ })).toBeInTheDocument();
  fireEvent.focus(screen.getByRole("link", { name: /Return to portfolio/ }));
});

it("stale evidence renders without numeric badges", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
    status: "stale", report: null, reason: "Changed evidence", badge: "Evaluation results stale",
  }))));
  render(<EvalPage />);
  expect(await screen.findByText("Evaluation results stale")).toBeInTheDocument();
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
});

it("rejects a mismatched badge and false accuracy mode", () => {
  expect(EvalSummarySchema.safeParse({ ...body, badge: "100% accurate" }).success).toBe(false);
  expect(EvalSummarySchema.safeParse({ ...body, report: { ...report, kind: "live_accuracy" } }).success).toBe(false);
});

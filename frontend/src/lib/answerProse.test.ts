import { describe, expect, it } from "vitest";
import { answerProse } from "./answerProse";

describe("assistant source annotations", () => {
  it.each([
    " 【University-Wide First Place — Graph Algorithm Contest (2025)】",
    " 【Detailed Overview】",
    " 【Identity and Professional Summary】",
    " 【Source: VayuSetu — Google Cloud Hackathon Project (X11, AC3)】",
    " *(Source: Academic Excellence — CGPA 9.77/10.0)*",
    " (Source: VayuSetu (Track 2))",
    " [Source: résumé]",
    "\n\n*Source: “School Background (Class 10 and 12)” — Aamir’s résumé.*",
  ])("withholds %s even when it arrives one character at a time", receipt => {
    const answer = "The team placed second runner-up.";
    for (let i = 1; i <= receipt.length; i++) {
      expect(answerProse(answer + receipt.slice(0, i), true).replace(/[\s*]+$/, "")).toBe(answer);
    }
    expect(answerProse(answer + receipt).trimEnd()).toBe(answer);
  });

  it("preserves the next claim, ordinary parentheses, code and links", () => {
    const answer = "First 【Detailed Overview】. Next (Track 2).";
    expect(answerProse(answer)).toBe("First. Next (Track 2).");
    const markdown = "Review [Source: project](https://example.org) and `【literal】` (source code).";
    expect(answerProse(markdown)).toBe(markdown);
    expect(answerProse("A (software project)", true)).toBe("A (software project)");
    expect(answerProse("First 【Detailed Overview】 . Second.")).toBe("First. Second.");
    expect(answerProse("**VayuSetu**【Detailed Overview】 placed third."))
      .toBe("**VayuSetu** placed third.");
    expect(answerProse("**Source:** [Official result](https://example.org/award)"))
      .toBe("[Official result](https://example.org/award)");
  });
});

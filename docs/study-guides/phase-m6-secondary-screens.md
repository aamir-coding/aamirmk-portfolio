# M6 study guide · Secondary screens and footer

The secondary routes let readers forward a verified brief, inspect what the
evaluation actually measured, or review protected recruiter records. The
same visual system supports all three jobs, with layout tuned to each one.

## Trace the implementation

| Source | What to inspect |
| --- | --- |
| `frontend/src/App.tsx` | Route selection adds noindex and no-referrer metadata to shared summaries. The home footer keeps direct email, LinkedIn, GitHub, and the privacy disclosure in the reading order. |
| `frontend/src/components/Summary/SummaryPage.tsx` | Token shape is resolved before fetch. Server results produce the ready, unavailable or retriable state. The absolute expiry timestamp is formatted in UTC. |
| `frontend/src/styles/summary.css` | The page measure caps the screen layout. A screen-only breakpoint stacks the sections on phones. Print removes the web controls and uses an inner 15 mm margin. |
| `frontend/src/components/Evals/EvalPage.tsx` | The evidence artifact supplies the badge, category counts, limitations, judge gate and hashes. The tables associate row and column headers through `scope`. |
| `frontend/src/components/Admin/AdminPage.tsx` | The access transition focuses the new heading or the credential field. The existing fetch module owns the bearer header and cache policy. Four-column tables sit in keyboard-scrollable regions. |
| `frontend/src/styles/under-hood.css` | The receipt uses aligned labels and values, allows long hashes to wrap, and retains the existing disclosure and telemetry. |

## Interview discussion

**How is a capability URL different from a session login?** The unguessable URL
grants access to that one summary until the server expires it. The front end
checks the token’s shape to avoid unnecessary requests. Only the server can
decide if a correctly shaped token still resolves. Referrer and cache policies
limit other places where the URL or its response can appear.

**Why are there two kinds of margin in print?** The browser can place the
document URL in a running footer. In Chromium, setting the page margin to
zero leaves no room for its automatic footer. Padding inside the document then
supplies the readable content margin. The print check inspected both text and
link annotations because an invisible URL could still be in a PDF link target.

**Why keep a dense table instead of turning rows into cards on a phone?** A native
table keeps the meaning of a cell connected to its row and column. The small
evaluation tables reflow at phone widths. The wider admin records have a named,
focusable scroll area to preserve those relationships and the full text.

## References

- [CSS page margins and Chromium’s automatic headers and footers](https://developer.chrome.com/blog/print-margins)
- [W3C WAI tutorial on tables with both kinds of header](https://www.w3.org/WAI/tutorials/tables/two-headers/)

## Teach-back

1. Which layer determines whether a shared team summary still opens? What does the client check first?
2. Why inspect a generated PDF’s link annotations as well as its visible text?
3. How does a named, focusable scroll area help a keyboard user read a wide table?

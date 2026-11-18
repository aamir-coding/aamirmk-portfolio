# M5 study guide · Fit and recruiter actions

The fit report gives recruiters a concise view of how Aamir’s evidence relates
to a role. The reveal order puts must-have gaps, partial matches, and strong
matches ahead of the source job description and the technical receipt.

## Trace the implementation

| Source | What to inspect |
| --- | --- |
| `frontend/src/components/Fit/FitReportModal.tsx` | `showModal()` opens the browser’s modal layer. A layout effect moves focus on form, progress, and result transitions. Dismissal aborts an active request and closes the dialog. |
| `frontend/src/components/Fit/FitReportCard.tsx` | The origin comes from the provider receipt or the existing explicit cache and preset flags. Counts are server values. Must-have order affects reading priority. Exact source mappings supplement visible raw evidence IDs. |
| `frontend/src/components/Fit/FitProgressStepper.tsx` | The browser’s progress element shows the percentage from the existing event. A separate status presents the current stage. |
| `frontend/src/components/Chat/HandoffCard.tsx` | The preview uses the same transcript slice that goes into the payload. The form checks consent before making a request and keeps the handoff ID across retries. |
| `frontend/src/components/Chat/AnswerFeedback.tsx` | Choosing a rating reveals the optional reason. The network request happens on form submission. |
| `frontend/src/components/Summary/SummaryAction.tsx` | The button describes the scope of the share link. Its request sends project IDs. The returned link shows its expiry and sets a no-referrer policy. |

## Interview discussion

**Why use a native dialog?** The browser handles top-layer placement, makes
the background inert, and records the previously focused element.
Application code handles request cancellation and which heading represents
the next screen. An explicit gap follow-up closes the modal before focusing
the conversation.

**Why keep the raw evidence ID beside a label?** A friendly link helps a person
inspect the project. The stable ID lets them trace what the report cited.
The link map uses exact known IDs. Requirement-local evidence checks and the
meaning of the server verdict stay in the existing evaluation pipeline.

**What is sent by each recruiter action?** Live analysis sends the job
description and optional role title. A consented handoff sends its previewed
messages and optional reply email. Feedback sends an answer ID, rating and
optional reason. The team-summary request sends selected project IDs.

## References

- The HTML Standard defines [modal dialog open, cancel, and close behavior](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element).
- WAI-ARIA Authoring Practices describes the [dialog keyboard and focus pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

## Teach-back

1. What does the browser do when the fit dialog opens, and which steps still belong to the app?
2. How can a reader distinguish an authored example, a cached report, and a fresh live assessment?
3. Which request sends previewed messages, and how does its payload differ from a team summary?

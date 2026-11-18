# M4 study guide · Assistant interaction

A recruiter can read a stream as it arrives, inspect earlier evidence, or draft
a follow-up in the same composer. The interface distinguishes those actions so
a token update cannot take over an earlier reading position or cancel a draft.

## Trace the implementation

| Source | What to inspect |
| --- | --- |
| `frontend/src/components/Chat/MessageList.tsx` | Scroll position belongs to the history element. A reader near the bottom follows updates. An explicit new turn or Jump to latest resumes following. Keyboard Jump focuses the history with `preventScroll` to keep the outer page steady. |
| `frontend/src/components/Chat/ChatInput.tsx` | Input keeps IME and multiline behavior. Enter submits an idle draft and leaves an active draft in place while the assistant works. Stop prevents the native click default because its control changes back into Send during the click. Escape is the other deliberate cancellation path. |
| `frontend/src/App.tsx` | Typed submission keeps composer focus. An explicitly selected question can focus the conversation heading. The completed message drives a separate polite status and the recovery panel offers the verified saved answer. |
| `frontend/src/components/Chat/MessageItem.tsx` | Waiting, saved, stopped, and interrupted states are shown with plain text. Answer prose and source links come before cards. Existing receipt and handoff rendering receives the same message data. |
| `frontend/src/components/Chat/SourceChips.tsx` | Public source links retain their existing URL eligibility check. Other source labels and section identifiers stay readable as references. |

## Interview discussion

**Why store scroll-follow intent in a ref?** The browser can deliver scroll
events frequently. The ref keeps the latest intent available without a render
for every pixel. The visible catch-up control only changes when the reader
crosses the threshold.

**What is the difference between a named history region and a live completion
status?** Screen-reader users can navigate the complete history at any time.
The polite status has stable, short text and is refreshed for each completed
reply. Individual token updates leave that status alone.

**Why use the verified saved answer in recovery?** A recruiter can inspect an
existing, sourced example while the live service is unavailable. The example
enters through the instant-answer path and needs no chat request. Its delivery
label makes the provenance visible in the transcript.

## References

- WAI-ARIA defines [named regions](https://www.w3.org/TR/wai-aria-1.2/#region), [live logs](https://www.w3.org/TR/wai-aria-1.2/#log), and [polite status messages](https://www.w3.org/TR/wai-aria-1.2/#status).
- The browser focus API supports [moving focus without scrolling](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/focus).
- Browser scrolling exposes the [current element offset and subpixel behavior](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollTop).

## Teach-back

1. What happens to the history offset if a reader scrolls up while another token arrives? What changes after Jump to latest?
2. How do Enter, Shift+Enter, IME composition, and Escape differ while an answer is streaming?
3. After a 429 response, how can a recruiter see a sourced answer without starting a second chat request? Which label confirms its delivery?

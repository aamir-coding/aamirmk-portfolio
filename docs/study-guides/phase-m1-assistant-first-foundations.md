# M1 study guide · Assistant-first portfolio foundations

## The design problem

A recruiter needs to identify the candidate, ask a useful question, or inspect
work without scrolling past the introduction. The same entry point has to be
useful if the assistant is warming, resting, or unreachable. The layout makes
the conversation the earliest product interaction and keeps project proof one
section below.

## Trace the implementation

| Source | Walkthrough |
|---|---|
| `frontend/src/App.tsx` | The route function preserves the lazy-loaded evaluation, summary, and admin pages. `Portfolio` owns cover versus transcript presentation. The same `ChatInput` remains mounted across both. `showChat` and `showOverview` schedule heading focus only on an explicit transition. |
| `frontend/src/components/Cover/CoverState.tsx` | The candidate identity is a real, programmatically focusable heading. The skip link and the heading ref give browser navigation and app state changes the same logical destination. |
| `frontend/src/components/Cover/SelectedWork.tsx` | Public project evidence is rendered as three static articles. The work list depends on no readiness, chat, or backend state. |
| `frontend/src/components/Chat/ChatInput.tsx` | A native labeled textarea owns draft input. The key handler leaves composition events and Shift+Enter alone, while form submission still validates an empty draft. Keyboard activation preserves composer focus without stealing focus on load or asynchronous completion. |
| `frontend/src/components/Chat/MessageList.tsx` | The log can scroll independently. Its count tracks whether a new user turn was submitted, while its scroll position tracks whether the reader is at the latest content. Token updates preserve the reader's position near older messages. |
| `frontend/src/components/Chat/MessageItem.tsx` | The reply and citations precede project cards. Typed server results still determine when those cards appear. |
| `frontend/src/data/answers.json` | The exact featured question has a separate saved response sourced to the public résumé and project. The existing instant-answer path adds it to the transcript without a provider call. |
| `frontend/src/styles/portfolio.css` | Scoped Field of Evidence tokens cover the public shell. Fluid type, a bounded measure, and narrow-screen layout preserve the order of actual document landmarks. |

## Interview discussion

**Why keep one composer?** React associates state with position in the rendered
tree. Replacing a landing form with a different transcript form can discard the
draft and browser focus. A single stable instance keeps draft ownership
local while the shell changes around it.

**Why focus a heading instead of the textarea?** On initial page load the user
has exercised no navigation intent. After choosing a starter, a transcript
heading communicates the transition and avoids opening a mobile keyboard.
A keyboard shortcut and ordinary tab order still provide direct access to the
composer.

**How does a scroll ref differ from React render state?** Scroll position is an
imperative browser detail. Keeping the follow position in a ref lets scroll
events update it without scheduling React renders. A new turn and a token
update have different effects on where the reader should be.

**How is an authored answer distinguished from model output?** It enters via
the existing instant-answer path with its known sources and delivery
provenance. It requires no live provider call. The visible authoring choice
changes the entry experience while the streaming schema stays in its
existing module.

## Primary references

- React explains when layout effects run and why they should be narrowly scoped. [React useLayoutEffect](https://react.dev/reference/react/useLayoutEffect)
- The browser focus API documents how to focus a control with or without moving the viewport. [MDN HTMLElement.focus](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/focus)
- A key event reports when it is part of an active text composition session. [MDN KeyboardEvent.isComposing](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/isComposing)
- A scroll element owns its own vertical offset, independently of the document's offset. [MDN Element.scrollTop](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollTop)

## Teach-back

1. Trace a first visit through the landing, composer, and first live response.
   Which transition moves focus and which event leaves it alone?
2. What changes when the featured question is selected while the service is
   resting? Which steps and source links still run in the browser?
3. How should the log react to a token arriving while a recruiter reads an older
   answer, compared with a deliberate follow-up submission?

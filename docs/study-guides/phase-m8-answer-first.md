# M8 — Streaming answers and visual evidence

## Delivery and presentation

The recorded stream can send source metadata and tool cards before text. The
parser and `useChat` keep those events on the message as they arrive.
`MessageItem.tsx` uses the message status to control when each part is visible.
A live message can show the waiting copy, then the formatted text. Once complete,
the text is followed by source links and any project cards. A saved answer
arrives already complete. A stopped or interrupted answer retains partial text.

`MessageList.tsx` keeps track of the previous last message. The ID links its
streaming and settled states. For incoming tokens the transcript still follows
the last turn when the reader is at the bottom. When that same turn settles
with text, the layout effect preserves the transcript's position and computes
whether Jump to latest is needed. Its button scrolls and focuses the conversation
history. The completion status stays separate from the text that updates with
each token.

- [React useLayoutEffect](https://react.dev/reference/react/useLayoutEffect)
- [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)

## Motion and image strategy

The concept's hero paints a static WebP first. A small canvas draws a short
wave over the river glyphs. The canvas stops after the animation, or when
reduced motion becomes active. The page can show the still with scripts disabled.
It uses a CSS view timeline for a subtle independent movement as the cover
leaves the viewport. Mobile images use a different crop when it helps
a reader see the actual UI.

- [CSS Scroll-driven Animations specification](https://www.w3.org/TR/scroll-animations-1/)
- [HTML picture element](https://html.spec.whatwg.org/multipage/embedded-content.html#the-picture-element)

## Interview practice

**Why does the frontend wait to show sources even though it already has them?**
The transport can deliver evidence whenever it is ready. Presentation keeps the
loading state and answer primary, then exposes evidence at the end of the turn.
The same events support both behaviors without a server contract change.

**How can you test the regression without waiting for a real model?**
Hold a local SSE fixture after the source and card frames. Assert the loading
state. Send tokens and check that the text appears by itself. Deliver the
completion frame and confirm that evidence appears below the text. For a long
follow-up, compare the last line's position within the transcript on either
side of completion and activate Jump to latest by keyboard.

**What are the layers of the motion fallback?**
The static poster covers reduced motion, disabled scripts and older browsers.
The glyph wave is an optional, short enhancement. CSS drives the scroll-linked
transform when the browser supports it.

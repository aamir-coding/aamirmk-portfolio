# M8 — Streaming answers and visual evidence

## Delivery and presentation

The recorded stream can send source metadata and tool cards before text. The
parser and `useChat` keep those events on the message as they arrive.
`MessageItem.tsx` uses the message status to control when each part is visible.
A live message can show the waiting copy, then the formatted text. Once complete,
the text is followed by a native source disclosure and any project cards. A saved
answer arrives already complete. A stopped or interrupted answer retains partial text.

`MessageList.tsx` keeps track of the previous last message. The ID links its
streaming and settled states. For incoming tokens the transcript still follows
the last turn when the reader is at the bottom. When that same turn settles
with text, the layout effect preserves the transcript's position and computes
whether Jump to latest is needed. Its button scrolls and focuses the conversation
history. Opening the disclosure can change the scrollable height without a scroll
event. The transcript handles the native toggle event during capture and updates
the button without moving the reader. The completion status stays separate from
the text that updates with each token.

- [React useLayoutEffect](https://react.dev/reference/react/useLayoutEffect)
- [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
- [HTML details element](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-details-element)

## Motion and image strategy

`HeroArt.tsx` provides a responsive WebP first and defers the optional
`fieldMotion.ts` import until after page load. The renderer samples the landscape
into a lattice and caches the static glyph layer. Each frame copies that layer
and redraws the glyphs affected by the timed sweep or pointer. Pointer coordinates
convert from the viewport to the scaled artwork, including the crop caused by
`object-fit: cover`. The pull falls smoothly to zero at its edge.

The canvas suspends when the artwork leaves the viewport or the document is
hidden. Reduced motion and keyboard pause show the poster. The no-script entry
provides direct résumé and project links. A CSS view timeline shifts the
decorative layer slightly as the cover leaves the viewport. Mobile project images
use closer crops where they make product details easier to see.

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
The poster provides the cover while motion loads, when it is paused, and when
reduced motion is requested. The canvas draws only while its cover can animate.
The document keeps direct links usable with JavaScript disabled.

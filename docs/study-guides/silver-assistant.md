# Silver assistant integration

The home screen, transcript and evidence panel offer three ways to reach the
same project material. A recruiter can type a follow-up while streaming, inspect
a project directly, or reuse one of the bundled answers when capacity is resting.

## Reading the implementation

1. In `frontend/src/App.tsx`, follow `handleSelectPrompt` into the existing chat
   hook. The health and capacity state determine whether a supported starter
   uses an authored answer. A custom question uses the ordinary live path.
2. In `components/Chat/MessageItem.tsx`, find `shownProjects`. After completion,
   it associates the answer's card IDs and source IDs with the showcase. A card
   from another project can still render through the existing card component.
3. In `components/Cover/SelectedWork.tsx`, the screenshot and public links come
   from the catalog. The optional architecture, role, stack and metrics come
   from the card on the specific answer. They have different provenance.
4. In `components/Cover/SidePanel.tsx`, a native dialog contains keyboard focus.
   Its cleanup restores focus. The parent layout effect takes over when a new
   question explicitly navigates to the conversation.
5. In `components/Cover/HeroArt.tsx`, page load, viewport intersection, document
   visibility and motion preferences determine whether the cover can animate.
   `fieldMotion.ts` updates a sparse glyph layer. `liquidRiver.ts` supplies
   Paper's shader with the preprocessed mask and caps the drawing resolution.
   Enter a conversation to see why cleanup must cover both a rendered frame and
   an import or image decode that may still be pending.

## Three interview questions

- A response supplies citations before the first token. Which layer should
  retain those citations, and when should the UI expose them?
- A recruiter closes project evidence with Escape, then later submits a new
  question from that same panel. Where should focus go in each case?
- How would you verify on a low-powered phone that a still terrain fallback
  actually avoids running the GPU shader?

The first answer separates transport order from presentation. The second
distinguishes dismissal from navigation. For the third, use a fresh reduced-motion
session, inspect resource requests and the canvas, then repeat on a device
without WebGL and verify the composer and project links still work.

[Paper Liquid Metal](https://shaders.paper.design/liquid-metal) · [React lazy](https://react.dev/reference/react/lazy) · [HTML dialog](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element)

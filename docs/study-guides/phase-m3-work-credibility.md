# M3 study guide · Work and credibility

The landing assistant is a live way to explore Aamir’s background. Selected
work lets the same visitor inspect his work directly. The assistant’s feature
uses a real saved answer with citations, while Entropy Online Judge and
HealthTracker expose live demos and source code.

## Trace the implementation

| Source | What to inspect |
| --- | --- |
| `frontend/src/components/Cover/SelectedWork.tsx` | The section is named by the `#work` heading and keeps the three existing project fragments. The assistant article comes first in the DOM. Links are normal anchors with descriptive names. |
| `frontend/src/components/Cover/art/assistant-saved-answer.webp` | The capture comes from the client exercising the authored AlgoUniversity answer in the resting state. Its two source chips point to the résumé and Entropy demo. |
| `frontend/src/styles/portfolio.css` | Flexible grid tracks keep the feature and two project entries within the available width. The wide figure reserves its aspect ratio. Narrow layouts show the readable excerpt, and focused links use the portfolio focus rule. |
| `frontend/index.html` | The browser handles the `noscript` fallback with the résumé and public project destinations. |
| `frontend/src/App.test.tsx` | The offline test opens the normal page and checks the named work section's six link destinations with the assistant unavailable. |

## Interview discussion

**Why use a native anchor for source and demo links?** The browser defines its
behavior for keyboard, touch, opening in a new tab, link previews, and copying
the address. The same destination remains available in the no-script entry.

**What happens if the work screenshot fails?** The browser already has the
question, a short equivalent of the saved answer, and the caption in the DOM.
The image error hides the broken resource. Its containing figure keeps its
geometry, and the links remain separate from the image.

**What does the evaluation record establish?** It reports measured checks and
their scope, including the status of the independent validation gate. The
portfolio feature gives visitors a route to review them. Its saved-answer
example illustrates the citation UI and carries no model-accuracy claim.

## References

- Project claims are sourced to [the published résumé](https://aamirmk-portfolio.vercel.app/resume.pdf). The current project code is in [the portfolio repository](https://github.com/aamir-coding/aamirmk-portfolio), [Entropy Online Judge](https://github.com/aamir-coding/entropy-oj), and [HealthTracker](https://github.com/aamir-coding/health-tracker).
- The browser defines link behavior and image text alternatives in the [HTML Standard](https://html.spec.whatwg.org/multipage/).
- The public record documents the project’s measured results and caveats. [Evaluation record](https://aamirmk-portfolio.vercel.app/evals)

## Teach-back

1. Which destinations can a recruiter reach with JavaScript disabled? Follow the paths starting from the HTML entry.
2. How does the saved-answer example remain understandable if a browser blocks the image or a visitor uses a screen reader?
3. What can the screenshot establish about the product, and where would you look to evaluate retrieval or model accuracy?

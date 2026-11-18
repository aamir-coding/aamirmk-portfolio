# M7 study guide · Regression and polish

M7 verifies a recruiter’s route from the cover to project evidence, the assistant,
role fit, sharing, and contact. It distinguishes the functionality verified
with controlled fixtures from behavior that depends on a deployed service or a device.

## Implementation trace

| Source | What to inspect |
| --- | --- |
| `frontend/src/main.tsx` and `frontend/src/configureValidation.ts` | The first module import disables dynamic code generation in Zod before the app initializes schemas. The browser keeps enforcing the existing script policy. |
| `frontend/src/components/Chat/formatHelpers.ts` | URL normalization runs before checking destinations known to be unavailable. A suppressed link still leaves the citation text visible. |
| `frontend/src/data/answers.json` | The existing prompt keys trigger authored answers while live service is warming or resting. Source IDs are retained where they support the claim. The source links point to the résumé or a verified project. |
| `frontend/src/styles/fit.css` | Long strings must be allowed to contribute a small minimum width to the report grid. That also keeps open disclosure text inside the scroll pane. |
| `frontend/src/styles/portfolio.css` | The mobile masthead paints above the cover so the full nav focus outline remains visible. The tab order and target size stay the same. |
| `frontend/scripts/check-bundle.mjs` | The verifier starts from the HTML entry and follows static imports. A lazy route’s bundle is outside the initial JavaScript total. |

## Interview discussion

**What did the CSP event tell us?** A browser can block a library’s optional
evaluation probe and still report the attempt. The app in this case kept
working through its fallback. Setting the supported JIT-less option before schema
initialization kept the validation behavior and removed the attempt.

**Why check both a 320 CSS px viewport and 200% text?** A narrow layout checks
columns, scrolling and control order at an equivalent width to 400% zoom on a
1280 px display. Enlarging root text additionally checks what happens when copy
grows within the available width. Real mobile browser controls and keyboard
behavior require a physical-device check. [W3C explanation of reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)

**How should a controlled LCP comparison be read?** Fix the viewport, network,
CPU, test route, and assets. Collect multiple fresh trials and compare the
median. That helps attribute differences in a lab. Field data covers more real
devices, networks, and cache states. [Web Vitals](https://web.dev/articles/vitals)

**What does replay prove?** Recorded responses let CI test retrieval and check
regressions without provider calls. Current model accuracy still depends on
independent evidence beyond those recordings.

## References

- [Zod configuration for Content Security Policy](https://zod.dev/compile#content-security-policy)
- [W3C Content Security Policy](https://www.w3.org/TR/CSP3/)

## Teach-back

1. Why configure Zod before importing modules that create schemas?
2. How can a report fit visually at 320 px and still have horizontal overflow inside its dialog?
3. Which conclusions can you draw from a three-run lab median, and which need field or device evidence?

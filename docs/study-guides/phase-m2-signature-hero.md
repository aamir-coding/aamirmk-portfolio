# M2 study guide · Field of Evidence artwork

The visual brief asks one landscape to work at three scales. At wide widths
the brightest ridge sits to the right of the composer. The tablet composition
keeps the pass and river in frame as the hero narrows. The phone composition
puts the reflected light in the bottom margin, where it has room alongside
the featured question. All three depict an invented landscape.

## Trace the implementation

| Source | What to inspect |
| --- | --- |
| `frontend/src/App.tsx` | The cover branch is the only place that renders `HeroArt`. The composer, featured question, and work links keep their existing behavior. |
| `frontend/src/components/Cover/HeroArt.tsx` | The browser picks the first matching media source and uses the wide still as the default. The empty alternative text and hidden ancestor communicate the artwork's decorative purpose. Native load and error events control the failed-image treatment as the selected source changes. |
| `frontend/src/components/Cover/art/` | Three local WebP files hold the different crops. The app ships their rendered pixels. |
| `frontend/src/styles/portfolio.css` | An isolated stacking context keeps the picture visually behind the cover. Its absolute box takes no room in document flow, and `pointer-events: none` leaves the controls available. Forced colors omit the art so the cover can use the system palette. The short desktop reveal is enabled through a motion preference. |

## Interview discussion

**Why three compositions?** The image's subject and the copy change position
relative to each other as the viewport narrows. Resolution selection alone
keeps the same composition. The `picture` sources let the browser choose one
composition at the appropriate viewport, including the smaller phone file.

**How can decorative art affect accessibility?** The image can be entirely
absent from the accessibility tree and still lower visible text contrast. A
pixel check samples the brightest part of the crop beneath each text region.
The phone reflection and forced-colors treatment address two different cases:
the first controls the painting's brightness, and the second lets the browser
use its own foreground and background colors together.

**Why measure layout during the reveal?** CSS rules describe intent. The
browser's layout counter measures whether geometry was recomputed during
replay. The opacity change keeps the existing flow intact. A timed
Chrome replay exercises the same CSS animation under CPU throttling.

## Primary references

- The dot lattice and the still-first comparison are adapted from the method described in the [0xSero ASCII Art craft guide](https://raw.githubusercontent.com/0xSero/ascii-art/main/SKILL.md).
- Responsive sources and their matching rules are documented in the [HTML Standard](https://html.spec.whatwg.org/multipage/embedded-content.html#the-picture-element).
- User discretion over animated movement is covered by the [Media Queries specification](https://drafts.csswg.org/mediaqueries-5/#prefers-reduced-motion).

## Teach-back

1. Which image will the browser choose at 375, 1024, and 1440 px? How would you check that it only requested the selected file?
2. How can a decorative image interfere with reading in forced-colors mode even if its alternative text is empty?
3. If the artwork request failed, which CSS rules would let the hero stay readable and the composer stay in the same place?

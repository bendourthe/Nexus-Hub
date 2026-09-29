# Teaching and design contract

The same example runs through all seven lessons: turn meeting notes into a status brief. Essential explanations remain visible without JavaScript or motion. Every diagram has native text labels; animation only highlights the relationship being explained.

| Lesson | Question | Illustration | Example / takeaway |
|---|---|---|---|
| Model | What does a model do? | Separate training from use; prompt and learned patterns feed the next output token. | The model drafts a brief, but a plausible sentence can be wrong. A prompt changes the input, not its trained weights. |
| Tokens | What does the model read? | A short sentence split into illustrative token chips, then a shared input/output budget. | Pieces can be words, word parts, or punctuation. Tokenization and media accounting depend on the model. |
| Prompt | How do I ask clearly? | Vague request beside a brief annotated with task, audience, constraints, and format. | Ask for decisions, owners, and dates; require missing information to be marked. |
| Context | What should I provide? | A document tray feeding the current request; unrelated files stay outside. | Meeting notes plus project summary, with room for the answer. More context is not automatically better context. |
| Harness | What turns an answer into useful work? | Three nested responsibilities: model, platform, Nexus procedures. | The platform supplies tools and permissions; Nexus supplies reusable skills, commands, rules, and supported hooks. |
| Loop | How does the work reach a finish line? | Draft -> check -> revise, with a visible pass exit and a bounded escalation exit. | Stop when decisions have evidence and owners/dates are present or explicitly unknown; ask after two failed revisions. |
| Graph | How do several steps work together? | Notes branch to decisions and actions, then join at one checked brief. | The join waits for both results. A node may be a person, tool, model, or ordinary code. |

## Layout grammar

Retain the existing teal, cream, dark surfaces, wordmark, approved platform marks, and system fonts. Use a consistent reading edge, 16-18px body text, 14px minimum instructional labels, short sentence-case headings, and a 4/8/12/16/24/32/48px spacing scale. On desktop, each lesson places a short explanation next to one large diagram. At narrow widths, the same reading order stacks. Avoid full-height panels and large decorative gaps.

Home keeps its identity and install block. Replace repeated benefit/comparison grids with a three-layer product distinction and one request-to-artifact demonstration. Training keeps the game and file explorer, adds a short learning objective, and represents not-run/running/complete/failed consistently.

## Motion contract

One finite highlight sequence per illustration, triggered by Replay. Pause cancels its timer; leaving the viewport, changing route, hiding the document, or switching to reduced motion stops work. Reduced motion shows the same complete diagram. No automatic looping diagram or idle reading-page canvas. Geometry comes from CSS, not repeated heading measurement.

## Assertion migration

The following legacy assertions are candidates for replacement only when their owning scene changes. Preserve approved asset bytes, installation commands, hashes, offline behavior, theme persistence, keyboard focus, Training data parity, deterministic game behavior, and presentation exit/reset coverage.

| Legacy concern | Disposition | Successor proof |
|---|---|---|
| No-wrap headings, forced font fitting, unbounded body width, doubled uppercase tags | Superseded by readable type and responsive composition. | Browser label bounds, >=14px instructional labels, body reading measure, 320-1920px geometry. |
| Always-looping sequences, hidden/revealed node counts, exact choreography | Superseded by complete-at-rest diagrams and finite highlighting. | Cold-load, direct-scroll, no-JS, reduced-motion, replay/pause, route/visibility cancellation. |
| Six old Foundations scenes, eight model stages, modality ladder, chatbot/action split, five harness stages | Superseded by the seven-lesson contract above. | Ordered lesson inventory, exact teaching relationships and visible concrete examples. |
| Home subtitle, repeated comparison cards, absolute enforcement claims | Superseded by the approved concise product explanation. | Model/platform/Nexus responsibility checks, artifact example, preserved identity/install asset checks. |
| Training pre-run gate reads PASS | Defect, not compatibility. | Initial and reset states pending; completion only after command output and artifact are available. |

Each removed test function must be enumerated in the final migration register with its replacement, including durable checks moved out of a dated suite. No blanket skips or expected failures.

## Construction ceiling

Reuse the self-contained HTML and existing Playwright installation. No framework, runtime dependency, generated decorative assets, network access, new game engine, or unrelated catalog changes.

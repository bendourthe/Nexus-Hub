# QuizKit (reference implementation)

A small, open-source trivia quiz library. It is shipped here as a local reference for the training's `/compare` step: it stands in for an open-source repository you would otherwise compare against over the network, so the demo works offline and the same every time.

## What is notable

QuizKit randomizes the deck on every run, so players cannot memorize answer positions. The order is shuffled with a Fisher-Yates pass each time a quiz starts (see `shuffle` and `startRun` in `logic.js`).

This shuffle capability is exactly what the training reverse-engineers into the Trivia Quiz: `/compare` surfaces it as an adoption candidate, the adoption report becomes a plan, and `/implement` builds the local equivalent. No dependency is added; only the logic is adopted.

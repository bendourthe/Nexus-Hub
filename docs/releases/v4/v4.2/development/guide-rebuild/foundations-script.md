# Foundations scene script (v4.2.2 Phase 3)

**Consumers**: sub-task 3.2 implements exactly these scenes; the render review checks each against this file.
**Constraints (binding, from the design brief)**: scrollytelling scenes, one concept + one animated inline-SVG diagram each; nothing position-fixed or sticky over content; no mode selector or toggle between "raw" and "harnessed" (both are always visible where compared); no chart libraries; both themes from one markup via CSS variables; every animation observer-gated with a complete static equivalent under reduced motion; labels >= 12px effective, scenes stack under 720px.

## Page frame

Eyebrow "Foundations", H1 "What actually happens when an AI edits your code", lead: one paragraph promising the five-minute mental model (model, platform, context, harness) with no marketing. Scenes follow as alternating text/diagram bands (`.fx-scene`, text column and diagram column swap sides each scene; stacked on mobile). A short bridge closes into Training.

## Scene 1 - The model: text in, text out

- **Teaching copy**: A language model does one thing: given everything in the current request, it predicts useful next text. It is very good at that. It also has no hands - it cannot open your files, run your tests, or remember what you did yesterday. On its own it can only talk about your code.
- **Diagram** (`fx-model`): left column of three input chips (Training, Your message, Nothing else), arrows converging into a rounded model node (glow-teal outline, "model" label), output arrow to three text lines of increasing length.
- **Animation**: input chips reveal staggered; arrow paths draw (stroke-dashoffset); output lines grow (scaleX from 0, staggered). One-shot on scene entry.
- **Reduced motion / static state**: everything at final state; no draws.

## Scene 2 - The platform: the loop that gives it hands

- **Teaching copy**: An agent platform - Claude Code, Codex, Cursor, Antigravity, Copilot - wraps that model in a loop. The platform shows the model your repo; the model answers with an action ("read this file", "run the tests", "apply this edit"); the platform executes the action and feeds the result back. Round and round until the task is done. This loop is what people mean by "an agent".
- **Diagram** (`fx-loop`): a circular loop between two nodes: MODEL (left) and YOUR REPO (right, with file/terminal/git glyph chips). Top arc labeled "action", bottom arc labeled "result". A pulse dot travels the full loop continuously.
- **Animation**: arcs draw on entry; pulse dot travels via CSS `offset-path` ONLY while the scene is on screen (`.live` class from the scene observer); labels fade in.
- **Reduced motion / static**: arcs and labels shown, pulse dot hidden.

## Scene 3 - Context: what the model actually sees

- **Teaching copy**: The model sees exactly one thing: the context window - the text the platform packs into this turn. Rules, the task, file excerpts, tool results. Pack it with the right material and the answer lands; pack it with noise and the model confidently edits the wrong file. Choosing what the model sees is context engineering, and it is half the game.
- **Diagram** (`fx-context`): two context windows side by side, always both visible (no toggle). Left window "focused": blocks stack in - Rules, Task, The two files that matter, Failing test output - arrow to a tidy diff card marked with a check. Right window "noisy": blocks - Rules, Task, 40 unrelated files, Old chat scrollback - arrow to a wrong-file card marked with a cross. Identical model chip above both, one label: "same model".
- **Animation**: blocks drop into each window in sequence (translateY + fade, staggered), then the outcome cards pop.
- **Reduced motion / static**: all blocks and outcomes visible.

## Scene 4 - The harness: procedure, not vibes

- **Teaching copy**: Nexus-Hub is a harness around that loop. Skills load written procedures the moment the task matches. Slash commands start the same governed workflow every time. Hooks fire deterministically on tool events - a secret scan blocks the commit whether or not the model "remembered" to be careful. Gates hold the work to a written definition of done. The model still does the thinking; the harness decides how the work is allowed to happen.
- **Diagram** (`fx-harness`): the Scene-2 loop redrawn compact at center; four guardrail arcs snap around it one by one, each with a chip label: Skills (procedures), Commands (entry points), Hooks (tripwires), Gates (definition of done).
- **Animation**: arcs draw in sequence (stroke-dashoffset, staggered), chips fade up after their arc.
- **Reduced motion / static**: all four arcs and chips shown.

## Scene 5 - One task, two runs (the composed chart)

- **Teaching copy**: Follow one real task - "fix the failing checkout test" - through both setups. Same model, same repo. The unharnessed run answers in chat and evaporates when the tab closes. The harnessed run loads the testing skill, runs the loop, gets blocked once by the secret-scan hook, passes the gate, and leaves a tested commit plus a written trail. The difference is not intelligence; it is what survives the session.
- **Diagram** (`fx-runs`): two horizontal lanes, both always visible, sharing one start node ("fix the failing test"). Top lane RAW: prompt -> model -> chat answer (bubble drawn with a dashed outline that fades to 30% opacity and stays faded, labeled "gone at tab close"). Bottom lane WITH NEXUS-HUB: /test -> skill loads -> loop runs -> hook blocks secret (small red tick that turns green) -> gate check -> artifact card (solid document icon, labeled "on disk, in git"). Pulse dots run along both lanes while on screen.
- **Animation**: lane paths draw on entry; pulses travel while `.live`; the chat bubble's fade and the artifact's settle are one-shot on entry.
- **Reduced motion / static**: both lanes complete; bubble already faded, artifact solid; no pulses.

## Bridge - See it run

- One short band: "That is the whole mental model. Training runs this loop for real on a small app with real bugs - you press the keys." Buttons: Open Training (primary, `data-go="training"`), Open Cheatsheets.

## Implementation notes

- Scene containers reuse `.reveal` for entry; a second observer toggles `.live` on scenes for continuous motion (pulses) so nothing animates off screen.
- All diagram colors come from theme tokens (`--accent`, `--ink-dim`, `--border`, `--green`, `--red`, `--surface`); no hardcoded dark-only fills.
- SVG text uses the sans stack at >= 12px effective; under 720px the scene grid stacks text above diagram; under 420px diagrams keep a 320px min drawing width inside an `overflow-x` scroll wrapper only if needed (prefer viewBox scaling).
- No element in the page uses `position: fixed`, and the only `position: sticky` in the file stays the site header.

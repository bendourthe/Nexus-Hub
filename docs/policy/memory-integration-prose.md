# Persistent agent memory

At the start of every session, before other tool work, read persistent agent memory:

`python -m nexus_memory read`

Record a lasting fact, decision, or event as you work. Do not record chatter, and do not let a spawned subagent write:

`python -m nexus_memory record --text "..." --source "..."`

If record prints a merge request, summarize the supplied content, keep what has lasting effect, invent nothing, and run the printed return command. Merges are one at a time. Nothing runs in a background process. If a child summary is missing or blank, run the printed recovery command; do not fabricate.

Search with `python -m nexus_memory search --pattern REGEX`. Open a summarized range with `python -m nexus_memory zoom --lo LO --hi HI`. Discard a bad summary with `python -m nexus_memory drop --lo LO --hi HI`.

Spawned subagents must be told: Do not write to persistent agent memory. You are a spawned subagent; only the parent session may record memory.

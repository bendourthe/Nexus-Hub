---
name: youtube-transcript
description: "Fetch a YouTube video transcript locally with yt-dlp; save clean text. Use for: transcript of a YouTube URL, pull the captions, download the subtitles. SKIP: speech-to-text on local files, downloading the video, summarizing a transcript you have."
summary_l0: "Fetch a YouTube video transcript locally via yt-dlp and save clean text"
overview_l1: "This skill fetches a YouTube video's publicly-available captions locally with the yt-dlp command-line tool, flattens them to clean raw text, and saves a .txt file into the current project (or ~/Downloads when there is no project). Use it when the user hands you a YouTube URL and wants the words: the transcript, the captions, or what the video says. It runs entirely on the user's machine: no paid API, no API key, and no query text leaves the machine beyond yt-dlp's own request to YouTube. yt-dlp is lazy-checked, never auto-installed, and is not a Nexus-Hub dependency. The skill fetches only public captions in accordance with YouTube's Terms of Service and stops on bot-flagging rather than retrying in a loop. It does not transcribe audio with a speech-to-text model, and it does not download the video."
version: 1.0.0
author: Benjamin Dourthe
category: Research
language: Multi-language
tags: [youtube, transcript, captions, subtitles, research, local-only]
tools_required: [Bash, Read, Write]
---

# YouTube Transcript

Fetch a YouTube video's publicly-available captions with the local `yt-dlp` tool, flatten them to clean text, and save a `.txt` file. Everything runs on the user's machine: there is no paid transcript API, no API key, and no third-party intermediary. `yt-dlp` makes the one request to YouTube; nothing else leaves the machine.

## When to Use This Skill

Use this skill when:

- The user gives you a YouTube URL and wants the words in it (the transcript, the captions, or "what does this video say").
- You need a video's spoken content as text to quote, search, summarize, or feed into another step.

**Trigger phrases**: "get the transcript of this video", "transcript of this YouTube URL", "pull the captions", "download the subtitles", "what does this YouTube video say".

**When NOT to use**:

- The user wants speech-to-text on a local audio or video file - that is a different, heavier operation (a transcription model), not caption download.
- The user wants the video file itself downloaded - this skill fetches captions only.
- The user already has the transcript and wants it summarized or rewritten - use a writing or summarization skill for that.

## Instructions

The path below is local-only and uses `yt-dlp`. There is no remote-API alternative in this skill.

### Step 1: Decide the save location and filename

- **Location**: save into the current project or working directory when there is one; otherwise save into `~/Downloads`.
- **Filename**: derive `Channel_Title` (the channel name with spaces replaced by underscores and filesystem-unsafe characters stripped). If channel metadata is unavailable, fall back to the video id.

### Step 2: Confirm yt-dlp is available

Check that `yt-dlp` is on PATH before doing anything else:

```bash
command -v yt-dlp
```

If it is absent, do NOT install it silently. Tell the user this skill needs `yt-dlp` and give the install hint, then stop:

```bash
pipx install yt-dlp   # or: pip install yt-dlp
```

### Step 3: Fetch the metadata for the filename

```bash
yt-dlp --print "%(channel)s|%(title)s" --skip-download "<URL>"
```

If `channel` is null, fall back in order: `channel` -> `uploader` -> `uploader_id`. Build `<NAME>` from the resolved channel per Step 1.

### Step 4: Download the captions only (json3)

```bash
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "en.*" --sub-format json3 -o "<OUT>/<NAME>.%(ext)s" "<URL>"
```

- `--write-subs` prefers manual (human) captions; `--write-auto-subs` falls back to auto-generated captions.
- Use `json3`, NOT `vtt` or `srt`: auto-generated VTT duplicates every line (rolling captions), so json3 is the only clean source.
- For a non-English or unknown-language video, list the available caption tracks first, then set `--sub-langs` accordingly:

```bash
yt-dlp --list-subs "<URL>"
```

### Step 5: Flatten the json3 file to clean text

Run the bundled flattening script, passing the output directory. It finds the `*.json3` file there, concatenates the caption fragments, unescapes HTML entities, collapses whitespace, and writes a sibling `.txt`:

```bash
python scripts/flatten_captions.py "<OUT>"
```

### Step 6: Report the result

Report the saved `.txt` path. When the transcript is short, print its text inline so the user sees it immediately.

## Caveat: public captions, Terms of Service, and bot-flagging

This block is required, not optional.

- **Public captions only.** Fetch only publicly-available captions, and use them in accordance with YouTube's Terms of Service.
- **Stop on bot-flagging.** On an HTTP 429 response, or a "Sign in to confirm you're not a bot" message, the local IP has been flagged. STOP and report it to the user. Do NOT retry in a loop - retrying deepens the flag and makes it worse.
- **One self-update retry is the ceiling.** A single `yt-dlp -U` self-update followed by one retry is acceptable (a stale binary is a common cause). After that, stop.
- **Never silently switch to audio.** Do not fall back to downloading the audio and transcribing it with a speech-to-text model unless the user explicitly asks for that.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I should just retry the 429 a few times until it works." | Retry loops deepen the IP flag; each retry makes the block worse, not better. Stop after at most one `yt-dlp -U` self-update and one retry, then report the bot-flag to the user. |
| "I'll just grab the audio and transcribe it instead." | That is a different, heavier operation (a speech-to-text model over a downloaded media file) that the user did not ask for. Do it only on an explicit request, never as a silent fallback. |
| "I'll download the VTT captions, they are simpler to parse." | Auto-generated VTT duplicates every line because captions roll, so the output is garbled. Use `--sub-format json3` and the bundled flattener, which produces clean, de-duplicated text. |
| "yt-dlp is missing, I'll just pip-install it quietly." | Installing software silently on the user's machine is a surprise side effect. Surface the missing dependency with the install hint and let the user decide. |

## Verification

- [ ] `yt-dlp` presence was checked with `command -v yt-dlp` before any download was attempted.
- [ ] Captions were downloaded with `--sub-format json3` (not vtt or srt).
- [ ] A clean `.txt` transcript file exists at the reported save path.
- [ ] The saved path was reported to the user (and printed inline when short).
- [ ] On any HTTP 429 or bot-confirmation response, the run STOPPED and reported rather than looping retries.
- [ ] No paid API, API key, or secret file was used; the only outbound request was yt-dlp's fetch to YouTube.

## Related Skills

- [[trend-research]] -- researching what is being said across sources; a video transcript is one input to that.
- [[local-docs-lookup]] -- the same local-first, no-third-party-service posture applied to library documentation.

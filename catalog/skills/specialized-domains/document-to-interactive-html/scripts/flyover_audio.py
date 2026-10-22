#!/usr/bin/env python3
"""Lay a music track under the fly-over so its hit lands on the card landing (9.97s).

  analyze TRACK [--hit 9.97]                       candidate hits, the recommended offset, and the
                                                   static gain for about -14 LUFS (true peak <= -1 dB)
  mux VIDEO TRACK OUT --offset S --gain-db G       the aligned, leveled track muxed under the video

A track's strongest "hit" is usually a gap-then-hit: the level falls away for a beat and the band
slams back in. analyze ranks those first, then plain strong onsets. A positive offset starts the
track that many seconds in; a negative one delays it. The video stream is copied untouched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flyover_common as fc  # noqa: E402

TARGET_LUFS = -14.0
PEAK_CEILING = -1.0
SR = 22050


def demuxer_for(track: Path) -> str:
    try:
        return fc.AUDIO_DEMUXERS[track.suffix.lower()]
    except KeyError:
        raise SystemExit(f"unsupported audio type {track.suffix}; use one of {sorted(fc.AUDIO_DEMUXERS)}") from None


def audio_input(track: Path, offset: float = 0.0) -> list[str]:
    seek = ["-ss", f"{offset:.3f}"] if offset > 0 else []
    return [*seek, "-protocol_whitelist", "file,pipe", "-f", demuxer_for(track), "-i", fc.ffmpeg_input(track)]


def offset_for(hit: float, target: float) -> float:
    """Seconds into the track at film time 0 so a hit at `hit` lands on `target`."""
    return round(hit - target, 3)


def gain_for(integrated_lufs: float, true_peak_db: float) -> float:
    """Static gain that reaches the loudness target without pushing the true peak above the ceiling."""
    return round(min(TARGET_LUFS - integrated_lufs, PEAK_CEILING - true_peak_db), 1)


def _decode(ffmpeg: str, track: Path):
    import numpy as np  # noqa: PLC0415 - lazy

    res = __import__("subprocess").run(
        [*fc.ffmpeg_base(ffmpeg), *audio_input(track), "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"],
        capture_output=True, timeout=120, shell=False)
    if res.returncode:
        raise SystemExit("could not decode the track: " + res.stderr.decode("utf-8", "replace")[-400:])
    return np.frombuffer(res.stdout, dtype=np.float32)


def candidates(x, sr: int = SR) -> list[dict]:
    """Gap-then-hit moments (ranked by gap depth), then the strongest plain onsets."""
    import numpy as np  # noqa: PLC0415 - lazy

    hop = int(0.005 * sr)
    n = len(x) // hop
    level = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9)
    body = np.median(level[level > level.max() - 40]) if n else 0.0
    gap_level = body - 15  # a musical "stop" sits well under the body of the track, not at silence
    found, i = [], 0
    while i < n:
        if level[i] < gap_level:
            j = i
            while j < n and level[j] < gap_level:
                j += 1
            gap = (j - i) * 0.005
            lo = i + int(np.argmin(level[i:j]))
            floor = level[lo]
            # attack: first frame from the gap's deepest point that climbs 15 dB above it
            k = next((m for m in range(lo, min(n, j + 24)) if level[m] > floor + 15), None)
            if 0.08 <= gap <= 0.6 and k is not None and level[k:k + 24].max() > body - 6:
                found.append({"kind": "gap-then-hit", "hit": round(k * 0.005, 3), "gap_start": round(i * 0.005, 3),
                              "depth_db": round(float(body - floor), 1)})
            i = j
        i += 1
    found.sort(key=lambda c: -c["depth_db"])
    rise = np.diff(level, prepend=level[0])
    peaks = [m for m in range(10, n - 10) if rise[m] == rise[m - 10: m + 11].max() and rise[m] > 8]
    peaks.sort(key=lambda m: -rise[m])
    found += [{"kind": "onset", "hit": round(m * 0.005, 3), "rise_db": round(float(rise[m]), 1)} for m in peaks[:6]]
    return found


def loudness(ffmpeg: str, track: Path, offset: float, duration: float) -> tuple[float, float]:
    res = fc.run_ffmpeg([fc.ffmpeg_base(ffmpeg)[0], "-hide_banner", "-nostdin", *audio_input(track, offset),
                         "-t", str(duration), "-af", "ebur128=peak=true", "-f", "null", "-"], timeout=120)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", res.stderr)
    p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", res.stderr)
    return float(i[-1]), float(p[-1]) if p and p[-1] != "-inf" else -99.0


def cmd_analyze(track: Path, hit_target: float, ffmpeg_path: str | None) -> int:
    ffmpeg = fc.find_ffmpeg(ffmpeg_path)
    x = _decode(ffmpeg, track)
    dur = len(x) / SR
    cands = candidates(x)
    usable = [c for c in cands if -2.0 <= offset_for(c["hit"], hit_target) <= dur - 4]
    if not usable:
        print(json.dumps({"duration": dur, "candidates": cands, "recommended": None}, indent=1))
        return 1
    best = usable[0]
    off = offset_for(best["hit"], hit_target)
    lufs, peak = loudness(ffmpeg, track, max(0.0, off), fc.DURATION)
    plan = {
        "duration": round(dur, 3), "recommended": best, "offset": off,
        "film_end_in_track": round(off + fc.DURATION, 3), "track_long_enough": off + fc.DURATION <= dur,
        "excerpt_lufs": lufs, "excerpt_true_peak_db": peak, "gain_db": gain_for(lufs, peak),
        "candidates": cands[:10],
    }
    print(json.dumps(plan, indent=1))
    return 0


def cmd_mux(video: Path, track: Path, out: Path, offset: float, gain_db: float, fade_out: float, ffmpeg_path: str | None) -> int:
    ffmpeg = fc.find_ffmpeg(ffmpeg_path)
    delay = f"adelay=delays={int(-offset * 1000)}:all=1," if offset < 0 else ""
    chain = (f"{delay}volume={gain_db}dB,afade=t=in:st=0:d=0.02,"
             f"afade=t=out:st={fc.DURATION - fade_out}:d={fade_out},aresample=48000")
    tmp = out.with_name(out.stem + ".partial" + out.suffix)
    res = fc.run_ffmpeg([
        *fc.ffmpeg_base(ffmpeg), "-protocol_whitelist", "file,pipe", "-i", fc.ffmpeg_input(video), *audio_input(track, offset),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", chain, "-c:a", "aac", "-b:a", "256k", "-ac", "2",
        "-t", str(fc.DURATION), "-movflags", "+faststart", fc.ffmpeg_input(tmp)], timeout=300)
    if res.returncode:
        tmp.unlink(missing_ok=True)
        raise SystemExit("mux failed: " + res.stderr[-600:])
    tmp.replace(out)
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    an = sub.add_parser("analyze")
    an.add_argument("track", type=Path)
    an.add_argument("--hit", type=float, default=9.97)
    an.add_argument("--ffmpeg")
    mx = sub.add_parser("mux")
    mx.add_argument("video", type=Path)
    mx.add_argument("track", type=Path)
    mx.add_argument("out", type=Path)
    mx.add_argument("--offset", type=float, required=True)
    mx.add_argument("--gain-db", type=float, required=True)
    mx.add_argument("--fade-out", type=float, default=0.5)
    mx.add_argument("--ffmpeg")
    a = ap.parse_args(argv)
    if a.cmd == "analyze":
        return cmd_analyze(a.track, a.hit, a.ffmpeg)
    return cmd_mux(a.video, a.track, a.out, a.offset, a.gain_db, a.fade_out, a.ffmpeg)


if __name__ == "__main__":
    sys.exit(main())

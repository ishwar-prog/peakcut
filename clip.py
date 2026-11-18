"""PeakCut CLI: Cut long videos and streams into vertical captioned clips directly from the terminal.

Usage:
    python clip.py <video_url_or_file> [options]

Examples:
    python clip.py "https://www.youtube.com/watch?v=..." --clips 3
    python clip.py sample.mp4 --style bounce --layout blur --out ./my_clips
    python clip.py sample.mp4 --json
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Ensure project root is in python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from studio import auth, config, ctx, jobs, media, render, tools


def main():
    parser = argparse.ArgumentParser(
        description="PeakCut CLI: Turn long videos into vertical captioned clips automatically."
    )
    parser.add_argument("source", help="Path to local video file OR URL (YouTube, Twitch, Kick)")
    parser.add_argument("--clips", "-c", type=int, default=3, help="Max clips to generate (default: 3)")
    parser.add_argument("--min-len", type=int, default=15, help="Min clip duration in seconds (default: 15)")
    parser.add_argument("--max-len", type=int, default=60, help="Max clip duration in seconds (default: 60)")
    parser.add_argument("--style", choices=["bounce", "clean", "box"], default="bounce", help="Caption style (default: bounce)")
    parser.add_argument("--layout", choices=["blur", "fill", "split"], default="blur", help="Layout style (default: blur)")
    parser.add_argument("--no-captions", action="store_true", help="Disable captions on clips")
    parser.add_argument("--out", "-o", default="./clips", help="Output directory for generated clips (default: ./clips)")
    parser.add_argument("--ai-key", help="AI API key (or set PEAKCUT_AI_KEY env var). If not set, clips by audio loudness.")
    parser.add_argument("--ai-provider", help="AI provider (gemini, openai, anthropic, groq, openrouter, ollama, custom)")
    parser.add_argument("--ai-model", help="AI model name (e.g. gemini-2.5-flash, gpt-4o-mini)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON for AI agents and scripts")

    args = parser.parse_args()

    # Verify ffmpeg
    missing = tools.setup()
    if missing:
        err = f"Error: PeakCut requires ffmpeg and ffprobe. Missing: {', '.join(missing)}.\n{tools.HELP}"
        if args.json:
            print(json.dumps({"status": "error", "message": err}))
        else:
            print(err, file=sys.stderr)
        sys.exit(1)

    if args.ai_key:
        os.environ["PEAKCUT_AI_KEY"] = args.ai_key
    if args.ai_provider:
        os.environ["PEAKCUT_AI_PROVIDER"] = args.ai_provider
    if args.ai_model:
        os.environ["PEAKCUT_AI_MODELS"] = args.ai_model

    user = auth.local_user()
    ctx.set_uid(user.id)

    src_str = args.source.strip()
    is_url = src_str.startswith("http://") or src_str.startswith("https://")

    if is_url:
        src = {"type": "url", "url": src_str, "name": src_str}
    else:
        src_path = Path(src_str).resolve()
        if not src_path.is_file():
            err = f"Error: Video file not found: {src_path}"
            if args.json:
                print(json.dumps({"status": "error", "message": err}))
            else:
                print(err, file=sys.stderr)
            sys.exit(1)
        src = {"type": "upload", "path": str(src_path), "name": src_path.name}

    options = {
        "max_clips": args.clips,
        "min_len": args.min_len,
        "max_len": args.max_len,
        "style": args.style,
        "layout": args.layout,
        "captions": not args.no_captions,
    }

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.json:
        print("=" * 60)
        print(" PeakCut CLI - Vertical Clip Generator")
        print("=" * 60)
        print(f" Source:      {src['name']}")
        print(f" Max clips:   {args.clips}")
        print(f" Style:       {args.style} | Layout: {args.layout} | Captions: {'Off' if args.no_captions else 'On'}")
        print(f" AI Provider: {os.environ.get('PEAKCUT_AI_PROVIDER', 'gemini')} (Key: {'Set' if os.environ.get('PEAKCUT_AI_KEY') else 'None (using loudness)'})")
        print(f" Output dir:  {out_dir}")
        print("-" * 60)

    job = jobs.create(src, options, enqueue=False)
    job_d = Path(job["dir"])

    last_stage = None
    import threading

    stop_monitor = threading.Event()

    def progress_logger():
        nonlocal last_stage
        while not stop_monitor.wait(1.5):
            cur = job.get("stage")
            prog = job.get("progress", 0.0)
            if cur and cur != last_stage:
                last_stage = cur
                if not args.json:
                    print(f"[*] {cur} ({int(prog * 100)}%)")

    t = threading.Thread(target=progress_logger, daemon=True)
    t.start()

    try:
        jobs._run_job(job)
    except Exception as e:
        stop_monitor.set()
        t.join(timeout=1.0)
        if args.json:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            print(f"\n[!] Job failed: {e}", file=sys.stderr)
        sys.exit(1)

    stop_monitor.set()
    t.join(timeout=1.0)

    # Collect rendered clips
    clips_dir = job_d / "clips"
    output_clips = []

    for i, c in enumerate(job.get("clips", []), 1):
        cid = c.get("id", f"clip{i:02d}")
        src_clip = clips_dir / f"{cid}.mp4"
        if src_clip.is_file():
            # Clean title for filename
            title = c.get("title", f"clip_{i}")
            safe_title = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in title).strip("_")
            dst_name = f"{i:02d}_{safe_title}.mp4" if safe_title else f"{cid}.mp4"
            dst_clip = out_dir / dst_name
            shutil.copyfile(src_clip, dst_clip)

            # Copy cover image if available
            src_cover = clips_dir / f"{cid}.jpg"
            cover_path = None
            if src_cover.is_file():
                dst_cover = out_dir / f"{dst_name[:-4]}.jpg"
                shutil.copyfile(src_cover, dst_cover)
                cover_path = str(dst_cover)

            output_clips.append({
                "index": i,
                "id": cid,
                "title": c.get("title", ""),
                "hook": c.get("hook", ""),
                "start": c.get("start", 0),
                "end": c.get("end", 0),
                "duration": round(c.get("end", 0) - c.get("start", 0), 2),
                "video_path": str(dst_clip),
                "cover_path": cover_path
            })

    result = {
        "status": "success",
        "job_id": job.get("id"),
        "title": job.get("title"),
        "duration": job.get("duration"),
        "clips_count": len(output_clips),
        "ai_used": bool(job.get("ai", {}).get("model")),
        "clips": output_clips,
        "output_directory": str(out_dir)
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("-" * 60)
        print(f"[✓] Completed! Generated {len(output_clips)} clip(s):")
        for clip in output_clips:
            print(f"\n  Clip #{clip['index']}: {clip['title']}")
            if clip['hook']:
                print(f"    Hook:     \"{clip['hook']}\"")
            print(f"    Time:     {clip['start']}s -> {clip['end']}s ({clip['duration']}s)")
            print(f"    File:     {clip['video_path']}")
        print(f"\nAll clips saved to: {out_dir}")
        print("=" * 60)


if __name__ == "__main__":
    main()

# Working on PeakCut (AI Agent Instructions)

A comprehensive guide for AI coding assistants (Qoder, Arena.ai, Cursor, Devin, Claude Code, Codex, Antigravity) and contributors.

---

## ⚡ Quick Start for AI Agents

When dropped into a new environment (container, sandbox, or local machine), run the setup script:

```bash
# On Linux/macOS or cloud AI sandboxes (Arena.ai, Codespaces, Docker):
bash setup.sh

# On Windows:
setup.bat
```

This automatically:
1. Installs `ffmpeg` and required multimedia libraries if missing.
2. Sets up Python 3.10-3.12 and installs dependencies from `requirements.txt`.
3. Pre-downloads the offline speech-to-text model (~480 MB).

---

## 🎬 How to Generate Clips

PeakCut provides two interfaces: **CLI** (ideal for autonomous AI agents and scripts) and **Web Studio** (for human users).

### 1. Headless / CLI Execution (`clip.py`)
AI agents in headless environments (like Qoder or Arena.ai) should use `clip.py` to create clips directly:

```bash
# Clip a YouTube, Twitch, or Kick URL
python clip.py "https://www.youtube.com/watch?v=VIDEO_ID" --clips 3 --out ./clips

# Clip a local video file
python clip.py path/to/video.mp4 --style bounce --layout blur --out ./clips

# Output JSON for programmatic parsing by AI agents:
python clip.py path/to/video.mp4 --json
```

**JSON Output Format:**
```json
{
  "status": "success",
  "job_id": "20261118-...",
  "title": "Video Title",
  "duration": 340.5,
  "clips_count": 3,
  "ai_used": true,
  "clips": [
    {
      "index": 1,
      "id": "clip01",
      "title": "Unbelievable moment",
      "hook": "Wait till the end...",
      "start": 12.4,
      "end": 45.2,
      "duration": 32.8,
      "video_path": "/workspace/clips/01_Unbelievable_moment.mp4",
      "cover_path": "/workspace/clips/01_Unbelievable_moment.jpg"
    }
  ],
  "output_directory": "/workspace/clips"
}
```

### 2. Web UI Execution
```bash
python -m studio.server
# Dashboard opens on http://127.0.0.1:8765
```

---

## 🔑 AI Key Configuration (BYOK & Fallback)

- **Zero-Config Fallback:** PeakCut functions **100% out of the box without any API keys**. If no AI key is provided, it automatically detects engaging highlights using audio loudness and speech density.
- **AI-Powered Selection:** To use LLM-driven highlight selection, hook generation, and smart titles, configure environment variables:
  ```bash
  export PEAKCUT_AI_PROVIDER=gemini        # gemini, openai, anthropic, groq, openrouter, ollama, custom
  export PEAKCUT_AI_KEY="your-api-key"
  export PEAKCUT_AI_MODELS="gemini-2.5-flash"
  ```
  Or pass `--ai-key "..." --ai-provider gemini` directly to `clip.py`.

---

## 🧪 Tests

Run the full automated test suite without external dependencies or keys:
```bash
python tests/run.py
```
This boots an isolated instance on a temporary port, verifies permissions, upload chunking, caption geometry, loudness calculation, and queue handling, then cleans up.

---

## 📂 Project Architecture

| File / Folder | Role |
|---|---|
| `clip.py` | CLI entry point for AI agents and headless environments |
| `setup.sh` / `setup.bat` | Universal one-step environment bootstrappers |
| `studio/server.py` | FastAPI server routes, middleware, and health endpoints |
| `studio/jobs.py` | Video pipeline: download -> audio extract -> transcribe -> AI picks -> render |
| `studio/render.py` | 9:16 vertical formatting, caption overlays (ASS subtitles), ffmpeg render |
| `studio/brain.py` | LLM prompts for clip scoring, hook generation, and title creation |
| `studio/transcribe.py` | Local offline speech-to-text using `sherpa-onnx` and Parakeet model |
| `studio/media.py` | Video downloading (`yt-dlp`), audio normalization, loudness analysis |
| `studio/tools.py` | Auto-discovery for `ffmpeg` and `ffprobe` binaries |
| `web/` | Vanilla HTML5/CSS/JS frontend dashboard (no node_modules build step required) |

---

## ⚠️ Key Environment Constraints

1. **Path Lengths on Windows:** Keep workspace paths reasonably short. Windows has a 260-character MAX_PATH limit that can affect ffmpeg temporary caption render files if nested excessively.
2. **Python Compatibility:** Python 3.10 to 3.12 is strongly recommended for pre-built binary wheels of `numpy`, `sherpa-onnx`, and `soundfile`.
3. **FFmpeg:** Required. Automatically located by `studio/tools.py` in standard system paths, WinGet packages, Scoop shims, and Homebrew directories.

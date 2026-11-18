#!/usr/bin/env bash
# PeakCut universal setup script for Linux and macOS environments (Codespaces, Arena.ai, Qoder, etc.)
set -e

echo "==================================================="
echo " Setting up PeakCut Environment"
echo "==================================================="

# 1. Install ffmpeg if missing
if ! command -v ffmpeg &> /dev/null; then
    echo "--> Installing ffmpeg..."
    if command -v apt-get &> /dev/null; then
        if [ "$EUID" -eq 0 ]; then
            apt-get update && apt-get install -y ffmpeg libsndfile1 ca-certificates
        else
            sudo apt-get update && sudo apt-get install -y ffmpeg libsndfile1 ca-certificates
        fi
    elif command -v brew &> /dev/null; then
        brew install ffmpeg libsndfile
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y ffmpeg libsndfile
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm ffmpeg libsndfile
    elif command -v apk &> /dev/null; then
        apk add ffmpeg libsndfile
    else
        echo "Warning: ffmpeg not found. Please install ffmpeg for video processing."
    fi
else
    echo "[✓] ffmpeg is already installed"
fi

# 2. Setup Python environment
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PY_VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || true)
        MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || true)
        if [ "$MAJOR" = "3" ] && [ "$MINOR" -ge 10 ] && [ "$MINOR" -le 13 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "--> System Python is outside recommended range (3.10-3.13). Setting up uv..."
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    uv python install 3.12
    uv venv .venv --python 3.12 --clear
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    echo "[✓] Using Python: $PYTHON_CMD ($PY_VER)"
    if [ ! -d ".venv" ]; then
        "$PYTHON_CMD" -m venv .venv
    fi
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# 3. Pre-fetch offline speech transcription model
echo "--> Checking speech recognition model..."
python -m studio.fetch_model

echo "==================================================="
echo " [✓] PeakCut is ready!"
echo " - Generate clips via CLI:"
echo "     python clip.py <video_url_or_file> --clips 3"
echo " - Start Web Studio:"
echo "     python -m studio.server"
echo "==================================================="

#!/usr/bin/env bash
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
echo "Starting PeakCut Studio on http://127.0.0.1:8765"
python -m studio.server

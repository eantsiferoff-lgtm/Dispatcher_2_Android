#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env || true
echo
printf '%s\n' 'Next:' '1) Put COMPOSIO_API_KEY and OPENAI_API_KEY into .env' '2) Run: python app.py' '3) Type: mcp' '4) For the full agent: python openai_agent.py'

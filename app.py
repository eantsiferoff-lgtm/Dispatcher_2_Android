import os
from pathlib import Path
from dotenv import load_dotenv
from core.runtime import Runtime
from core.composio_gateway import ComposioGateway

load_dotenv()
ROOT = Path(__file__).resolve().parent

def main():
    runtime = Runtime(ROOT)
    print('Dispatcher 2.0 — working runtime')
    print("Commands: 'plan <text>', 'connect gmail', 'mcp', 'exit'")
    while True:
        raw = input('\n> ').strip()
        if raw.lower() == 'exit': break
        if raw.lower() == 'mcp':
            info = ComposioGateway().mcp_endpoint()
            print('MCP URL:', info['url'])
            print('Session:', info['session_id'])
            continue
        if raw.lower().startswith('connect '):
            toolkit = raw.split(None, 1)[1]
            print(ComposioGateway().authorize(toolkit)['redirect_url'])
            continue
        request = raw[5:].strip() if raw.lower().startswith('plan ') else raw
        _, plan, task = runtime.prepare(request)
        print({"request": request, "skills": plan.skills, "steps": plan.steps, "task_id": task.task_id})

if __name__ == '__main__': main()

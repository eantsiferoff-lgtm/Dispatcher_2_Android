# Dispatcher 2.0 — working Composio integration

A modular personal AI dispatcher: **request → registry → skills → Composio → external apps**.

Composio Sessions are the integration boundary. A session is scoped to `DISPATCHER_USER_ID`, can discover tools dynamically, and can expose the same session through a hosted MCP endpoint. Current Composio docs recommend Sessions over the legacy standalone MCP-server API.

## 1. Install

```bash
./setup.sh
```

Then edit `.env`:

```text
COMPOSIO_API_KEY=...
OPENAI_API_KEY=...
DISPATCHER_USER_ID=user_001
OPENAI_MODEL=gpt-5.6
```

## 2. Test routing without external services

```bash
python app.py
```

Examples:

```text
plan Проанализируй голубые фишки и сделай портфель
plan Распознай счет-фактуру для УТ 8.3
plan Подготовь грантовую заявку из документов
```

## 3. Connect Gmail

```bash
python connect.py gmail
```

Open the returned URL and complete OAuth. The connection is stored against the stable dispatcher user ID.

## 4. Start the agent

```bash
python openai_agent.py
```

The agent receives the Composio session tools and can discover and execute app tools. Keep consequential actions behind an explicit confirmation gate.

## 5. MCP

```text
python app.py
mcp
```

The command creates a Composio Session with `mcp=True` and prints its hosted MCP endpoint. Use that endpoint with an MCP-compatible client.

## Architecture

```text
User
  ↓
Master Dispatcher
  ↓
Skill Registry + Routing
  ↓
One or more domain Skills
  ↓
Tool/Approval boundary
  ↓
Composio Session
  ↓
Gmail / Drive / GitHub / Slack / ...
```

New skills are added under `skills/<skill-id>/SKILL.md` and registered in `registry.yaml`; the dispatcher core does not need to be rewritten.

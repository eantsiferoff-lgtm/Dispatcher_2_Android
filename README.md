# Dispatcher 2.0 — working Composio integration

A modular personal AI dispatcher: **request → registry → planner → plan/DAG → executor → backend → result**.

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
User request
  ↓
Master Dispatcher
  ↓
Skill Registry
  ↓
Planner
  ↓
Plan / DAG
  ↓
Executor + Execution Router
  ↓
Backend selected for the Skill
  ├── LocalBackend
  ├── OpenAIBackend
  ├── ComposioBackend
  └── N8NBackend
  ↓
Result
```

Skills are discovered dynamically from `skills/<skill-id>/SKILL.md`. A new domain Skill can be added without rewriting the dispatcher core. Skill metadata defines capabilities, triggers, lifecycle information, and execution configuration.

## Workspace and lifecycle rules

### Skill lifecycle

Skills follow the lifecycle:

```text
ACTIVE → DORMANT → ARCHIVED
             ↓
          DELETED

- `ACTIVE` Skills are eligible for planning and execution.
- `DORMANT` and `ARCHIVED` Skills are excluded from the active domain.
- `DELETED` is a terminal lifecycle status for normal eligibility.
- A deleted Skill can be restored through the existing registry/lifecycle mechanism.

### Workspace boundaries

Project files, runtime data, temporary data, and archive data are separate concerns.

```text
TEMP ≠ PROJECT
ARCHIVE ≠ PROJECT
USER DATA ≠ PROJECT


The workspace distinguishes:

- Project — source code and project configuration.
- Runtime Data — dispatcher runtime state and execution data.
- Temporary Data — working data used during task execution.
- Archive — retained historical data.

### Temporary file lifecycle

Temporary data should not be retained by default.

After task completion:

```text
TEMP
 ↓
Task completed
 ↓
needed?
 ├── YES → results / artifacts / projects / archive
 └── NO  → DELETE
```

### Regression rule

Changes to lifecycle or workspace behavior must pass the full test suite before being committed.

The J.6 regression checkpoint passed with:

```text
154 tests — OK
```

from __future__ import annotations

from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request as HTTPRequest
from starlette.responses import JSONResponse
from starlette.routing import Route

from .runtime import Runtime


def create_app(runtime: Runtime) -> Starlette:
    async def create_request(request: HTTPRequest) -> JSONResponse:
        payload: dict[str, Any] = await request.json()

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            return JSONResponse(
                {"error": "text is required"},
                status_code=400,
            )

        attachments = payload.get("attachments") or []
        project_id = payload.get("project_id")

        _, _, task = runtime.prepare(
            text=text,
            attachments=attachments,
            project_id=project_id,
        )

        return JSONResponse(
            {
                "task_id": task.task_id,
                "request_id": task.request_id,
                "status": task.status,
            }
        )

    async def get_task(request: HTTPRequest) -> JSONResponse:
        task_id = request.path_params["task_id"]
        task = runtime.restore_task(task_id)

        if task is None:
            return JSONResponse(
                {"error": "task not found"},
                status_code=404,
            )

        steps = list(task.plan.steps) if task.plan is not None else []
        results = [
            step["result"]
            for step in steps
            if isinstance(step.get("result"), dict)
        ]

        workflow = None
        if task.plan is not None:
            workflow = runtime._select_workflow(
                type(
                    "Decision",
                    (),
                    {"skills": list(task.plan.skills)},
                )()
            )

        return JSONResponse(
            {
                "task_id": task.task_id,
                "request_id": task.request_id,
                "project_id": task.project_id,
                "status": task.status,
                "workflow": workflow,
                "steps": steps,
                "results": results,
                "artifacts": list(task.artifacts),
                "errors": list(task.errors),
                "current_step": task.current_step,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
        )

    async def get_task_trace(request: HTTPRequest) -> JSONResponse:
        task_id = request.path_params["task_id"]
        task = runtime.restore_task(task_id)

        if task is None:
            return JSONResponse(
                {"error": "task not found"},
                status_code=404,
            )

        events = [
            event
            for event in runtime.execution_trace.events()
            if event.get("task_id") in {"", task_id}
        ]

        return JSONResponse({"events": events})

    async def get_skills(request: HTTPRequest) -> JSONResponse:
        skills = runtime.registry.active_domain()

        return JSONResponse(
            {
                "skills": [
                    {
                        "skill_id": skill.skill_id,
                        "name": skill.name,
                        "description": skill.description,
                        "capabilities": list(skill.capabilities),
                        "triggers": list(skill.triggers),
                        "lifecycle_status": skill.lifecycle_status,
                    }
                    for skill in skills
                ]
            }
        )

    async def get_workflows(request: HTTPRequest) -> JSONResponse:
        return JSONResponse(
            {
                "workflows": [
                    {
                        "workflow_id": workflow_id,
                        "steps": list(workflow.get("steps", [])),
                    }
                    for workflow_id, workflow
                    in runtime.config.workflows.items()
                ]
            }
        )

    return Starlette(
        routes=[
            Route("/request", create_request, methods=["POST"]),
            Route("/task/{task_id}/trace", get_task_trace, methods=["GET"]),
            Route("/task/{task_id}", get_task, methods=["GET"]),
            Route("/skills", get_skills, methods=["GET"]),
            Route("/workflows", get_workflows, methods=["GET"]),
        ]
    )

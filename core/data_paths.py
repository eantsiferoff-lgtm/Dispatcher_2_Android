from __future__ import annotations
from pathlib import Path


class DataPaths:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.state = self.root / "state"
        self.requests = self.root / "requests"
        self.results = self.root / "results"
        self.traces = self.root / "traces"
        self.artifacts = self.root / "artifacts"
        self.projects = self.root / "projects"
        self.archive = self.root / "archive"
        self.archive_skills = self.archive / "skills"
        self.archive_requests = self.archive / "requests"

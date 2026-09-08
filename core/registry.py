from pathlib import Path
import yaml

class SkillRegistry:
    def __init__(self, registry_path: str):
        self.path = Path(registry_path)
        self.data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.skills = {s["id"]: s for s in self.data.get("skills", [])}

    def all(self):
        return list(self.skills.values())

    def get(self, skill_id):
        return self.skills.get(skill_id)

    def load_instructions(self, skill_id):
        skill = self.get(skill_id)
        if not skill:
            raise KeyError(f"Unknown skill: {skill_id}")
        path = self.path.parent / skill["path"]
        return path.read_text(encoding="utf-8")

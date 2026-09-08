from pathlib import Path

class SkillLoader:
    def __init__(self, root: Path):
        self.root = Path(root)

    def load(self, skill_id: str) -> str:
        skill = self.root / 'skills' / skill_id / 'SKILL.md'
        if not skill.exists():
            raise FileNotFoundError(f'Skill not found: {skill_id}')
        return skill.read_text(encoding='utf-8')

    def load_many(self, skill_ids):
        return {sid: self.load(sid) for sid in skill_ids}

from pathlib import Path
import yaml
from .skill_loader import SkillLoader

class Dispatcher:
    def __init__(self, root: str):
        self.root = Path(root)
        self.registry = yaml.safe_load((self.root / 'registry.yaml').read_text(encoding='utf-8'))
        self.routing = yaml.safe_load((self.root / 'routing.yaml').read_text(encoding='utf-8'))
        self.skills = {x['id']: x for x in self.registry.get('skills', [])}
        self.loader = SkillLoader(self.root)

    def _normalize(self, text: str):
        text = text.lower().replace("ё", "е")
        for suffix in ("ами", "ями", "ого", "ему", "ому", "ыми", "ими",
                       "ах", "ях", "ам", "ям", "ом", "ем", "ов", "ев",
                       "ей", "ой", "ий", "ый", "ая", "яя", "ое", "ее",
                       "ые", "ие", "у", "ю", "а", "я", "ы", "и", "о", "е"):
            if len(text) > len(suffix) + 3 and text.endswith(suffix):
                text = text[:-len(suffix)]
                break
        return text

    def classify(self, request: str):
        text = request.lower().replace("ё", "е")
        normalized_text = " ".join(self._normalize(x) for x in text.split())
        scores = {sid: 0 for sid in self.skills}
        for rule in self.routing.get('rules', []):
            if any(self._normalize(term) in normalized_text or term.lower() in text for term in rule.get('when', [])):
                for sid in rule.get('skills', []):
                    scores[sid] = scores.get(sid, 0) + sum((self._normalize(term) in normalized_text) or (term.lower() in text) for term in rule.get('when', []))
        ranked = sorted(scores.items(), key=lambda x: (x[1], self.skills.get(x[0], {}).get('priority', 0)), reverse=True)
        return [sid for sid, score in ranked if score > 0]

    def plan(self, request: str):
        selected = self.classify(request)
        selected_set = set(selected)
        combinations = [c for c in self.routing.get('combinations', []) if set(c.get('match', [])).issubset(selected_set)]
        return {'request': request, 'skills': selected, 'combinations': combinations}

    def build_context(self, request: str):
        plan = self.plan(request)
        instructions = self.loader.load_many(plan['skills']) if plan['skills'] else {}
        return {'plan': plan, 'skill_instructions': instructions}

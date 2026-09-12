from __future__ import annotations

from dataclasses import dataclass, field

from .capability_index import CapabilityIndex
from .skill_registry import SkillRegistry


@dataclass
class PlanCandidate:
    skill_id: str
    score: float
    matched_signals: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class PlannerDecision:
    skills: list[str] = field(default_factory=list)
    candidates: list[PlanCandidate] = field(default_factory=list)
    confidence: float = 0.0


class Planner:
    def __init__(self, registry: SkillRegistry, fallback=None, fallback_threshold: float = 0.20):
        self.registry = registry
        self.index = CapabilityIndex(registry)
        self.fallback = fallback
        self.fallback_threshold = fallback_threshold

    @staticmethod
    def _normalize(text: str) -> str:
        return text.lower().replace("ё", "е")

    @staticmethod
    def _description_words(description: str) -> list[str]:
        normalized = Planner._normalize(description)
        cleaned = normalized
        for char in ".,:;()[]{}\"'":
            cleaned = cleaned.replace(char, " ")

        return [
            word
            for word in cleaned.split()
            if len(word) >= 5
        ]

    def plan(self, request: str) -> PlannerDecision:
        text = self._normalize(request)
        candidates: list[PlanCandidate] = []

        for skill in self.registry.active_domain():
            matched_signals: list[str] = []
            score = 0.0

            for trigger in skill.triggers:
                signal = self._normalize(trigger)

                if signal in text:
                    matched_signals.append(trigger)

                    if len(signal.split()) >= 2:
                        score += 0.50
                    elif signal in {"найди", "рядом", "поблизости"}:
                        score += 0.10
                    else:
                        score += 0.35

            for capability in skill.capabilities:
                parts = self._normalize(capability).split("-")

                if any(part in text for part in parts):
                    matched_signals.append(capability)
                    score += 0.10

            if not matched_signals:
                description_words = self._description_words(
                    skill.description
                )

                description_matches = [
                    word
                    for word in description_words
                    if word in text
                ]

                if len(description_matches) >= 2:
                    unique_matches = list(dict.fromkeys(description_matches))
                    matched_signals.extend(unique_matches[:4])
                    score += min(
                        0.60,
                        len(unique_matches) * 0.15,
                    )

            if not matched_signals:
                continue

            trigger_count = sum(
                1
                for trigger in skill.triggers
                if trigger in matched_signals
            )
            capability_count = len(matched_signals) - trigger_count

            score = min(1.0, score)

            candidates.append(
                PlanCandidate(
                    skill_id=skill.skill_id,
                    score=score,
                    matched_signals=matched_signals,
                    reason=(
                        f"triggers={trigger_count}, "
                        f"capabilities={capability_count}"
                    ),
                )
            )

        candidates.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        skills = [
            candidate.skill_id
            for candidate in candidates
            if candidate.score >= 0.20
        ]

        confidence = (
            candidates[0].score
            if candidates
            else 0.0
        )

        decision = PlannerDecision(
            skills=skills,
            candidates=candidates,
            confidence=confidence,
        )

        if decision.confidence < self.fallback_threshold and self.fallback is not None:
            fallback_skills = self.fallback(request) or []
            allowed = {skill.skill_id for skill in self.registry.active_domain()}
            decision.skills = [skill_id for skill_id in fallback_skills if skill_id in allowed]

        return decision

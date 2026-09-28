"""
VaniSetu — Conversation State Machine
Zero external dependencies (stdlib dataclasses only).
"""
from enum import Enum
from dataclasses import dataclass, field


class Stage(str, Enum):
    GREETING     = "greeting"
    IDENTITY     = "identity"        # name, age, district
    LIVELIHOOD   = "livelihood"      # occupation, experience, skills
    EDUCATION    = "education"       # education level
    PREFERENCES  = "preferences"     # location pref, duration
    RECOMMEND    = "recommendation"  # fetch + speak scores
    CONFIRM      = "confirmation"    # register? yes/no
    END          = "end"


@dataclass
class Profile:
    """Everything extracted from the conversation so far."""
    name: str = ""
    age: int | None = None
    gender: str = ""
    phone: str = ""
    district: str = ""
    state: str = ""

    occupation: str = ""
    years_exp: int | None = None
    sector: str = ""
    skills: list[str] = field(default_factory=list)

    education: str = ""     # below_8th | 8th_pass | 10th_pass | 12th_pass | iti | diploma | graduate
    nsqf_level: int | None = None

    pref_location: str = ""
    pref_duration: str = ""
    language: str = "hi"
    confidence: float = 0.0


@dataclass
class CallState:
    call_id: str = ""
    stage: Stage = Stage.GREETING
    profile: Profile = field(default_factory=Profile)
    history: list[dict] = field(default_factory=list)   # [{role, content}]
    recommendation: dict = field(default_factory=dict)

    # ── helpers ──────────────────────────────────────────────────────────────

    def next_stage(self):
        stages = list(Stage)
        i = stages.index(self.stage)
        if i < len(stages) - 1:
            self.stage = stages[i + 1]

    def identity_done(self) -> bool:
        return bool(self.profile.name and self.profile.district)

    def livelihood_done(self) -> bool:
        return bool(self.profile.occupation and self.profile.skills)

    def ready_for_recommendation(self) -> bool:
        return self.identity_done() and self.livelihood_done() and bool(self.profile.education)

    def recent_history(self, n: int = 6) -> list[dict]:
        """Last n turns to keep token usage low."""
        return self.history[-n:]

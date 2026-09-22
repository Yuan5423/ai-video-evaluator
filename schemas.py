from typing import List
from pydantic import BaseModel, Field

class Scores(BaseModel):
    viewpoint_impact: int = Field(ge=0, le=2)
    user_pain_or_benefit: int = Field(ge=0, le=2)
    beginner_clarity: int = Field(ge=0, le=2)
    editability: int = Field(ge=0, le=2)
    emotion_memory: int = Field(ge=0, le=2)

class Candidate(BaseModel):
    core_viewpoint: str
    viral_score: float = Field(ge=0, le=10)
    scores: Scores
    reason: str
    original_excerpt: str
    recommended_hook: str
    editing_structure: str

class EditingAdvice(BaseModel):
    keep_opening: str
    keep_middle: str
    remove: str
    keep_ending: str
    suggested_duration: str

class Titles(BaseModel):
    pain_point: str
    counterintuitive: str
    result: str

class EvaluationReport(BaseModel):
    overall_summary: str
    worth_editing: bool
    suggested_video_count: int = Field(ge=0, le=20)
    overall_score: float = Field(ge=0, le=10)
    candidates: List[Candidate] = Field(default_factory=list, max_length=3)
    best_hook: str
    editing_advice: EditingAdvice
    titles: Titles

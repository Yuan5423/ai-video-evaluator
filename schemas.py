from typing import List, Literal

from pydantic import BaseModel, Field

class Scores(BaseModel):
    strong_viewpoint: int = Field(ge=0, le=2)
    information_gain: int = Field(ge=0, le=2)
    contrast_value: int = Field(ge=0, le=2)
    standalone_segment: int = Field(ge=0, le=2)
    user_propagation_value: int = Field(ge=0, le=2)

class OpeningRecommendation(BaseModel):
    source_range: str
    original_sentence: str
    reason: str

class ClipPlan(BaseModel):
    opening_excerpt: str
    core_excerpt: str
    ending_excerpt: str
    structure_reason: str

class Candidate(BaseModel):
    source_range: str
    original_excerpt: str
    core_viewpoint: str
    clip_value_score: float = Field(ge=0, le=10)
    reason: str
    independence: Literal["高", "中", "低"]
    value_types: List[str] = Field(default_factory=list, max_length=3)
    suggested_duration: str
    editing_plan: ClipPlan

class EvaluationReport(BaseModel):
    overall_summary: str
    worth_editing: bool
    clip_value_level: Literal["高剪辑价值", "中等剪辑价值", "低剪辑价值", "无明显剪辑价值"]
    suggested_video_count: int = Field(ge=0, le=20)
    overall_score: float = Field(ge=0, le=10)
    overall_scores: Scores
    effective_clip_rate: float = Field(ge=0, le=100)
    best_opening: OpeningRecommendation
    candidates: List[Candidate] = Field(default_factory=list, max_length=3)

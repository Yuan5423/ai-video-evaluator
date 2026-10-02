import os
import json
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from schemas import EvaluationReport

load_dotenv()
PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"

def highlight_key_sentence(excerpt: str) -> str:
    """Ensure every source excerpt has one visually emphasised original sentence."""
    if "**" in excerpt:
        return excerpt
    sentences = [item.strip() for item in re.split(r"(?<=[。！？!?])", excerpt) if item.strip()]
    if not sentences:
        return excerpt
    # Emphasise up to three complete, information-rich sentences without adding UI sections.
    key_sentences = sorted(sentences, key=len, reverse=True)[:3]
    highlighted = excerpt
    for key_sentence in key_sentences:
        highlighted = highlighted.replace(key_sentence, f"**{key_sentence}**", 1)
    return highlighted

def exact_source_quote(quote: str, transcript: str) -> Optional[str]:
    """Return the exact contiguous source text, or None when a quote was altered."""
    quote = quote.replace("**", "")
    compact_quote = "".join(quote.split())
    if not compact_quote:
        return None
    compact_source = "".join(transcript.split())
    start = compact_source.find(compact_quote)
    if start < 0:
        return None
    positions = [index for index, char in enumerate(transcript) if not char.isspace()]
    end = start + len(compact_quote) - 1
    return transcript[positions[start]:positions[end] + 1]

def source_quote_span(quote: str, transcript: str) -> Optional[tuple[str, int, int]]:
    """Locate an exact quote and retain its original character range."""
    quote = quote.replace("**", "")
    compact_quote = "".join(quote.split())
    compact_source = "".join(transcript.split())
    if not compact_quote:
        return None
    start = compact_source.find(compact_quote)
    if start < 0:
        return None
    positions = [index for index, char in enumerate(transcript) if not char.isspace()]
    end = start + len(compact_quote) - 1
    return transcript[positions[start]:positions[end] + 1], positions[start], positions[end] + 1

def calculate_clip_rate(transcript: str, spans: list[tuple[int, int]]) -> float:
    total = sum(1 for char in transcript if not char.isspace())
    if not total or not spans:
        return 0.0
    merged = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    useful = sum(sum(1 for char in transcript[start:end] if not char.isspace()) for start, end in merged)
    return round(useful / total * 100, 1)

def fallback_opening_sentence(transcript: str) -> str:
    """Return an exact spoken sentence only when the model's quote cannot be verified."""
    spoken_lines = [
        line.strip()
        for line in transcript.splitlines()
        if line.strip() and not re.fullmatch(r"(?:发言人|speaker)?\s*\d{1,2}:\d{2}(?::\d{2})?", line.strip(), re.I)
    ]
    source = "\n".join(spoken_lines) or transcript.strip()
    sentences = [item.strip() for item in re.split(r"(?<=[。！？!?])", source) if item.strip()]
    return max(sentences or [source], key=len)

def normalise_report_payload(payload: dict) -> dict:
    """Accept minor model-format variations before validating the report schema."""
    def bounded_number(value, maximum, default=0):
        try:
            return max(0, min(maximum, float(value)))
        except (TypeError, ValueError):
            return default

    score_source = payload.get("overall_scores") or payload.get("scores") or {}
    legacy_score_names = {
        "hook_strength": "strong_viewpoint",
        "viewpoint_clarity": "information_gain",
        "information_density": "contrast_value",
        "emotional_tension": "standalone_segment",
        "sharing_potential": "user_propagation_value",
    }
    payload["overall_scores"] = {
        name: int(round(bounded_number(score_source.get(name, score_source.get(legacy_name)), 2)))
        for name, legacy_name in legacy_score_names.items()
    }
    payload["overall_summary"] = str(payload.get("overall_summary") or "模型未提供总体结论。")
    payload["overall_score"] = bounded_number(payload.get("overall_score"), 10)
    payload["effective_clip_rate"] = bounded_number(payload.get("effective_clip_rate"), 100)
    payload["worth_editing"] = bool(payload.get("worth_editing", False))
    level = payload.get("clip_value_level")
    allowed_levels = {"高剪辑价值", "中等剪辑价值", "低剪辑价值", "无明显剪辑价值"}
    payload["clip_value_level"] = level if level in allowed_levels else "中等剪辑价值"

    opening = payload.get("best_opening") or {}
    payload["best_opening"] = {
        "source_range": str(opening.get("source_range") or "全文原文"),
        "original_sentence": str(opening.get("original_sentence") or ""),
        "reason": str(opening.get("reason") or "从原文中选择相对更适合前置的一句。"),
    }

    raw_candidates = payload.get("candidates") or []
    if not isinstance(raw_candidates, list):
        raw_candidates = []
    candidates = []
    for raw_candidate in raw_candidates[:1]:
        if not isinstance(raw_candidate, dict):
            continue
        plan = raw_candidate.get("editing_plan") or {}
        ordered = plan.get("ordered_sentences") or []
        if not isinstance(ordered, list):
            ordered = []
        # Compatibility with the earlier opening/core/ending response shape.
        if not ordered:
            ordered = [plan.get(key, "") for key in ("opening_excerpt", "core_excerpt", "ending_excerpt")]
        ordered = [str(sentence).strip() for sentence in ordered if str(sentence).strip()]
        if len(ordered) < 2:
            continue
        value_types = raw_candidate.get("value_types") or []
        if isinstance(value_types, str):
            value_types = [value_types]
        candidates.append({
            "source_range": str(raw_candidate.get("source_range") or "全文原文"),
            "original_excerpt": str(raw_candidate.get("original_excerpt") or "\n".join(ordered)),
            "core_viewpoint": str(raw_candidate.get("core_viewpoint") or "原文中的核心观点"),
            "clip_value_score": bounded_number(raw_candidate.get("clip_value_score"), 10),
            "reason": str(raw_candidate.get("reason") or "该组原文句子可组成一条完整表达。"),
            "independence": raw_candidate.get("independence") if raw_candidate.get("independence") in {"高", "中", "低"} else "中",
            "value_types": [str(item) for item in value_types[:3]],
            "suggested_duration": str(raw_candidate.get("suggested_duration") or "30–60 秒"),
            "editing_plan": {
                "ordered_sentences": ordered[:6],
                "structure_reason": str(plan.get("structure_reason") or "按以上原文句子顺序呈现核心观点。"),
            },
        })
    payload["candidates"] = candidates
    payload["suggested_video_count"] = len(candidates)
    return payload

def evaluate_script(transcript: str, client: Optional[OpenAI] = None) -> EvaluationReport:
    if not transcript.strip():
        raise ValueError("请输入口播转写稿。")
    if client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("服务尚未配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY。")
        client = OpenAI(api_key=api_key, base_url=os.getenv("AI_BASE_URL", "https://api.deepseek.com"))
    schema = json.dumps(EvaluationReport.model_json_schema(), ensure_ascii=False)
    system = PROMPT_PATH.read_text(encoding="utf-8") + "\n\n必须只输出 JSON，不要 Markdown。JSON 必须符合此 Schema：\n" + schema
    response = client.chat.completions.create(
        model=os.getenv("AI_MODEL", os.getenv("OPENAI_MODEL", "deepseek-chat")), temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": "请完整阅读以下口播转写稿，再输出评估报告：\n\n" + transcript},
        ], response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("模型没有返回可解析的评估结果。")
    try:
        report = EvaluationReport.model_validate(normalise_report_payload(json.loads(content)))
        verified_candidates = []
        source_spans = []
        for candidate in report.candidates[:1]:
            plan = candidate.editing_plan
            verified_sentences = []
            candidate_spans = []
            for sentence in plan.ordered_sentences:
                match = source_quote_span(sentence, transcript)
                if match is None:
                    continue
                excerpt, start, end = match
                verified_sentences.append(excerpt)
                candidate_spans.append((start, end))
            if len(verified_sentences) < 2:
                continue
            plan.ordered_sentences = verified_sentences
            # The prominent UI title must also be usable source material, never an AI rewrite.
            candidate.core_viewpoint = verified_sentences[0]
            candidate.original_excerpt = highlight_key_sentence("\n".join(verified_sentences))
            verified_candidates.append(candidate)
            source_spans.extend(candidate_spans)
        report.candidates = verified_candidates
        report.suggested_video_count = len(verified_candidates)
        if not verified_candidates:
            report.worth_editing = False
            report.clip_value_level = "无明显剪辑价值"
        report.effective_clip_rate = calculate_clip_rate(transcript, source_spans)
        opening = exact_source_quote(report.best_opening.original_sentence, transcript)
        if opening:
            report.best_opening.original_sentence = opening
        else:
            report.best_opening.original_sentence = fallback_opening_sentence(transcript)
            report.best_opening.reason = "原稿中未找到模型选择的完全匹配句子，已展示原文中相对完整的一句供人工判断。"
        if report.candidates:
            # The recommendation and the actual edit must start from the same exact source sentence.
            report.best_opening.original_sentence = report.candidates[0].editing_plan.ordered_sentences[0]
            report.best_opening.source_range = report.candidates[0].source_range
        return report
    except Exception as exc:
        raise RuntimeError("模型返回内容不完整，已无法自动转换为评估报告；请重新评估一次。") from exc

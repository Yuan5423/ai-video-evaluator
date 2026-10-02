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
        report = EvaluationReport.model_validate(json.loads(content))
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
        return report
    except Exception as exc:
        raise RuntimeError("模型返回格式不符合评估报告结构。") from exc

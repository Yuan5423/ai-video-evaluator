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
        for candidate in report.candidates:
            excerpt = exact_source_quote(candidate.original_excerpt, transcript)
            if excerpt is None:
                continue
            candidate.original_excerpt = highlight_key_sentence(excerpt)
            candidate.recommended_hook = exact_source_quote(candidate.recommended_hook, transcript) or excerpt
            verified_candidates.append(candidate)
        report.candidates = verified_candidates
        report.suggested_video_count = min(report.suggested_video_count, len(verified_candidates))
        if not verified_candidates:
            report.worth_editing = False
        report.best_hook = exact_source_quote(report.best_hook, transcript) or (
            verified_candidates[0].recommended_hook if verified_candidates else ""
        )
        return report
    except Exception as exc:
        raise RuntimeError("模型返回格式不符合评估报告结构。") from exc

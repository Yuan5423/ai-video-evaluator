import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from schemas import EvaluationReport

load_dotenv()
PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"

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
        return EvaluationReport.model_validate(json.loads(content))
    except Exception as exc:
        raise RuntimeError("模型返回格式不符合评估报告结构。") from exc

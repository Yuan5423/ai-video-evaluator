import html
import io
import re
import textwrap
from datetime import datetime

import streamlit as st

from agent import evaluate_script

st.set_page_config(page_title="AI短视频口播评估助手", page_icon="🎬", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
.stApp{background:radial-gradient(circle at 8% 0,#edf0ff 0,transparent 31%),#f6f7fb;color:#182230;font-family:'DM Sans','Noto Sans SC',sans-serif}.block-container{max-width:1200px;padding:46px 34px 72px}h1{font-size:2.45rem!important;letter-spacing:-.055em}h2{font-size:1.24rem!important;margin:40px 0 5px;padding-left:12px;border-left:4px solid #635bff}.eyebrow{color:#635bff;font-size:.76rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px}.hero-subtitle{color:#69758a;font-size:1rem;margin-bottom:28px;max-width:680px}.surface,.card,.candidate,.titlecard,.operator-card,.clip-plan{background:rgba(255,255,255,.92);border:1px solid #e6e9f2;border-radius:18px;box-shadow:0 8px 30px rgba(24,34,48,.045)}.surface{padding:24px}.card{padding:22px 24px;height:100%}.candidate{padding:25px;margin:12px 0;border-left:4px solid #13a47a;background:linear-gradient(105deg,#f5fffb,#fff)}.titlecard{padding:17px 18px;min-height:105px;border-top:3px solid #ec8d32;background:linear-gradient(140deg,#fffaf4,#fff)}.operator-card{padding:19px 20px;min-height:132px;border-top:3px solid #665cff;background:linear-gradient(140deg,#f9f8ff,#fff)}.clip-plan{padding:24px;margin:12px 0;border-left:4px solid #3277e8;background:linear-gradient(105deg,#f4f9ff,#fff)}.label,.metric-label,.titlekind{color:#8791a0;font-size:.78rem;font-weight:700;margin:16px 0 6px;letter-spacing:.04em}.copy{color:#394455;line-height:1.7}.metric{color:#172033;font-size:2rem;font-weight:700;letter-spacing:-.04em}.metric-note{color:#637083;font-size:.82rem;margin-top:4px}.score{background:linear-gradient(135deg,#eeecff,#f0f7ff);border-color:#dfddff}.score .metric,.rank,.cscore{color:#574cff}.hook{padding:25px 28px;border-left:4px solid #f08a2b;background:linear-gradient(110deg,#fff8f0,#fff);border-radius:14px}.quote{color:#f08a2b;font-size:2rem;line-height:1}.hooktext{font-size:1.25rem;font-weight:700;line-height:1.65}.top{display:flex;justify-content:space-between;gap:16px}.rank{font-size:.76rem;font-weight:700;letter-spacing:.1em}.ctitle{font-size:1.15rem;font-weight:700;margin-top:5px}.cscore{font-size:1.35rem;font-weight:700}.flow{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.step{background:#eaf3ff;color:#2864bd;border-radius:999px;padding:9px 14px;font-size:.83rem;font-weight:600}.arrow{color:#6d9de3}.titletext{color:#263143;font-weight:600;line-height:1.5}.empty{padding:22px;background:#fafbfc;border:1px dashed #d9dee8;border-radius:14px;color:#7b8695}.section-tip{color:#7a8696;font-size:.88rem;margin:0 0 14px}.history-item{padding:14px 0;border-bottom:1px solid #edf0f4}div[data-testid="stTextArea"] textarea{background:#fff;border:1px solid #dfe4ef;border-radius:14px;min-height:300px;padding:18px;font-size:1rem;line-height:1.7}div[data-testid="stTextArea"] textarea:focus{border-color:#9c96ff;box-shadow:0 0 0 3px rgba(99,91,255,.12)}div[data-testid="stButton"] button{border:0;border-radius:13px;background:linear-gradient(105deg,#5549e8,#3977f6);color:#fff;font-weight:700;min-height:46px;box-shadow:0 8px 18px rgba(73,79,220,.2)}
div[data-testid="stRadio"] label,div[data-testid="stRadio"] label span,div[data-testid="stRadio"] p{color:#263143!important;font-weight:600!important}
/* Keep the original report layout; only make the six IP diagnosis cards easier to scan. */
h2{margin:34px 0 14px!important;padding-left:0!important;border-left:0!important}.candidate{border-left:1px solid #e6e9f2!important;background:rgba(255,255,255,.92)!important}.titlecard{border-top:1px solid #e6e9f2!important;background:rgba(255,255,255,.92)!important}.hook{border-left:4px solid #635bff!important;background:linear-gradient(110deg,#fff,#f8f8ff)!important}.quote{color:#635bff!important}.step{background:#f0f1f8!important;color:#4b5666!important}.arrow{color:#a0a8b5!important}.clip-plan{padding:24px;border-left:1px solid #e6e9f2;background:rgba(255,255,255,.92)}.section-tip{display:none}.operator-card{position:relative;overflow:hidden;padding:20px 20px 18px!important;min-height:146px!important;border:0!important;box-shadow:0 10px 24px rgba(36,49,73,.08)!important;transition:transform .18s ease}.operator-card:hover{transform:translateY(-3px)}.operator-card::after{content:"";position:absolute;width:72px;height:72px;right:-20px;top:-24px;border-radius:50%;background:rgba(255,255,255,.42)}.operator-card .metric-label{position:relative;z-index:1;display:inline-block;margin:0 0 12px!important;padding:5px 9px;border-radius:999px;background:rgba(255,255,255,.7);color:#354052!important}.operator-card .copy{position:relative;z-index:1;font-size:.94rem}.operator-icon{font-size:1.35rem;line-height:1;margin-right:7px;vertical-align:-2px}.operator-card.audience{background:linear-gradient(135deg,#e9e4ff,#f8f7ff)}.operator-card.hook-card{background:linear-gradient(135deg,#ffe8c8,#fff8ec)}.operator-card.conflict{background:linear-gradient(135deg,#ffdfe8,#fff5f8)}.operator-card.risk{background:linear-gradient(135deg,#dceeff,#f3f9ff)}.operator-card.comment{background:linear-gradient(135deg,#d9f7ec,#f1fcf8)}.operator-card.positioning{background:linear-gradient(135deg,#efe0ff,#faf5ff)}
/* Dashboard visual system: the same light, colourful card language is used across the whole product. */
.stApp{background:radial-gradient(circle at 5% 2%,#ded8ff 0,transparent 23%),radial-gradient(circle at 95% 14%,#d9f6ff 0,transparent 22%),linear-gradient(180deg,#f6f6ff 0%,#fbfcff 55%,#f7f9fd 100%)!important}.block-container{max-width:1240px!important}.eyebrow{display:inline-block;padding:6px 10px;border-radius:999px;background:#e8e5ff;color:#5549e8!important;letter-spacing:.1em}.hero-subtitle{padding:14px 18px;border-radius:16px;background:rgba(255,255,255,.72);border:1px solid rgba(255,255,255,.9);box-shadow:0 8px 28px rgba(71,78,139,.07)}h1{margin-top:10px!important}.surface{border:0!important;box-shadow:0 12px 28px rgba(43,52,88,.08)!important;background:linear-gradient(135deg,#fff,#f9f9ff)!important}.card{border:0!important;box-shadow:0 10px 24px rgba(43,52,88,.07)!important;background:linear-gradient(145deg,#fff,#f7f8ff)!important}.score{background:linear-gradient(135deg,#ded8ff,#f4f2ff)!important}.titlecard{border:0!important;box-shadow:0 9px 22px rgba(43,52,88,.06)!important}.titlecard:nth-child(1){background:linear-gradient(135deg,#ffe5f2,#fff7fb)!important}.titlecard:nth-child(2){background:linear-gradient(135deg,#e3f5ff,#f7fcff)!important}.titlecard:nth-child(3){background:linear-gradient(135deg,#fff1cf,#fffaf0)!important}.hook{border:0!important;background:linear-gradient(135deg,#fff0d9,#fffaf2)!important;box-shadow:0 12px 28px rgba(152,103,43,.09)}.candidate{border:0!important;background:linear-gradient(135deg,#e6f7f0,#fbfffd)!important;box-shadow:0 12px 26px rgba(28,110,82,.08)!important}.clip-plan{border:0!important;background:linear-gradient(135deg,#e6f0ff,#fbfdff)!important;box-shadow:0 12px 26px rgba(41,99,175,.08)!important}.empty{border:0!important;background:linear-gradient(135deg,#f1efff,#fafaff)!important}.flow .step{background:#fff!important;box-shadow:0 4px 10px rgba(40,75,134,.09)}div[data-testid="stTextArea"] textarea{border:0!important;background:rgba(255,255,255,.9)!important;box-shadow:0 10px 26px rgba(43,52,88,.08)!important}div[data-testid="stFileUploader"]{padding:16px;border-radius:18px;background:linear-gradient(135deg,#f0edff,#fafaff);border:1px dashed #bcb5ff}details[data-testid="stExpander"]{border:0!important;border-radius:18px!important;background:rgba(255,255,255,.78)!important;box-shadow:0 9px 24px rgba(43,52,88,.06)}
/* Varied bento-card geometry inspired by the supplied dashboard reference. */
.surface{border-radius:28px 28px 12px 28px!important}.card{border-radius:24px!important}.score{border-radius:32px 16px 32px 16px!important}.titlecard{border-radius:28px 12px 28px 12px!important;min-height:124px!important}.titlecard:nth-child(1){background:linear-gradient(135deg,#ffd5ed,#ffecf7)!important}.titlecard:nth-child(2){background:linear-gradient(135deg,#c9f0ff,#eefaff)!important}.titlecard:nth-child(3){background:linear-gradient(135deg,#ffe7a9,#fff7db)!important}.hook{border-radius:34px 14px 34px 14px!important}.candidate{border-radius:30px 14px 30px 14px!important}.clip-plan{border-radius:14px 30px 14px 30px!important}.operator-card{min-height:158px!important;border-radius:30px 14px 30px 14px!important}.operator-card.lead-card{min-height:194px!important;border-radius:38px 18px 38px 18px!important;background:linear-gradient(135deg,#ffc4e2 0%,#ee78be 48%,#d853ad 100%)!important;color:#fff}.operator-card.lead-card .metric-label{background:rgba(255,255,255,.28);color:#fff!important}.operator-card.lead-card .copy{color:#fff!important;font-size:1rem}.operator-card.tall-card{min-height:194px!important;border-radius:18px 38px 18px 38px!important;background:linear-gradient(145deg,#b8edff,#70cdec 60%,#5bb3db)!important}.operator-card.compact-card{min-height:144px!important}.operator-card.tag-card{min-height:124px!important;border-radius:16px 30px 16px 30px!important}.operator-action{min-height:124px;padding:21px 24px;border-radius:30px 16px 30px 16px;background:linear-gradient(135deg,#fff2ae,#ffd36f);box-shadow:0 10px 24px rgba(185,132,28,.14)}.operator-action .metric-label{margin:0 0 10px!important;color:#705000!important}.operator-action .copy{font-size:.98rem;color:#604d25}.flow .step:nth-child(3n+1){background:#ffd9ed!important}.flow .step:nth-child(3n+2){background:#d7f4ff!important}.flow .step:nth-child(3n){background:#fff0bd!important}
/* Final design system: calm monochrome structure + the lime accent palette from the reference. */
.stApp{background:linear-gradient(180deg,#edf4d8 0,#f6f7ef 38%,#f8f8f4 100%)!important;color:#111!important}.block-container{max-width:1180px!important;padding-top:28px!important}.product-hero{position:relative;overflow:hidden;padding:34px 38px 30px;margin:0 0 24px;border-radius:34px 34px 18px 34px;background:#111;color:#fff;box-shadow:0 18px 44px rgba(10,10,10,.18)}.product-hero::after{content:"";position:absolute;width:290px;height:290px;right:-80px;top:-120px;border-radius:50%;background:#b8d85e}.product-hero>*{position:relative;z-index:1}.product-hero h1{margin:12px 0 7px!important;color:#fff!important;font-size:2.65rem!important}.hero-kicker{display:inline-block;padding:5px 10px;border:1px solid rgba(255,255,255,.4);border-radius:999px;color:#d9ee99;font-size:.72rem;font-weight:700;letter-spacing:.1em}.hero-promise{font-size:1.45rem;font-weight:800;letter-spacing:-.03em}.product-hero p{max-width:700px;margin:10px 0 18px;color:#d5d5d5;line-height:1.7}.hero-steps{display:flex;gap:8px;flex-wrap:wrap}.hero-steps span{padding:8px 12px;border-radius:999px;background:#b8d85e;color:#111;font-size:.82rem;font-weight:800}.eyebrow,.hero-subtitle{display:none!important}h2{border:0!important;margin:34px 0 10px!important;padding:0!important;color:#111!important;font-size:1.4rem!important}.decision-hero{display:flex;justify-content:space-between;gap:24px;align-items:center;padding:27px 30px;margin:22px 0 30px;border-radius:28px 28px 12px 28px;background:#111;color:#fff}.decision-hero h2{margin:7px 0!important;color:#cce87d!important;font-size:2rem!important}.decision-hero p{max-width:750px;margin:0;color:#eee;line-height:1.75}.decision-score{flex:0 0 140px;padding:17px;border-radius:19px;background:#b8d85e;color:#111;text-align:center}.decision-score span,.decision-score small{display:block;font-size:.76rem;font-weight:700}.decision-score strong{font-size:3rem;line-height:1;letter-spacing:-.08em}.operator-card{min-height:184px!important;margin:0 0 14px!important;padding:20px!important;border-radius:24px!important;box-shadow:none!important;transform:none!important}.operator-card:hover{transform:none!important}.operator-card::after{display:none}.operator-card .metric-label{padding:0!important;background:none!important;color:#111!important;font-size:.82rem!important}.operator-card .copy{color:#1c1c1c!important;line-height:1.7}.operator-card.audience{background:#dff3a5!important}.operator-card.hook-card{background:#b8d85e!important}.operator-card.conflict{background:#ffd778!important}.operator-card.risk{background:#cde8dc!important}.operator-card.comment{background:#efd7ee!important}.operator-card.positioning{background:#d5e6ff!important}.operator-action{margin:0 0 24px;min-height:0!important;border-radius:18px 18px 28px 18px!important;background:#111!important;color:#fff!important;box-shadow:none!important}.operator-action .metric-label{color:#cce87d!important}.operator-action .copy{color:#fff!important}.surface,.card,.candidate,.titlecard,.hook,.clip-plan{border:0!important;box-shadow:none!important}.surface{background:#fff!important;border-radius:22px!important}.card{background:#fff!important;border-radius:20px!important}.score{background:#b8d85e!important}.titlecard{background:#fff!important;border:2px solid #111!important;border-radius:22px!important}.titlecard:nth-child(1),.titlecard:nth-child(2),.titlecard:nth-child(3){background:#fff!important}.titlecard:nth-child(1){border-radius:28px 10px 28px 10px!important}.titlecard:nth-child(2){border-radius:10px 28px 10px 28px!important}.hook{background:#fff7db!important;border-radius:30px 14px 30px 14px!important}.candidate{background:#fff!important;border-left:8px solid #b8d85e!important;border-radius:22px!important}.clip-plan{background:#e7f2c2!important;border-radius:14px 28px 14px 28px!important}.flow .step,.flow .step:nth-child(3n+1),.flow .step:nth-child(3n+2),.flow .step:nth-child(3n){background:#111!important;color:#fff!important;box-shadow:none!important}.metric{color:#111!important}.rank,.cscore{color:#587516!important}.empty{background:#fff!important;border:2px dashed #b8d85e!important}div[data-testid="stTextArea"] textarea{background:#fff!important;border:2px solid #111!important;box-shadow:none!important;border-radius:22px!important}div[data-testid="stButton"] button{background:#111!important;border-radius:999px!important;box-shadow:none!important}div[data-testid="stFileUploader"]{background:#fff!important;border:2px dashed #8aa63d!important;border-radius:20px!important}details[data-testid="stExpander"]{background:#fff!important;border:1px solid #d8dfc3!important;box-shadow:none!important}
/* IP board deliberately uses one muted palette, not six competing accent colours. */
.operator-card.audience,.operator-card.conflict,.operator-card.risk,.operator-card.comment,.operator-card.positioning{background:#f7f8ee!important}.operator-card.hook-card{background:#c9e47d!important}.operator-card.risk{background:#edf2db!important}.operator-card.positioning{background:#e7efcd!important}
</style>""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "transcript_input" not in st.session_state:
    st.session_state.transcript_input = ""
if "active_report" not in st.session_state:
    st.session_state.active_report = None
if "active_image" not in st.session_state:
    st.session_state.active_image = None

def file_to_text(uploaded_file):
    if uploaded_file.name.lower().endswith(".docx"):
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("服务器尚未安装 Word 文件导入组件。") from exc
        document = Document(io.BytesIO(uploaded_file.getvalue()))
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    paragraphs.append(" ".join(cells))
        text = "\n".join(paragraphs)
        if not text:
            raise ValueError("该 Word 文档没有可读取的文字内容。")
        return text
    try:
        return uploaded_file.getvalue().decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        return uploaded_file.getvalue().decode("gb18030").strip()

def format_highlighted_excerpt(text):
    """Safely render model-marked **key sentences** as bold text."""
    escaped = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

def make_report_image(report):
    """Create a portable PNG summary for download and history preview."""
    from PIL import Image, ImageDraw, ImageFont
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((path for path in font_candidates if __import__("os").path.exists(path)), None)
    regular = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
    small = ImageFont.truetype(font_path, 27) if font_path else ImageFont.load_default()
    title = ImageFont.truetype(font_path, 46) if font_path else ImageFont.load_default()
    lines = ["AI口播剪辑价值评估报告", "", f"剪辑价值：{report.clip_value_level}", f"综合评分：{report.overall_score:.1f} / 10", f"有效可剪率：{report.effective_clip_rate:.1f}%", f"预计可剪条数：{report.suggested_video_count}", "", "总体结论：", report.overall_summary]
    lines.extend(["", "推荐开头（原文）：", report.best_opening.original_sentence, f"原文范围：{report.best_opening.source_range}", f"理由：{report.best_opening.reason}"])
    lines.extend(["", "可剪片段："])
    for index, candidate in enumerate(report.candidates, 1):
        plan = candidate.editing_plan
        ordered_lines = [f"第 {step} 句：{sentence}" for step, sentence in enumerate(plan.ordered_sentences, 1)]
        lines.extend([f"核心成片｜{candidate.clip_value_score:.1f} / 10", f"原文范围：{candidate.source_range}", f"核心观点：{candidate.core_viewpoint}", f"为什么值得剪：{candidate.reason}", f"独立完整度：{candidate.independence}", f"价值类型：{'、'.join(candidate.value_types)}", f"预计时长：{candidate.suggested_duration}", "剪辑方案（原文句子重排）：", *ordered_lines, f"重排说明：{plan.structure_reason}", ""])
    wrapped = []
    for line in lines:
        # Chinese transcripts often contain no spaces; force wrapping to avoid clipping text horizontally.
        wrapped.extend(textwrap.wrap(line, width=30, break_long_words=True, break_on_hyphens=False) or [""])
    image = Image.new("RGB", (1440, max(1000, 220 + len(wrapped) * 56)), "white")
    draw = ImageDraw.Draw(image)
    y = 60
    for index, line in enumerate(wrapped):
        draw.text((76, y), line, fill="#182230", font=title if index == 0 else (regular if index in (2, 3, 4) else small))
        y += 72 if index == 0 else 56
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()

def render_report(report):
    st.markdown(f'''<section class="decision-hero">
      <div><div class="hero-kicker">素材剪辑结论</div><h2>{html.escape(report.clip_value_level)}</h2><p>{html.escape(report.overall_summary)}</p></div>
      <div class="decision-score"><span>综合评分</span><strong>{report.overall_score:.1f}</strong><small>/ 10</small></div>
    </section>''', unsafe_allow_html=True)
    st.header("IP 操盘诊断")
    st.caption("内容团队要先看这六项：谁会看、为什么停留、哪里会流失、如何形成讨论。")
    diagnosis = report.traffic_diagnosis
    def operator_card(label, value, card_class, icon, shape=""):
        st.markdown(f'<div class="operator-card {card_class} {shape}"><div class="metric-label"><span class="operator-icon">{icon}</span>{label}</div><div class="copy">{html.escape(value)}</div></div>', unsafe_allow_html=True)

    # Stable two-row grid: deliberate visual hierarchy without overlap at any screen width.
    for col, item in zip(st.columns(3), [
        ("目标观众", diagnosis.target_audience, "audience", "👥"),
        ("流量钩子", diagnosis.traffic_hook, "hook-card", "⚡"),
        ("核心冲突", diagnosis.core_conflict, "conflict", "🔥"),
    ]):
        with col:
            operator_card(*item)
    for col, item in zip(st.columns(3), [
        ("完播风险", diagnosis.retention_risk, "risk", "⏱️"),
        ("评论触发", diagnosis.comment_trigger, "comment", "💬"),
        ("IP 标签", diagnosis.ip_positioning, "positioning", "✦"),
    ]):
        with col:
            operator_card(*item)
    st.markdown(f'<div class="operator-action"><div class="metric-label">🧭 操盘下一步</div><div class="copy">{html.escape(report.operator_action)}</div></div>', unsafe_allow_html=True)
    st.header("抖音发布标题建议")
    st.markdown('<div class="section-tip">标题用于发布页；视频中的口播内容仍只使用原文句子。</div>', unsafe_allow_html=True)
    st.caption("以下是发布标题，不属于视频原文；视频内口播仍严格使用原文句子。")
    if report.title_options:
        for col, option in zip(st.columns(len(report.title_options)), report.title_options):
            with col:
                st.markdown(f'<div class="titlecard"><div class="titlekind">{html.escape(option.angle)}</div><div class="titletext">{html.escape(option.title)}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">本素材暂未形成可靠的发布标题建议。</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.markdown(f'<div class="card score"><div class="metric-label">综合评分</div><div class="metric">{report.overall_score:.1f}<span style="font-size:1rem;color:#8d96a4"> / 10</span></div><div class="metric-note">{"达到剪辑标准" if report.overall_score >= 8 else "尚未达到剪辑标准"}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card"><div class="metric-label">剪辑价值结论</div><div class="metric" style="font-size:1.35rem">{html.escape(report.clip_value_level)}</div><div class="metric-note">结合片段完整度与用户价值判断</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card"><div class="metric-label">有效可剪率</div><div class="metric">{report.effective_clip_rate:.1f}<span style="font-size:1rem;color:#8d96a4">%</span></div><div class="metric-note">预计可产出 {report.suggested_video_count} 条有效短视频</div></div>', unsafe_allow_html=True)

    st.header("五维评分")
    st.markdown('<div class="section-tip">快速定位素材是卡在开头、观点、信息密度、情绪还是传播性。</div>', unsafe_allow_html=True)
    scores = report.overall_scores
    dimensions = [("开头吸引力", scores.hook_strength), ("观点清晰度", scores.viewpoint_clarity), ("信息密度", scores.information_density), ("情绪 / 冲突", scores.emotional_tension), ("传播潜力", scores.sharing_potential)]
    for col, (name, value) in zip(st.columns(5), dimensions):
        with col:
            st.markdown(f'<div class="card"><div class="metric-label">{name}</div><div class="metric" style="font-size:1.35rem">{value}<span style="font-size:.85rem;color:#a0a8b5"> / 2</span></div><div style="height:5px;background:#edf0f5;border-radius:4px;margin-top:12px"><div style="width:{value * 50}%;height:5px;background:linear-gradient(90deg,#635bff,#5c9bff);border-radius:4px"></div></div></div>', unsafe_allow_html=True)

    st.header("推荐开头")
    st.markdown('<div class="section-tip">从原文中挑选最能让用户停下来的句子，可前置但不改写。</div>', unsafe_allow_html=True)
    opening = report.best_opening
    st.markdown(f'<div class="hook"><div class="quote">“</div><div class="hooktext">{html.escape(opening.original_sentence)}</div><div class="label">原文范围</div><div class="copy">{html.escape(opening.source_range)}</div><div class="label">为什么适合前置</div><div class="copy">{html.escape(opening.reason)}</div></div>', unsafe_allow_html=True)

    st.header("剪辑方案")
    st.markdown('<div class="section-tip">蓝色区块展示原文句子的重排顺序，不新增、不改写口播内容。</div>', unsafe_allow_html=True)
    if not report.candidates:
        st.markdown('<div class="empty">暂无可形成完整剪辑方案的独立片段。</div>', unsafe_allow_html=True)
    for index, candidate in enumerate(report.candidates, 1):
        plan = candidate.editing_plan
        ordered_steps = ''.join(f'<span class="step">第 {step} 句</span>{"<span class=\"arrow\">→</span>" if step < len(plan.ordered_sentences) else ""}' for step in range(1, len(plan.ordered_sentences) + 1))
        ordered_text = '<br>'.join(f'<b>第 {step} 句：</b>{html.escape(sentence)}' for step, sentence in enumerate(plan.ordered_sentences, 1))
        st.markdown(f'<div class="clip-plan"><div class="rank">核心成片 · {html.escape(candidate.core_viewpoint)}</div><div class="flow">{ordered_steps}</div><div class="copy">{ordered_text}<br><b>重排说明：</b>{html.escape(plan.structure_reason)}</div></div>', unsafe_allow_html=True)

    image_bytes = st.session_state.get("active_image")
    if image_bytes:
        st.header("保存分析截图")
        st.download_button("下载分析截图（PNG）", data=image_bytes, file_name="ai-video-evaluation-report.png", mime="image/png", use_container_width=False)
        st.image(image_bytes, caption="当前分析报告截图预览", use_container_width=True)

st.markdown('''<section class="product-hero">
  <div class="hero-kicker">AI VIDEO EVALUATOR / 01</div>
  <h1>AI 口播评估助手</h1>
  <div class="hero-promise">30 秒判断：这段口播，到底值不值得剪？</div>
  <p>不先教你怎么剪，先从原文里找出能留住人、能独立成片、值得投入剪辑时间的内容。</p>
  <div class="hero-steps"><span>01 投入口播</span><span>02 判断价值</span><span>03 找出可剪段落</span></div>
</section>''', unsafe_allow_html=True)

with st.expander(f"历史评估记录（{len(st.session_state.history)}）", expanded=False):
    st.caption("记录仅保存在当前浏览器会话中；刷新浏览器、清除缓存或重新部署后会消失。")
    if not st.session_state.history:
        st.write("还没有历史记录。完成一次评估后会自动保存在这里。")
    else:
        history_indices = list(range(len(st.session_state.history) - 1, -1, -1))
        selected_index = st.selectbox("选择历史记录", history_indices, format_func=lambda i: f"{st.session_state.history[i]['created_at']} · {st.session_state.history[i]['score']:.1f}/10 · {st.session_state.history[i]['transcript'].replace(chr(10), ' ')[:36]}", key="selected_history_index")
        selected_item = st.session_state.history[selected_index]
        if st.button("查看选中的历史记录", key="view_selected_history", type="secondary"):
            st.session_state.transcript_input = selected_item["transcript"]
            st.session_state.active_report = selected_item["report"]
            st.session_state.active_image = selected_item.get("image")
            st.rerun()
        for index in history_indices:
            item = st.session_state.history[index]
            title = item["transcript"].replace("\n", " ").strip()[:42] or "未命名口播"
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{title}…**  \\n{item['created_at']} · {item['score']:.1f}/10")
            with right:
                if st.button("查看", key=f"history_{index}"):
                    st.session_state.transcript_input = item["transcript"]
                    st.session_state.active_report = item["report"]
                    st.session_state.active_image = item.get("image")
                    st.rerun()
        if st.button("清空本次历史", key="clear_history"):
            st.session_state.history = []
            st.session_state.active_report = None
            st.session_state.active_image = None
            st.rerun()

with st.container(border=True):
    st.markdown('<div class="label" style="margin-top:0">口播素材</div>', unsafe_allow_html=True)
    source_mode = st.radio("导入方式", ["导入 Word 文档", "粘贴文字"], horizontal=True, label_visibility="collapsed")
    if source_mode == "导入 Word 文档":
        uploaded = st.file_uploader("上传 Word 文档", type=["docx"], help="仅支持未加密的 .docx 文件。旧版 .doc 请先在 Word 中另存为 .docx。")
        st.caption("上传后会自动提取 Word 正文和表格文字，无需再粘贴内容。")
        if uploaded is not None:
            try:
                uploaded_text = file_to_text(uploaded)
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Word 文档读取失败。请确认文件未加密、未损坏，并且是 .docx 格式；旧版 .doc 文件请先另存为 .docx。")
            else:
                fingerprint = f"{uploaded.name}:{uploaded.size}"
                if st.session_state.get("uploaded_fingerprint") != fingerprint:
                    st.session_state.transcript_input = uploaded_text
                    st.session_state.uploaded_fingerprint = fingerprint
                st.success(f"已读取《{uploaded.name}》的文字内容，点击下方按钮即可开始评估。")
    else:
        st.text_area("口播转写稿", key="transcript_input", height=330, label_visibility="collapsed", placeholder="请粘贴完整的口播转写稿，不需要自己整理，我们会自动寻找值得剪辑的内容。")
        st.caption("我们会阅读全文，并从任何位置寻找最强开头。")
    run = st.button("开始评估  →", type="primary", use_container_width=True)

if run:
    transcript = st.session_state.transcript_input
    if not transcript.strip():
        st.warning("请先输入或导入口播转写稿。")
    else:
        with st.spinner("正在完整阅读并寻找高价值片段…"):
            try:
                report = evaluate_script(transcript)
            except Exception as exc:
                st.error(f"评估失败（{type(exc).__name__}）：{exc}")
                st.caption("配置检测、网络、模型限流或模型返回格式都可能导致失败；上方信息可用于准确定位。")
            else:
                st.session_state.active_report = report
                report_image = make_report_image(report)
                st.session_state.active_image = report_image
                st.session_state.history.append({
                    "transcript": transcript,
                    "report": report,
                    "score": report.overall_score,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "image": report_image,
                })
                st.success("评估完成，结果已保存到本次历史记录。")

if st.session_state.active_report is not None:
    render_report(st.session_state.active_report)



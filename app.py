import html
import io
from datetime import datetime

import streamlit as st

from agent import evaluate_script

st.set_page_config(page_title="AI短视频口播评估助手", page_icon="🎬", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
.stApp{background:#f5f6f8;color:#182230;font-family:'DM Sans','Noto Sans SC',sans-serif}.block-container{max-width:1160px;padding:46px 34px 72px}h1{font-size:2.2rem!important;letter-spacing:-.04em}h2{font-size:1.2rem!important;margin:28px 0 12px}.eyebrow{color:#635bff;font-size:.76rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px}.hero-subtitle{color:#8993a3;font-size:1rem;margin-bottom:28px}.surface,.card,.candidate,.titlecard{background:#fff;border:1px solid #e8ebf1;border-radius:18px;box-shadow:0 8px 30px rgba(24,34,48,.045)}.surface{padding:24px}.card{padding:22px 24px;height:100%}.candidate{padding:25px;margin:12px 0}.titlecard{padding:17px 18px;min-height:105px}.label,.metric-label,.titlekind{color:#8791a0;font-size:.78rem;font-weight:600;margin:16px 0 6px}.copy{color:#394455;line-height:1.7}.metric{color:#172033;font-size:2rem;font-weight:700;letter-spacing:-.04em}.metric-note{color:#637083;font-size:.82rem;margin-top:4px}.score{background:linear-gradient(135deg,#f1efff,#f1f7ff);border-color:#dfddff}.score .metric,.rank,.cscore{color:#574cff}.hook{padding:25px 28px;border-left:4px solid #635bff;background:linear-gradient(110deg,#fff,#fafaff);border-radius:14px}.quote{color:#635bff;font-size:2rem;line-height:1}.hooktext{font-size:1.25rem;font-weight:600;line-height:1.65}.top{display:flex;justify-content:space-between;gap:16px}.rank{font-size:.76rem;font-weight:700;letter-spacing:.1em}.ctitle{font-size:1.15rem;font-weight:700;margin-top:5px}.cscore{font-size:1.35rem;font-weight:700}.flow{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.step{background:#f2f4f8;color:#4b5666;border-radius:999px;padding:9px 14px;font-size:.83rem;font-weight:600}.arrow{color:#a0a8b5}.titletext{color:#263143;font-weight:600;line-height:1.5}.empty{padding:22px;background:#fafbfc;border:1px dashed #d9dee8;border-radius:14px;color:#7b8695}.history-item{padding:14px 0;border-bottom:1px solid #edf0f4}div[data-testid="stTextArea"] textarea{background:#fff;border:1px solid #e0e4eb;border-radius:14px;min-height:300px;padding:18px;font-size:1rem;line-height:1.7}div[data-testid="stTextArea"] textarea:focus{border-color:#9c96ff;box-shadow:0 0 0 3px rgba(99,91,255,.12)}div[data-testid="stButton"] button{border:0;border-radius:13px;background:linear-gradient(105deg,#5549e8,#3977f6);color:#fff;font-weight:700;min-height:46px;box-shadow:0 8px 18px rgba(73,79,220,.2)}
div[data-testid="stRadio"] label,div[data-testid="stRadio"] label span,div[data-testid="stRadio"] p{color:#263143!important;font-weight:600!important}
</style>""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "transcript_input" not in st.session_state:
    st.session_state.transcript_input = ""
if "active_report" not in st.session_state:
    st.session_state.active_report = None

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

def render_report(report):
    st.markdown('<div class="eyebrow" style="margin-top:36px">EVALUATION REPORT</div>', unsafe_allow_html=True)
    st.header("素材总评")
    st.markdown(f'<div class="surface"><div class="copy">{html.escape(report.overall_summary)}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.markdown(f'<div class="card score"><div class="metric-label">综合评分</div><div class="metric">{report.overall_score:.1f}<span style="font-size:1rem;color:#8d96a4"> / 10</span></div><div class="metric-note">{"达到剪辑标准" if report.overall_score >= 8 else "尚未达到剪辑标准"}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card"><div class="metric-label">素材判断</div><div class="metric" style="font-size:1.35rem">{"高潜力素材" if report.worth_editing else "暂不建议剪辑"}</div><div class="metric-note">整体内容价值判断</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="card"><div class="metric-label">预计可剪条数</div><div class="metric">{report.suggested_video_count}</div><div class="metric-note">基于独立高价值观点</div></div>', unsafe_allow_html=True)

    st.header("五维评分")
    if report.candidates:
        scores = report.candidates[0].scores
        dimensions = [("观点冲击力", scores.viewpoint_impact), ("用户痛点", scores.user_pain_or_benefit), ("小白理解度", scores.beginner_clarity), ("可传播性", scores.editability), ("情绪记忆点", scores.emotion_memory)]
        for col, (name, value) in zip(st.columns(5), dimensions):
            with col:
                st.markdown(f'<div class="card"><div class="metric-label">{name}</div><div class="metric" style="font-size:1.35rem">{value}<span style="font-size:.85rem;color:#a0a8b5"> / 2</span></div><div style="height:5px;background:#edf0f5;border-radius:4px;margin-top:12px"><div style="width:{value * 50}%;height:5px;background:linear-gradient(90deg,#635bff,#5c9bff);border-radius:4px"></div></div></div>', unsafe_allow_html=True)

    st.header("推荐开头")
    st.markdown(f'<div class="hook"><div class="quote">“</div><div class="hooktext">{html.escape(report.best_hook)}</div></div>', unsafe_allow_html=True)
    st.header("爆款候选")
    if not report.candidates:
        st.markdown('<div class="empty">暂未发现达到合格标准的独立高价值片段。建议补充具体方法、案例或可执行步骤。</div>', unsafe_allow_html=True)
    for index, candidate in enumerate(report.candidates, 1):
        st.markdown(f'<div class="candidate"><div class="top"><div><div class="rank">TOP {index}</div><div class="ctitle">{html.escape(candidate.core_viewpoint)}</div></div><div class="cscore">{candidate.viral_score:.1f}<span style="font-size:.8rem;color:#9aa3b0"> / 10</span></div></div><div class="label">推荐开头</div><div class="copy">{html.escape(candidate.recommended_hook)}</div><div class="label">为什么值得剪</div><div class="copy">{html.escape(candidate.reason)}</div><div class="label">原文对应内容</div><div class="copy">{html.escape(candidate.original_excerpt)}</div><div class="label">剪辑结构</div><div class="copy">{html.escape(candidate.editing_structure)}</div></div>', unsafe_allow_html=True)

    st.header("剪辑方案")
    advice = report.editing_advice
    st.markdown(f'<div class="surface"><div class="flow"><span class="step">开头</span><span class="arrow">→</span><span class="step">痛点</span><span class="arrow">→</span><span class="step">核心观点</span><span class="arrow">→</span><span class="step">案例</span><span class="arrow">→</span><span class="step">结尾</span></div><div class="label">保留与删减</div><div class="copy"><b>开头：</b>{html.escape(advice.keep_opening)}<br><b>中间：</b>{html.escape(advice.keep_middle)}<br><b>删除：</b>{html.escape(advice.remove)}<br><b>结尾：</b>{html.escape(advice.keep_ending)}<br><b>建议时长：</b>{html.escape(advice.suggested_duration)}</div></div>', unsafe_allow_html=True)
    st.header("标题建议")
    for col, kind, title in zip(st.columns(3), ["痛点型", "反常识型", "结果型"], [report.titles.pain_point, report.titles.counterintuitive, report.titles.result]):
        with col:
            st.markdown(f'<div class="titlecard"><div class="titlekind">{kind}</div><div class="titletext">{html.escape(title)}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="eyebrow">AI CONTENT INTELLIGENCE</div>', unsafe_allow_html=True)
st.title("AI短视频口播评估助手")
st.markdown('<div class="hero-subtitle">从完整口播中识别真正值得剪辑的观点，让每一条内容都有清晰的传播理由。</div>', unsafe_allow_html=True)

with st.expander(f"历史评估记录（{len(st.session_state.history)}）", expanded=False):
    st.caption("记录仅保存在当前浏览器会话中；刷新浏览器、清除缓存或重新部署后会消失。")
    if not st.session_state.history:
        st.write("还没有历史记录。完成一次评估后会自动保存在这里。")
    else:
        for index, item in enumerate(reversed(st.session_state.history), 1):
            title = item["transcript"].replace("\n", " ").strip()[:42] or "未命名口播"
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{title}…**  \\n{item['created_at']} · {item['score']:.1f}/10")
            with right:
                if st.button("查看", key=f"history_{len(st.session_state.history) - index}"):
                    st.session_state.transcript_input = item["transcript"]
                    st.session_state.active_report = item["report"]
                    st.rerun()
        if st.button("清空本次历史", key="clear_history"):
            st.session_state.history = []
            st.session_state.active_report = None
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
            except Exception:
                st.error("评估暂时失败，请稍后重试；如果问题持续，请检查服务器端 API 配置。")
            else:
                st.session_state.active_report = report
                st.session_state.history.append({
                    "transcript": transcript,
                    "report": report,
                    "score": report.overall_score,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                st.success("评估完成，结果已保存到本次历史记录。")

if st.session_state.active_report is not None:
    render_report(st.session_state.active_report)


                a=report.editing_advice
                st.markdown(f'<div class="surface"><div class="flow"><span class="step">开头</span><span class="arrow">→</span><span class="step">痛点</span><span class="arrow">→</span><span class="step">核心观点</span><span class="arrow">→</span><span class="step">案例</span><span class="arrow">→</span><span class="step">结尾</span></div><div class="label">保留与删减</div><div class="copy"><b>开头：</b>{a.keep_opening}<br><b>中间：</b>{a.keep_middle}<br><b>删除：</b>{a.remove}<br><b>结尾：</b>{a.keep_ending}<br><b>建议时长：</b>{a.suggested_duration}</div></div>',unsafe_allow_html=True)
                st.header("标题建议")
                for col,kind,text in zip(st.columns(3),["痛点型","反常识型","结果型"],[report.titles.pain_point,report.titles.counterintuitive,report.titles.result]):
                    with col: st.markdown(f'<div class="titlecard"><div class="titlekind">{kind}</div><div class="titletext">{text}</div></div>',unsafe_allow_html=True)

# AI短视频口播评估助手

一个基于 Python、Streamlit 和兼容 OpenAI 接口模型的单 Agent 文字评估工具，默认接入 DeepSeek。

## 启动

```bash
cd ai-video-evaluator
python -m venv .venv
# Windows: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

编辑 `.env`，把 `DEEPSEEK_API_KEY` 替换为 DeepSeek 控制台创建的 Key（仅服务器端读取，勿提交 Git）。然后运行：

```bash
streamlit run app.py
```

默认使用 `deepseek-chat`。也可通过 `AI_BASE_URL` 和 `AI_MODEL` 切换到其他 OpenAI 兼容服务。测试样例位于 `tests/sample_scripts.json`。

# OpenClaw + Qwen 120k Context Optimization Demo

## Problem Statement

Có key Qwen 120k nhưng khi cắm vào OpenClaw thì crash phía Qwen.

Demo này được làm để trình bày cách giải quyết bài toán đó ngay cả khi:
- chưa có Qwen key thật
- không muốn phụ thuộc OpenClaw runtime thật
- cần một demo local ổn định trên Windows

Mặc định demo chạy bằng mock mode. Nếu máy có Ollama thì có thể bật `USE_OLLAMA=true`, nhưng nếu Ollama lỗi thì hệ thống vẫn fallback về mock để demo không fail.

## Root Cause

OpenClaw inject quá nhiều context mỗi turn.

Trong OpenClaw-style agent runtime, usable context luôn nhỏ hơn model window vì mỗi lượt gọi model còn phải gánh:
- `SOUL.md`
- `AGENTS.md`
- `MEMORY.md`
- `TOOLS.md`
- history
- tool outputs
- logs/search results

Raw context injection làm backend Qwen dễ crash, timeout hoặc treo trong giai đoạn prefill.

## Solution

Demo này bám theo tinh thần của `openclaw-optimization-guide`:
- minimal prompt files
- vault
- sub-agent summary
- pruning
- compaction

Ý tưởng cốt lõi:
- thu nhỏ injected files
- chuyển knowledge dài sang `vault/`
- dùng sub-agent để gom tool output lớn thành summary
- prune context bằng head/tail trimming
- compact history thành summary ngắn

Kết quả là payload gửi tới model backend nhỏ hơn rất nhiều và không còn ở vùng crash risk như raw mode.

## Repo Structure

```text
openclaw-qwen-demo/
  README.md
  Dockerfile
  docker-compose.yml
  backend/
    server.py
    optimize.py
    fake_openclaw_pipeline.py
    subagent.py
    demo_data.py
    model_client.py
    qwen_client.py
    requirements.txt
  frontend/
    index.html
    app.js
    style.css
  config/
    openclaw_demo_config.json
  minimal_prompt/
    SOUL.md
    AGENTS.md
    MEMORY.md
    TOOLS.md
  vault/
    01_thinking/qwen-openclaw-context-strategy.md
    02_reference/qwen-vllm-deploy.md
    02_reference/openclaw-compaction-pruning.md
```

## API Endpoints

- `GET /health`
- `POST /demo/raw`
- `POST /demo/optimized`
- `POST /demo/subagent`
- `GET /demo/vault`
- `GET /demo/compare`

## Cách Chạy Local

```bash
pip install -r backend/requirements.txt
uvicorn backend.server:app --host 0.0.0.0 --port 3000
```

Mở:

```text
http://localhost:3000
```

## Cách Chạy Docker

```bash
docker compose up --build
```

Mở:

```text
http://localhost:3000
```

## Script Demo 3 Phút Cho Leader

1. Mở trang demo và nói: "Bên này không dùng Qwen key thật, mock mode là mặc định để chứng minh giải pháp context optimization."
2. Bấm `Run RAW mode` để cho leader thấy payload raw rất dài, token estimate lớn, latency cao, crash risk cao.
3. Chỉ vào card giải thích rằng vấn đề không nằm ở model 120k trên giấy, mà nằm ở OpenClaw inject quá nhiều thứ mỗi turn.
4. Bấm `Run Sub-agent simulation` để cho thấy tool output 80k-120k chars được gom còn vài trăm chars.
5. Bấm `Show Vault strategy` để cho thấy `MEMORY.md` chỉ giữ pointer tới `vault/` thay vì dump full docs.
6. Bấm `Run OPTIMIZED mode` để cho leader thấy before/after chars, token reduction, crash risk giảm và model response thành công.
7. Chốt bằng bảng compare: "Qwen 120k không đồng nghĩa usable context là 120k. Cách giải quyết là giảm context pressure trước khi inference."

## Optional Ollama Mode

Mặc định hệ thống dùng mock response.

Nếu muốn thử local model qua Ollama:

```bash
set USE_OLLAMA=true
set OLLAMA_MODEL=qwen2.5:3b
uvicorn backend.server:app --host 0.0.0.0 --port 3000
```

Hoặc với Docker:

```bash
set USE_OLLAMA=true
docker compose up --build
```

Ứng dụng sẽ thử gọi:
- `http://host.docker.internal:11434/api/generate`
- `http://localhost:11434/api/generate`

Nếu Ollama fail thì tự fallback về mock mode.

## Note

Demo này không cần Qwen key thật; mock mode dùng để chứng minh giải pháp context optimization. Khi có Qwen key/vLLM backend thật, chỉ thay `model_client.py`.

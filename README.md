# OpenClaw + Gemini 2.5 Flash Optimized Context Demo

## 1. Mục tiêu demo

Repo này demo bản **đã apply fix** cho lỗi context overload trong OpenClaw-style runtime. Thay vì demo RAW vs OPTIMIZED, màn chính là live chat:

User question -> optimized OpenClaw-style prompt -> Gemini/mock answer -> no crash.

Backend vẫn dựng một raw context nội bộ để đo before/after, nhưng chỉ gửi prompt đã tối ưu sang model.

## 2. Vì sao không dùng Qwen key

Hiện tại chưa có Qwen key thật. Bài toán gốc là Qwen 120k context bị crash/timeout khi OpenClaw inject quá nhiều context. Demo này không gọi Qwen thật để tránh phụ thuộc key và tránh làm buổi demo fail.

## 3. Vì sao dùng Gemini 2.5 Flash free key

Gemini 2.5 Flash được dùng như backend live thay thế để chứng minh pipeline chat ổn sau khi context đã được tối ưu. Gemini không phải trọng tâm. Trọng tâm là chiến lược minimal prompt, vault pointer, sub-agent summary, pruning và compaction.

## 4. Chạy không có key: mock mode

Không cần cấu hình gì. Nếu thiếu `GEMINI_API_KEY`, backend tự trả mock response. UI vẫn hiển thị context budget, reduction %, estimated tokens và crash risk.

## 5. Chạy có Gemini key

Windows PowerShell:
 
```powershell
setx GEMINI_API_KEY "YOUR_KEY"
```

Sau đó mở terminal mới để biến môi trường có hiệu lực.

Backend giữ key ở server. Frontend không gọi Gemini trực tiếp và không bao giờ nhận key.

## 6. Cách chạy

```powershell
docker compose up --build
```

Mở:

```text
http://localhost:3000
```

Endpoints chính:

- `GET /health`
- `POST /chat`
- `GET /strategy`
- `GET /config/openclaw`

## 7. Script demo cho leader

“Em không demo raw overload nữa; em demo bản đã fix.”

“Gemini chỉ thay Qwen để live chat.”

“Chiến lược chính là minimal prompt, vault pointer, sub-agent summary, pruning, compaction.”

“Backend build raw OpenClaw-style context để đo before, nhưng chỉ gửi optimized prompt sang model.”

“Nếu Gemini hết quota hoặc chưa có key, mock fallback vẫn chạy để demo không fail.”

## 8. Nếu leader hỏi “Qwen đâu?”

“Khi có Qwen key, chỉ thay provider/model. Context optimization giữ nguyên.”

## Cấu trúc chính

```text
backend/server.py        FastAPI endpoints
backend/model_client.py  Gemini REST client + mock fallback
backend/optimize.py      token estimate, pruning, compaction, reduction metrics
backend/prompt_builder.py raw/optimized OpenClaw-style prompt builder
frontend/                static chat UI
minimal_prompt/          SOUL/AGENTS/MEMORY/TOOLS bản tối giản
vault/                   ghi chú dài, chỉ trỏ bằng pointer
config/                  ví dụ OpenClaw Gemini optimized config
```

# OpenClaw + Gemini 2.5 Flash Optimized Context Demo

## Mục tiêu demo

Repo này demo bản đã apply fix cho lỗi context overload trong OpenClaw-style runtime.

Flow chính:

```text
user question -> optimized OpenClaw-style context -> Gemini live answer -> low context budget / low crash risk
```

Gemini chỉ đóng vai trò live backend thay Qwen vì hiện chưa có Qwen key thật.
Khi có Qwen key thật, chỉ thay provider/model. Context strategy giữ nguyên.

## Vì sao không dùng Qwen key

Bài toán gốc là:

> Có key Qwen 120k nhưng khi cắm vào OpenClaw thì crash phía Qwen.

Demo này không phụ thuộc Qwen key thật để tránh làm buổi demo fail vì quota, timeout hoặc backend không sẵn sàng.

## Vì sao vẫn có thể crash dù window lớn

Qwen 120k hoặc Gemini vẫn có thể crash nếu OpenClaw inject quá nhiều context mỗi turn:
- `SOUL.md`
- `AGENTS.md`
- `MEMORY.md`
- `TOOLS.md`
- history
- tool outputs
- logs/search results

Model window lớn không đồng nghĩa safe usable runtime budget cũng lớn như vậy.

## Giải pháp

Demo bám theo chiến lược:
- minimal prompt files
- vault pointers
- sub-agent summary
- pruning
- compaction

Backend vẫn build một raw context nội bộ để đo before/after, nhưng chỉ gửi optimized prompt sang Gemini hoặc mock fallback.

## Mock fallback

Nếu thiếu `GEMINI_API_KEY` hoặc Gemini API lỗi, backend tự fallback về mock.
Demo không fail chỉ vì live backend không sẵn sàng.

## Gemini live mode

Windows PowerShell:

```powershell
setx GEMINI_API_KEY "YOUR_KEY"
```

Hoặc dùng:

```powershell
setx GOOGLE_API_KEY "YOUR_KEY"
```

Mở terminal mới để env có hiệu lực.

## Cách chạy

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

## Using this strategy in real OpenClaw

Web demo chứng minh pipeline tối ưu context.

Folder `openclaw-runtime-pack/` là bản áp dụng cùng chiến lược đó vào OpenClaw thật:
- `openclaw-runtime-pack/openclaw.json`
- `openclaw-runtime-pack/agent/SOUL.md`
- `openclaw-runtime-pack/agent/AGENTS.md`
- `openclaw-runtime-pack/agent/MEMORY.md`
- `openclaw-runtime-pack/agent/TOOLS.md`
- `openclaw-runtime-pack/agent/vault/...`

Cách set Gemini key trên Windows PowerShell:

```powershell
setx GEMINI_API_KEY "YOUR_KEY"
```

Khi dùng Qwen thật:
- chỉ thay provider/model trong `openclaw-runtime-pack/openclaw.json`
- giữ nguyên context strategy

## Script demo cho leader

1. “Em không demo raw overload làm flow chính; em demo bản đã fix với Gemini live hoặc mock fallback.”
2. “Gemini chỉ thay Qwen để live answer. Phần quan trọng là minimal prompt, vault pointer, sub-agent summary, pruning và compaction.”
3. “Khi có Qwen key thật, chỉ thay model/provider trong runtime pack; chiến lược tối ưu context vẫn giữ nguyên.”

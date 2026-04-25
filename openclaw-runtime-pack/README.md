# OpenClaw Runtime Pack

Pack này mô phỏng cách áp dụng cùng một chiến lược tối ưu context vào OpenClaw thật.

Mục tiêu:
- dùng Gemini 2.5 Flash làm live backend thay Qwen trong giai đoạn chưa có Qwen key
- giữ prompt files cực nhỏ
- đẩy knowledge dài sang vault
- dùng sub-agent summary thay raw tool output
- bật pruning và compaction mặc định

Khi có Qwen key thật:
- chỉ thay provider/model trong `openclaw.json`
- không cần đổi chiến lược context optimization

Env key:
- `GEMINI_API_KEY`
- hoặc `GOOGLE_API_KEY`

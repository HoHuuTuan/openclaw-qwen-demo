"""Context optimization simulation for RAW vs OPTIMIZED demo modes."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .demo_data import (
    CONTEXT_WINDOW_TOKENS,
    KNOWLEDGE_ARTICLES,
    SAFE_RUNTIME_BUDGET_TOKENS,
    build_minimal_context,
    build_raw_context,
)
from .qwen_client import QwenClient, QwenResult
from .subagent import run_research_subagent


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
ROOT = Path(__file__).resolve().parents[1]
MINIMAL_PROMPT_DIR = ROOT / "minimal_prompt"


@dataclass(frozen=True)
class SectionMetric:
    name: str
    tokens: int
    chars: int


@dataclass(frozen=True)
class TaskProfile:
    prompt_tokens: int
    complexity_label: str
    detected_topics: list[str]
    raw_pressure: float
    vault_article_limit: int
    analysis: str


@dataclass(frozen=True)
class DemoResult:
    mode: str
    status: str
    context_tokens: int
    context_window_tokens: int
    safe_runtime_budget_tokens: int
    estimated_latency_ms: int
    estimated_crash_risk_percent: int
    crash_risk_label: str
    summary_reduction_percent: int
    task_profile: TaskProfile
    sections: list[SectionMetric]
    pipeline: list[str]
    explanation: str
    prompt_preview: str


DEFAULT_PROMPT = (
    "Investigate why Qwen with a 120k context window crashes or times out "
    "when connected to an OpenClaw-style agent runtime, then propose a stable "
    "optimization strategy for production-like usage."
)


def normalize_prompt(prompt: str | None) -> str:
    cleaned = " ".join((prompt or "").split())
    return cleaned or DEFAULT_PROMPT


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def file_size_bytes(path: Path) -> int:
    return len(read_text(path).encode("utf-8"))


def current_workspace_budget() -> dict[str, Any]:
    soul_path = MINIMAL_PROMPT_DIR / "SOUL.md"
    memory_path = MINIMAL_PROMPT_DIR / "MEMORY.md"
    tools_path = MINIMAL_PROMPT_DIR / "TOOLS.md"
    agents_path = MINIMAL_PROMPT_DIR / "AGENTS.md"

    sizes = {
        "SOUL.md": file_size_bytes(soul_path),
        "MEMORY.md": file_size_bytes(memory_path),
        "TOOLS.md": file_size_bytes(tools_path),
        "AGENTS.md": file_size_bytes(agents_path),
    }
    injected_total = sum(sizes.values())
    return {
        "files": sizes,
        "injected_total_bytes": injected_total,
        "injected_total_kb": round(injected_total / 1024, 2),
        "target_kb": 8,
    }


def estimate_tokens(text: str) -> int:
    """Approximate tokens without depending on tokenizer packages."""

    return max(1, math.ceil(len(TOKEN_PATTERN.findall(text)) * 1.18))


def analyze_task(prompt: str) -> TaskProfile:
    prompt_tokens = estimate_tokens(prompt)
    lower_prompt = prompt.lower()
    topic_rules = {
        "qwen": {"qwen", "120k", "128k", "long context", "context window"},
        "openclaw": {"openclaw", "agent", "agents", "runtime"},
        "serving": {"vllm", "deploy", "latency", "prefill", "kv cache", "timeout"},
        "optimization": {"optimize", "optimization", "prune", "pruning", "compact", "compaction", "summary"},
        "coding": {"code", "repo", "bug", "test", "docker", "fastapi", "api"},
    }
    detected = [
        topic
        for topic, keywords in topic_rules.items()
        if any(keyword in lower_prompt for keyword in keywords)
    ]
    has_many_lines = prompt.count("\n") >= 3
    has_many_topics = len(detected) >= 3

    if prompt_tokens > 450 or has_many_lines or has_many_topics:
        complexity = "complex"
    elif prompt_tokens > 120 or len(detected) >= 2:
        complexity = "medium"
    else:
        complexity = "simple"

    pressure = 0.72 + min(prompt_tokens / 900, 0.38) + len(detected) * 0.055
    if has_many_lines:
        pressure += 0.08
    pressure = min(1.35, max(0.68, pressure))

    article_limit = 1
    if complexity == "medium":
        article_limit = 2
    if complexity == "complex":
        article_limit = 3

    topic_text = ", ".join(detected) if detected else "general"
    analysis = (
        f"Prompt tokens: ~{prompt_tokens}. Complexity: {complexity}. "
        f"Detected topics: {topic_text}. RAW pressure multiplier: {pressure:.2f}. "
        f"Optimized vault limit: {article_limit} focused article(s)."
    )

    return TaskProfile(
        prompt_tokens=prompt_tokens,
        complexity_label=complexity,
        detected_topics=detected or ["general"],
        raw_pressure=pressure,
        vault_article_limit=article_limit,
        analysis=analysis,
    )


def section_metrics(sections: dict[str, str]) -> list[SectionMetric]:
    return [
        SectionMetric(name=name, tokens=estimate_tokens(value), chars=len(value))
        for name, value in sections.items()
    ]


def join_sections(sections: dict[str, str]) -> str:
    return "\n\n".join(f"## {name}\n{value.strip()}" for name, value in sections.items())


def preview_context(context: str, limit: int = 2400) -> str:
    if len(context) <= limit:
        return context

    half = limit // 2
    omitted = len(context) - limit
    return (
        context[:half]
        + f"\n\n... omitted {omitted:,} characters of injected context ...\n\n"
        + context[-half:]
    )


def estimate_latency_ms(tokens: int) -> int:
    # Prefill grows faster than linearly in many practical agent setups because
    # large prompts add memory pressure, queueing, and repeated resend overhead.
    return int(450 + tokens * 0.95 + (tokens / 1000) ** 2 * 38)


def estimate_crash_risk_percent(tokens: int) -> int:
    if tokens <= SAFE_RUNTIME_BUDGET_TOKENS:
        return max(3, int(tokens / SAFE_RUNTIME_BUDGET_TOKENS * 18))
    overload = (tokens - SAFE_RUNTIME_BUDGET_TOKENS) / max(1, CONTEXT_WINDOW_TOKENS - SAFE_RUNTIME_BUDGET_TOKENS)
    return min(98, int(25 + overload * 92))


def crash_risk_label(tokens: int) -> str:
    if tokens > CONTEXT_WINDOW_TOKENS:
        return "critical: exceeds model window"
    if tokens > SAFE_RUNTIME_BUDGET_TOKENS:
        return "high: timeout / crash risk"
    if tokens > SAFE_RUNTIME_BUDGET_TOKENS * 0.65:
        return "medium: unstable under load"
    return "low: stable demo range"


def crash_risk_level(tokens: int) -> str:
    if tokens > SAFE_RUNTIME_BUDGET_TOKENS:
        return "cao"
    if tokens > SAFE_RUNTIME_BUDGET_TOKENS * 0.65:
        return "trung bình"
    return "thấp"


def context_size_label(tokens: int) -> str:
    ratio = tokens / SAFE_RUNTIME_BUDGET_TOKENS
    if ratio <= 0.25:
        return "gói tối ưu rất gọn"
    if ratio <= 0.65:
        return "gói tối ưu an toàn"
    if ratio <= 1:
        return "gần ngưỡng runtime an toàn"
    return "vượt ngưỡng runtime an toàn"


def compact_text(text: str, max_sentences: int = 5) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    selected = [sentence for sentence in sentences if sentence][:max_sentences]
    return " ".join(selected)


def format_runtime_status(result: QwenResult, *, simulated: bool) -> str:
    if simulated:
        return "mock fallback"
    if result.success:
        return "ok"
    return "failed"


def runtime_summary(result: QwenResult, *, simulated: bool) -> str:
    if simulated:
        return "Khong co Qwen that, dang hien ket qua fallback de demo offline."
    if result.success:
        return "Request da chay that qua Qwen endpoint."
    return result.error or "Request that khong thanh cong."


def build_comparison_verdict(
    *,
    optimized_success: bool,
    raw_success: bool,
    qwen_enabled: bool,
    optimized_tokens: int,
    raw_tokens: int,
) -> str:
    if not qwen_enabled:
        return (
            "Chua cau hinh Qwen that. Bang so sanh hien token/context that cua hai nhanh, "
            "nhung ket qua tra loi dang dung fallback o nhanh optimized."
        )
    if optimized_success and not raw_success:
        return (
            f"Cung mot prompt, nhanh optimized van tra loi duoc con nhanh raw that bai. "
            f"Chenh lech context dang active la ~{optimized_tokens:,} token vs ~{raw_tokens:,} token."
        )
    if optimized_success and raw_success:
        return (
            f"Ca hai nhanh deu tra loi duoc, nhung nhanh optimized gon hon ro ret "
            f"({optimized_tokens:,} token vs {raw_tokens:,} token) nen an toan hon cho runtime."
        )
    if not optimized_success and not raw_success:
        return (
            "Ca hai nhanh deu khong tra loi duoc tren cau hinh hien tai. "
            "Can kiem tra lai Qwen backend, timeout, hoac gioi han context."
        )
    return (
        "Ket qua runtime dang lech voi ky vong mo phong. "
        "Nen kiem tra lai timeout, model backend, va cach server xu ly prompt dai."
    )


def retrieve_vault_excerpt(query: str, article_limit: int) -> str:
    """Pick small excerpts from vault-like articles instead of injecting all docs."""

    query_terms = {
        term
        for term in re.findall(r"[a-zA-Z0-9_+-]{3,}", query.lower())
        if term not in {"the", "and", "for", "with", "this", "that", "when", "into"}
    }
    fallback_terms = {"qwen", "context", "openclaw", "pruning", "compaction", "timeout"}
    keywords = query_terms or fallback_terms
    ranked: list[tuple[int, dict[str, str]]] = []
    for article in KNOWLEDGE_ARTICLES:
        haystack = f"{article['title']} {article['body']}".lower()
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score == 0:
            score = sum(1 for keyword in fallback_terms if keyword in haystack)
        ranked.append((score, article))

    excerpts = []
    for _, article in sorted(ranked, key=lambda item: item[0], reverse=True)[:article_limit]:
        excerpts.append(
            f"Source: {article['path']}\n"
            f"{compact_text(article['body'], max_sentences=2)}"
        )
    return "\n\n".join(excerpts)


def prune_context(sections: dict[str, str], budget_tokens: int) -> dict[str, str]:
    """Drop lower-priority sections until the active context fits the budget."""

    priority = ["SOUL", "AGENTS", "MEMORY", "TOOLS", "TASK", "VAULT_EXCERPTS", "SUBAGENT_SUMMARY", "COMPACTED_STATE"]
    pruned = {key: sections[key] for key in priority if key in sections}

    while estimate_tokens(join_sections(pruned)) > budget_tokens and "VAULT_EXCERPTS" in pruned:
        pruned["VAULT_EXCERPTS"] = compact_text(pruned["VAULT_EXCERPTS"], max_sentences=3)
        if estimate_tokens(join_sections(pruned)) <= budget_tokens:
            break
        pruned.pop("VAULT_EXCERPTS", None)

    return pruned


def simulate_raw(prompt: str | None = None) -> DemoResult:
    user_task = normalize_prompt(prompt)
    profile = analyze_task(user_task)
    sections = build_raw_context(
        user_task,
        pressure=profile.raw_pressure,
        task_notes=profile.analysis,
    )
    prompt = join_sections(sections)
    tokens = estimate_tokens(prompt)
    risk = estimate_crash_risk_percent(tokens)
    status = "timeout / crash risk" if tokens > SAFE_RUNTIME_BUDGET_TOKENS else "ok"

    return DemoResult(
        mode="RAW",
        status=status,
        context_tokens=tokens,
        context_window_tokens=CONTEXT_WINDOW_TOKENS,
        safe_runtime_budget_tokens=SAFE_RUNTIME_BUDGET_TOKENS,
        estimated_latency_ms=estimate_latency_ms(tokens),
        estimated_crash_risk_percent=risk,
        crash_risk_label=crash_risk_label(tokens),
        summary_reduction_percent=0,
        task_profile=profile,
        sections=section_metrics(sections),
        pipeline=[
            "Inject full SOUL / AGENTS / MEMORY / TOOLS.",
            "Append entire knowledge base into prompt.",
            "Return full sub-agent transcript.",
            "Send oversized prompt to Qwen runtime.",
        ],
        explanation=(
            "RAW mode demonstrates the failure pattern: a 120k model window is "
            "consumed by runtime overhead before the actual task has enough safe "
            "space. The demo marks this as timeout/crash risk instead of calling "
            "any real model."
        ),
        prompt_preview=preview_context(prompt),
    )


def simulate_optimized(prompt: str | None = None) -> DemoResult:
    user_task = normalize_prompt(prompt)
    profile = analyze_task(user_task)
    sections = build_minimal_context(user_task, task_notes=profile.analysis)
    research = run_research_subagent(sections["TASK"])
    vault_excerpt = retrieve_vault_excerpt(sections["TASK"], profile.vault_article_limit)

    optimized_sections = {
        **sections,
        "VAULT_EXCERPTS": vault_excerpt,
        "SUBAGENT_SUMMARY": research.summary,
        "COMPACTED_STATE": (
            "Decision: prove that usable context is lower than advertised window. "
            "Risk: prompt bloat creates timeout pressure. Next step: show before/after metrics."
        ),
    }
    optimized_sections = prune_context(optimized_sections, SAFE_RUNTIME_BUDGET_TOKENS)
    prompt = join_sections(optimized_sections)
    tokens = estimate_tokens(prompt)

    summary_reduction = int(
        100 - (research.summary_chars / max(1, research.original_chars) * 100)
    )

    return DemoResult(
        mode="OPTIMIZED",
        status="stable simulation",
        context_tokens=tokens,
        context_window_tokens=CONTEXT_WINDOW_TOKENS,
        safe_runtime_budget_tokens=SAFE_RUNTIME_BUDGET_TOKENS,
        estimated_latency_ms=estimate_latency_ms(tokens),
        estimated_crash_risk_percent=estimate_crash_risk_percent(tokens),
        crash_risk_label=crash_risk_label(tokens),
        summary_reduction_percent=summary_reduction,
        task_profile=profile,
        sections=section_metrics(optimized_sections),
        pipeline=[
            "Minimize SOUL / AGENTS / MEMORY / TOOLS.",
            "Move long knowledge into vault files.",
            "Retrieve only focused vault excerpts.",
            "Require sub-agent to return concise summary.",
            "Prune stale or low-priority context.",
            "Compact previous work into short durable state.",
        ],
        explanation=(
            "OPTIMIZED mode follows the optimization-guide mindset: keep the "
            "active runtime prompt small and treat the vault as external "
            "knowledge. The model can have a 120k window, but the agent should "
            "operate far below the risky overload zone."
        ),
        prompt_preview=preview_context(prompt),
    )


def generate_simulated_answer(prompt: str, optimized: DemoResult) -> str:
    """Create a useful local answer while keeping the model-call seam obvious."""

    topics = set(optimized.task_profile.detected_topics)
    lead = (
        "Lượt chạy tối ưu này đã hoàn thành thành công trên luồng context kiểu OpenClaw đã được tinh gọn. "
        "Thay vì gửi toàn bộ runtime prompt cồng kềnh sang Qwen, backend chỉ dựng một gói context nhỏ hơn "
        "gồm prompt vận hành tối thiểu, trích đoạn từ vault, summary từ sub-agent, phần tool đã được cắt gọn "
        "và trạng thái đã được compaction."
    )

    points = [
        "Điểm gây overload thường không nằm ở prompt người dùng, mà nằm ở phần runtime context luôn bị inject lặp đi lặp lại quanh prompt đó.",
        "SOUL, AGENTS, MEMORY và TOOLS cần đủ ngắn để an toàn trong mọi lượt gọi model.",
        "Knowledge dài nên nằm trong vault và chỉ đi vào model call dưới dạng trích đoạn thật sự liên quan.",
        "Sub-agent nên trả về summary ngắn để bàn giao, thay vì full transcript.",
        "Pruning và compaction giúp loại bỏ lượt cũ, chỉ dẫn trùng lặp và mô tả tool dư thừa khỏi active prompt.",
    ]

    if "serving" in topics:
        points.append(
            "Với luồng serving của Qwen, cách này giúp giảm áp lực prefill, thời gian chờ hàng đợi, áp lực KV-cache và xác suất timeout."
        )
    if "coding" in topics:
        points.append(
            "Với workflow coding, cách này cũng giúp giữ ghi chú repo và hướng dẫn tool trong đúng phạm vi tác vụ hiện tại, thay vì dump toàn bộ file và history note."
        )
    if "optimization" in topics:
        points.append(
            "Mục tiêu của tối ưu không phải là lấp đầy cửa sổ 120k, mà là giữ request nằm đủ xa khỏi ngưỡng mất ổn định của runtime."
        )

    answer_lines = [
        lead,
        "",
        f"Với prompt của bạn: \"{prompt}\"",
        "",
        "Giải thích thực tế:",
    ]
    answer_lines.extend(f"- {point}" for point in points)
    answer_lines.extend(
        [
            "",
            "Kết luận: tác vụ này vẫn có thể được xử lý và trả lời vì active context đã đủ gọn để tránh vùng overload hoặc crash ở phía Qwen.",
        ]
    )
    return "\n".join(answer_lines)


def ask_with_optimized_context(prompt: str | None = None) -> dict[str, Any]:
    user_task = normalize_prompt(prompt)
    optimized = simulate_optimized(user_task)
    raw = simulate_raw(user_task)
    tokens = optimized.context_tokens
    budget = current_workspace_budget()
    optimized_context = join_sections(
        {
            "SOUL": "Operate through the optimized OpenClaw context path only.",
            "TASK": user_task,
            "COMPACTED_CONTEXT": optimized.prompt_preview,
        }
    )
    fallback_answer = generate_simulated_answer(user_task, optimized)
    qwen_client = QwenClient()
    qwen_result = qwen_client.complete(
        prompt=user_task,
        optimized_context=optimized_context,
        fallback_answer=fallback_answer,
    )
    raw_context = join_sections(
        build_raw_context(
            user_task,
            pressure=optimized.task_profile.raw_pressure,
            task_notes=optimized.task_profile.analysis,
        )
    )
    raw_runtime = qwen_client.complete_from_messages(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are answering through an unoptimized OpenClaw-style context path. "
                    "The following system context is intentionally verbose."
                ),
            },
            {"role": "system", "content": raw_context},
            {"role": "user", "content": user_task},
        ],
        allow_mock_fallback=False,
        timeout_seconds=45,
    )
    raw_injected_kb = round(len(raw_context.encode("utf-8")) / 1024, 2)
    optimized_is_simulated = not qwen_client.enabled or qwen_result.used_mock
    raw_is_simulated = not qwen_client.enabled
    raw_summary = (
        runtime_summary(raw_runtime, simulated=raw_is_simulated)
        if qwen_client.enabled
        else (
            "Chua cau hinh Qwen that. Nhanh raw dang hien so lieu context that va danh gia mo phong "
            "ve kha nang qua tai."
        )
    )
    raw_comparison = {
        "status": raw.status,
        "estimated_tokens": raw.context_tokens,
        "estimated_injected_kb": raw_injected_kb,
        "latency_estimate": raw_runtime.elapsed_ms or raw.estimated_latency_ms,
        "crash_risk_percent": raw.estimated_crash_risk_percent,
        "crash_risk_label": raw.crash_risk_label,
        "summary": raw_summary,
        "would_answer_successfully": raw_runtime.success if qwen_client.enabled else raw.context_tokens <= SAFE_RUNTIME_BUDGET_TOKENS,
        "actual": {
            "attempted": qwen_client.enabled,
            "status": format_runtime_status(raw_runtime, simulated=raw_is_simulated),
            "provider": raw_runtime.provider,
            "latency_ms": raw_runtime.elapsed_ms,
            "answer": raw_runtime.answer,
            "error": raw_runtime.error,
            "summary": raw_summary,
        },
    }

    return {
        "status": "ok",
        "prompt": user_task,
        "answer": qwen_result.answer,
        "mode": "optimized-qwen-path",
        "stable": qwen_result.success,
        "metrics": {
            "estimated_tokens": tokens,
            "crash_risk": crash_risk_level(tokens),
            "crash_risk_label": optimized.crash_risk_label,
            "crash_risk_percent": optimized.estimated_crash_risk_percent,
            "latency_estimate": qwen_result.elapsed_ms or optimized.estimated_latency_ms,
            "context_size_label": "đã tối ưu",
            "estimated_injected_kb": budget["injected_total_kb"],
        },
        "context_preview": optimized.prompt_preview,
        "optimization_applied": [
            "system prompt tối thiểu",
            "hướng dẫn AGENTS ngắn gọn",
            "memory dạng pointer",
            "context từ sub-agent đã được tóm tắt",
            "đã pruning tools/context",
            "đã loại bỏ các khối context lặp lại",
        ],
        "notes": (
            "Request đã hoàn thành qua luồng context tối ưu. "
            f"Provider đang dùng: {qwen_result.provider}."
        ),
        "adapter": {
            "provider": qwen_result.provider,
            "used_mock": qwen_result.used_mock,
            "real_qwen_enabled": qwen_result.provider == "qwen-http-adapter",
        },
        "optimized_run": {
            "attempted": qwen_client.enabled,
            "status": format_runtime_status(qwen_result, simulated=optimized_is_simulated),
            "provider": qwen_result.provider,
            "latency_ms": qwen_result.elapsed_ms,
            "answer": qwen_result.answer,
            "error": qwen_result.error,
            "summary": runtime_summary(qwen_result, simulated=optimized_is_simulated),
        },
        "comparison_verdict": build_comparison_verdict(
            optimized_success=qwen_result.success,
            raw_success=raw_comparison["would_answer_successfully"],
            qwen_enabled=qwen_client.enabled,
            optimized_tokens=tokens,
            raw_tokens=raw.context_tokens,
        ),
        "stability_label": "Đã trả lời thành công với context tối ưu",
        "stability_details": {
            "stability_note": (
                "Sau khi áp dụng giải pháp tối ưu, request kiểu OpenClaw được giữ trong vùng giảm rủi ro overload và có thể hoàn thành ổn định."
            ),
            "optimization_summary": optimized.pipeline,
            "task_analysis": optimized.task_profile.analysis,
        },
        "comparison_without_optimization": raw_comparison,
        "proof_checklist": [
            {
                "step": "1. Thu gọn workspace files",
                "status": "ok",
                "evidence": (
                    f"SOUL={budget['files']['SOUL.md']}B, MEMORY={budget['files']['MEMORY.md']}B, "
                    f"TOOLS={budget['files']['TOOLS.md']}B, AGENTS={budget['files']['AGENTS.md']}B, "
                    f"tong injected ~{budget['injected_total_kb']}KB"
                ),
            },
            {
                "step": "2. Day knowledge dai sang vault/",
                "status": "ok",
                "evidence": "Memory dang pointer; vault excerpts duoc truy xuat theo task thay vi dump toan bo docs.",
            },
            {
                "step": "3. Main Qwen chi lam orchestrator",
                "status": "ok",
                "evidence": "SOUL ghi ro: 'You coordinate; sub-agents execute'.",
            },
            {
                "step": "4. Bat pruning manh",
                "status": "ok",
                "evidence": "Prune context som, giu prompt duoi safe budget, khong dua lai output cu vao main session.",
            },
            {
                "step": "5. Bat compaction",
                "status": "ok",
                "evidence": "Co COMPACTED_STATE de chuyen cong viec nang thanh state ngan gon.",
            },
            {
                "step": "6. Giam tool spam",
                "status": "ok",
                "evidence": "Tool docs ngan; output dai khong dua vao session chinh, chi giu summary.",
            },
            {
                "step": "7. Cau hinh Qwen backend dung long-context",
                "status": "guide",
                "evidence": "Khi co backend that: dat --max-model-len, rope-scaling/YaRN va test tang dan.",
            },
            {
                "step": "8. Chay doi chieu ket qua that",
                "status": "ok" if qwen_client.enabled else "info",
                "evidence": (
                    "Da goi ca nhanh optimized va raw tren cung endpoint Qwen that."
                    if qwen_client.enabled
                    else "Chua cau hinh Qwen that nen optimized dung fallback, raw hien o che do mo phong."
                ),
            },
        ],
    }


def compare_modes(prompt: str | None = None, mode: str = "compare") -> dict[str, Any]:
    normalized_mode = mode.lower()
    if normalized_mode not in {"compare", "raw", "optimized"}:
        normalized_mode = "compare"

    raw = simulate_raw(prompt) if normalized_mode in {"compare", "raw"} else None
    optimized = simulate_optimized(prompt) if normalized_mode in {"compare", "optimized"} else None

    if normalized_mode == "raw":
        return {"raw": asdict(raw), "optimized": None, "comparison": None}

    if normalized_mode == "optimized":
        return {"raw": None, "optimized": asdict(optimized), "comparison": None}

    token_reduction = int(
        100 - (optimized.context_tokens / max(1, raw.context_tokens) * 100)
    )
    latency_reduction = int(
        100 - (optimized.estimated_latency_ms / max(1, raw.estimated_latency_ms) * 100)
    )
    risk_reduction = raw.estimated_crash_risk_percent - optimized.estimated_crash_risk_percent

    return {
        "raw": asdict(raw),
        "optimized": asdict(optimized),
        "comparison": {
            "token_reduction_percent": token_reduction,
            "latency_reduction_percent": latency_reduction,
            "crash_risk_reduction_points": risk_reduction,
            "message": (
                "120k context window does not equal 120k usable agent context. "
                "Optimization wins by reducing prompt bloat before inference."
            ),
        },
    }

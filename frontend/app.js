const formatNumber = new Intl.NumberFormat("vi-VN");

function byId(id) {
  return document.getElementById(id);
}

function latency(ms) {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms}ms`;
}

function runtimeLatency(actualMs, estimatedMs) {
  if (actualMs != null) return latency(actualMs);
  return latency(estimatedMs ?? 0);
}

function runtimeLabel(run, fallback) {
  if (!run) return fallback;
  if (run.status === "ok") return "Thành công";
  if (run.status === "failed") return "Lỗi thực tế";
  if (run.status === "mock fallback") return "Mock fallback";
  return fallback;
}

function riskLabel(label, percent) {
  if (!label && percent == null) return "không xác định";
  if (percent == null) return label;
  return `${label} (${percent}%)`;
}

function setBadgeState(el, state, text) {
  el.classList.remove("success-badge", "risk-badge", "neutral-badge");
  el.classList.add(state);
  el.textContent = text;
}

function resetCompareUi() {
  byId("verdictText").textContent = "Nhập prompt rồi bấm chạy để so sánh hai nhánh trên cùng một tác vụ.";
  byId("cmpStatusOpt").textContent = "Chưa chạy";
  byId("cmpStatusRaw").textContent = "Chưa chạy";
  byId("cmpTokensOpt").textContent = "--";
  byId("cmpTokensRaw").textContent = "--";
  byId("cmpInjectedOpt").textContent = "--";
  byId("cmpInjectedRaw").textContent = "--";
  byId("cmpLatencyOpt").textContent = "--";
  byId("cmpLatencyRaw").textContent = "--";
  byId("cmpRiskOpt").textContent = "--";
  byId("cmpRiskRaw").textContent = "--";
  byId("cmpStableOpt").textContent = "--";
  byId("cmpStableRaw").textContent = "--";

  setBadgeState(byId("stabilityBadge"), "neutral-badge", "Chưa chạy");
  setBadgeState(byId("rawBadge"), "neutral-badge", "Chưa chạy");

  byId("promptEcho").textContent = "Hãy gửi một prompt để chạy demo context tối ưu.";
  byId("answerText").textContent = "Câu trả lời sẽ xuất hiện tại đây sau khi hệ thống chạy xong nhánh optimized.";
  byId("answerNote").textContent = "Ghi chú về request optimized sẽ xuất hiện tại đây.";
  byId("rawRuntimeNote").textContent = "Khi chạy, panel này sẽ hiện câu trả lời thực tế hoặc lỗi thực tế của nhánh raw.";
  byId("rawAnswerText").textContent = "Chưa có kết quả raw.";
  byId("rawContrast").innerHTML = `
    <div><span>Trạng thái</span><strong>Chưa chạy</strong></div>
    <div><span>Nhận định</span><strong>Nhập prompt để xem nhánh raw phản ứng ra sao.</strong></div>
  `;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Yêu cầu thất bại: ${response.status}`);
  }

  return response.json();
}

function setLoading(isLoading) {
  const button = byId("askButton");
  button.disabled = isLoading;
  button.textContent = isLoading ? "Đang chạy so sánh thực tế..." : "Chạy So Sánh Thực Tế";
}

function setError(message) {
  byId("formError").textContent = message || "";
}

function renderMetrics(metrics) {
  const safeMetrics = metrics || {};
  byId("metricsList").innerHTML = `
    <div><span>Token ước tính bị inject</span><strong>${formatNumber.format(safeMetrics.estimated_tokens ?? 0)}</strong></div>
    <div><span>Injected context</span><strong>${safeMetrics.estimated_injected_kb ?? 0} KB</strong></div>
    <div><span>Độ trễ runtime</span><strong>${latency(safeMetrics.latency_estimate ?? 0)}</strong></div>
    <div><span>Rủi ro crash</span><strong>${riskLabel(safeMetrics.crash_risk_label ?? safeMetrics.crash_risk, safeMetrics.crash_risk_percent)}</strong></div>
    <div><span>Kích thước context</span><strong>${safeMetrics.context_size_label ?? "không xác định"}</strong></div>
  `;
}

function renderCompareScoreboard(data) {
  const opt = data.metrics || {};
  const raw = data.comparison_without_optimization || {};
  const optRun = data.optimized_run || {};
  const rawRun = raw.actual || {};

  byId("cmpStatusOpt").textContent = runtimeLabel(optRun, data.stable ? "Ổn định" : "Không ổn định");
  byId("cmpStatusRaw").textContent = runtimeLabel(rawRun, raw.status ?? "không xác định");
  byId("cmpTokensOpt").textContent = formatNumber.format(opt.estimated_tokens ?? 0);
  byId("cmpTokensRaw").textContent = formatNumber.format(raw.estimated_tokens ?? 0);
  byId("cmpInjectedOpt").textContent = `${opt.estimated_injected_kb ?? 0} KB`;
  byId("cmpInjectedRaw").textContent = raw.estimated_injected_kb != null ? `${raw.estimated_injected_kb} KB` : "không xác định";
  byId("cmpLatencyOpt").textContent = runtimeLatency(optRun.latency_ms, opt.latency_estimate);
  byId("cmpLatencyRaw").textContent = runtimeLatency(rawRun.latency_ms, raw.latency_estimate);
  byId("cmpRiskOpt").textContent = riskLabel(opt.crash_risk_label ?? opt.crash_risk, opt.crash_risk_percent);
  byId("cmpRiskRaw").textContent = riskLabel(raw.crash_risk_label, raw.crash_risk_percent);
  byId("cmpStableOpt").textContent = optRun.status === "mock fallback" ? "Có, nhưng là mock" : data.stable ? "Có" : "Không";
  byId("cmpStableRaw").textContent = rawRun.status === "mock fallback" ? "Có, nhưng là mock" : raw.would_answer_successfully ? "Có" : "Không";
}

function renderOptimization(items) {
  const list = byId("optimizationList");
  list.innerHTML = "";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });
}

function renderProofChecklist(items) {
  const list = byId("proofChecklist");
  list.innerHTML = "";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `${item.step} [${item.status}] - ${item.evidence}`;
    list.appendChild(li);
  });
}

function renderPathDetails(data) {
  const adapter = data.adapter || {};
  const stabilityDetails = data.stability_details || {};
  byId("pathDetails").innerHTML = `
    <div><span>Chế độ</span><strong>${data.mode ?? "không xác định"}</strong></div>
    <div><span>Ổn định</span><strong>${data.stable ? "có" : "không"}</strong></div>
    <div><span>Provider</span><strong>${adapter.provider ?? "không xác định"}</strong></div>
    <div><span>Đã bật Qwen thật</span><strong>${adapter.real_qwen_enabled ? "có" : "không"}</strong></div>
    <div><span>Ghi chú</span><strong>${data.notes ?? "không có"}</strong></div>
    <div><span>Nhận định ổn định</span><strong>${stabilityDetails.stability_note ?? "không có"}</strong></div>
  `;
}

function renderRawContrast(comparison) {
  const raw = comparison || {};
  const run = raw.actual || {};
  const rawAnswer = run.answer || run.error || "Không có phản hồi thực tế từ nhánh raw.";

  if (run.status === "ok") {
    setBadgeState(byId("rawBadge"), "success-badge", "Raw trả lời được");
  } else if (run.status === "failed" || raw.would_answer_successfully === false) {
    setBadgeState(byId("rawBadge"), "risk-badge", "Raw quá tải / thất bại");
  } else if (run.status === "mock fallback") {
    setBadgeState(byId("rawBadge"), "neutral-badge", "Raw đang ở mock");
  } else {
    setBadgeState(byId("rawBadge"), "neutral-badge", "Chưa có kết luận");
  }

  byId("rawRuntimeNote").textContent = run.summary ?? raw.summary ?? "Chưa có kết quả chạy thực tế.";
  byId("rawAnswerText").textContent = rawAnswer;
  byId("rawContrast").innerHTML = `
    <div><span>Trạng thái</span><strong>${runtimeLabel(run, raw.status ?? "không xác định")}</strong></div>
    <div><span>Token ước tính</span><strong>${formatNumber.format(raw.estimated_tokens ?? 0)}</strong></div>
    <div><span>Injected context</span><strong>${raw.estimated_injected_kb != null ? `${raw.estimated_injected_kb} KB` : "không xác định"}</strong></div>
    <div><span>Độ trễ runtime</span><strong>${runtimeLatency(run.latency_ms, raw.latency_estimate)}</strong></div>
    <div><span>Rủi ro crash</span><strong>${riskLabel(raw.crash_risk_label, raw.crash_risk_percent)}</strong></div>
    <div><span>Có trả lời ổn định không</span><strong>${raw.would_answer_successfully ? "có" : "không"}</strong></div>
    <div><span>Provider</span><strong>${run.provider ?? "không xác định"}</strong></div>
    <div><span>Nhận định</span><strong>${run.summary ?? raw.summary ?? "không có"}</strong></div>
  `;
}

function renderVerdict(data) {
  byId("verdictText").textContent = data.comparison_verdict ?? "Chưa có kết luận so sánh.";
}

function renderAnswer(data) {
  const optRun = data.optimized_run || {};
  byId("answerPanel").classList.remove("is-empty");

  if (optRun.status === "ok" || data.stable) {
    setBadgeState(byId("stabilityBadge"), "success-badge", "Optimized ổn định");
  } else if (optRun.status === "mock fallback") {
    setBadgeState(byId("stabilityBadge"), "neutral-badge", "Đang dùng fallback cục bộ");
  } else if (optRun.status === "failed") {
    setBadgeState(byId("stabilityBadge"), "risk-badge", "Optimized thất bại");
  } else {
    setBadgeState(byId("stabilityBadge"), "neutral-badge", "Chưa có kết luận");
  }

  byId("promptEcho").textContent = data.prompt ?? "";
  byId("answerText").textContent = data.answer ?? "Không nhận được nội dung trả lời.";
  byId("answerNote").textContent = optRun.summary ?? data.notes ?? "";
  byId("contextPreview").textContent = data.context_preview ?? "Không có context preview.";
  renderCompareScoreboard(data);
  renderMetrics(data.metrics);
  renderOptimization(data.optimization_applied);
  renderProofChecklist(data.proof_checklist);
  renderPathDetails(data);
  renderRawContrast(data.comparison_without_optimization);
  renderVerdict(data);
}

async function ask(prompt) {
  setError("");
  setLoading(true);

  setBadgeState(byId("stabilityBadge"), "neutral-badge", "Đang chạy");
  setBadgeState(byId("rawBadge"), "neutral-badge", "Đang chạy");
  byId("answerText").textContent = "Đang chạy nhánh optimized...";
  byId("answerNote").textContent = "Đang gọi cả nhánh optimized và raw để so sánh.";
  byId("rawRuntimeNote").textContent = "Đang chạy nhánh raw...";
  byId("rawAnswerText").textContent = "Đang chờ phản hồi thực tế từ nhánh raw...";
  byId("rawContrast").innerHTML = `
    <div><span>Trạng thái</span><strong>Đang chạy</strong></div>
    <div><span>Nhận định</span><strong>Hệ thống đang gửi cùng một prompt qua nhánh raw.</strong></div>
  `;

  try {
    const data = await postJson("/api/ask", { prompt });
    renderAnswer(data);
  } catch (error) {
    setError(error.message);
    setBadgeState(byId("stabilityBadge"), "risk-badge", "Optimized lỗi");
    setBadgeState(byId("rawBadge"), "neutral-badge", "Chưa có dữ liệu");
    byId("answerText").textContent = "Demo chưa thể hoàn tất. Hãy xem lỗi phía trên rồi thử lại.";
    byId("rawRuntimeNote").textContent = "Không lấy được kết quả từ backend.";
    byId("rawAnswerText").textContent = "Nhánh raw chưa có dữ liệu vì request chính bị lỗi.";
  } finally {
    setLoading(false);
  }
}

byId("askForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const prompt = byId("promptInput").value.trim();
  if (!prompt) {
    setError("Vui lòng nhập câu hỏi hoặc tác vụ trước khi chạy demo.");
    byId("promptInput").focus();
    return;
  }
  ask(prompt);
});

document.querySelectorAll(".example-prompt").forEach((button) => {
  button.addEventListener("click", () => {
    byId("promptInput").value = button.textContent;
    setError("");
    byId("promptInput").focus();
  });
});

resetCompareUi();

const formatNumber = new Intl.NumberFormat("vi-VN");

function byId(id) {
  return document.getElementById(id);
}

function promptValue() {
  return byId("promptInput").value.trim();
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function setBadge(id, kind, text) {
  const el = byId(id);
  el.className = `badge ${kind}`;
  el.textContent = text;
}

function prettyJson(data) {
  return JSON.stringify(data, null, 2);
}

function resetPanelsForPromptChange() {
  byId("cmpContextOptimized").textContent = "--";
  byId("cmpContextRaw").textContent = "--";
  byId("cmpTokensOptimized").textContent = "--";
  byId("cmpTokensRaw").textContent = "--";
  byId("cmpReduction").textContent = "--";
  byId("cmpRiskOptimized").textContent = "--";
  byId("cmpRiskRaw").textContent = "--";
  byId("cmpModelResponse").textContent = "--";
  byId("cmpCrashReason").textContent = "--";
  byId("rawBarFill").style.width = "92%";
  byId("optimizedBarFill").style.width = "14%";
  byId("rawBarLabel").textContent = "120k+";
  byId("optimizedBarLabel").textContent = "4k";
  setBadge("rawStatus", "neutral", "Chưa chạy");
  setBadge("optimizedStatus", "neutral", "Chưa chạy");
  setBadge("subagentStatus", "neutral", "Chưa chạy");
  byId("rawOutput").textContent = "Bấm \"Run RAW mode\" để xem payload dài gây crash/timeout risk.";
  byId("optimizedOutput").textContent = "Bấm \"Run OPTIMIZED mode\" để xem context được rút gọn và model response.";
  byId("subagentOutput").textContent = "Bấm \"Run Sub-agent simulation\" để xem 80k-120k chars được gom thành summary.";
}

function renderCompare(data) {
  const raw = data.raw || {};
  const optimized = data.optimized || {};
  const comparison = data.comparison || {};

  byId("cmpContextOptimized").textContent = optimized.after_chars != null ? `${formatNumber.format(optimized.after_chars)} chars` : "--";
  byId("cmpContextRaw").textContent = raw.before_chars != null ? `${formatNumber.format(raw.before_chars)} chars` : "--";
  byId("cmpTokensOptimized").textContent = optimized.estimated_tokens_after != null ? formatNumber.format(optimized.estimated_tokens_after) : "--";
  byId("cmpTokensRaw").textContent = raw.estimated_tokens != null ? formatNumber.format(raw.estimated_tokens) : "--";
  byId("cmpReduction").textContent = comparison.reduction_percent != null ? `${comparison.reduction_percent}%` : "--";
  byId("cmpRiskOptimized").textContent = comparison.crash_risk_optimized ?? "--";
  byId("cmpRiskRaw").textContent = comparison.crash_risk_raw ?? "--";
  byId("cmpModelResponse").textContent = comparison.model_response ?? "--";
  byId("cmpCrashReason").textContent = raw.crash_reason ?? "--";

  const rawWidth = Math.min(96, Math.max(15, Math.round((raw.estimated_tokens ?? 0) / 500)));
  const optimizedWidth = Math.min(96, Math.max(6, Math.round((optimized.estimated_tokens_after ?? 0) / 500)));
  byId("rawBarFill").style.width = `${rawWidth}%`;
  byId("optimizedBarFill").style.width = `${optimizedWidth}%`;
  byId("rawBarLabel").textContent = raw.estimated_tokens ? `${formatNumber.format(raw.estimated_tokens)} tok` : "120k+";
  byId("optimizedBarLabel").textContent = optimized.estimated_tokens_after ? `${formatNumber.format(optimized.estimated_tokens_after)} tok` : "4k";
}

async function runRaw() {
  setBadge("rawStatus", "neutral", "Đang chạy");
  const data = await fetchJson("/demo/raw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: promptValue() }),
  });
  setBadge("rawStatus", "bad", data.status);
  byId("rawOutput").textContent = prettyJson(data);
  return data;
}

async function runOptimized() {
  setBadge("optimizedStatus", "neutral", "Đang chạy");
  const data = await fetchJson("/demo/optimized", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: promptValue() }),
  });
  setBadge("optimizedStatus", "good", data.status);
  byId("optimizedOutput").textContent = prettyJson(data);
  return data;
}

async function runSubagent() {
  setBadge("subagentStatus", "neutral", "Đang chạy");
  const data = await fetchJson("/demo/subagent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: promptValue() }),
  });
  setBadge("subagentStatus", "good", data.status);
  byId("subagentOutput").textContent = prettyJson(data);
}

async function showVault() {
  setBadge("vaultStatus", "neutral", "Đang tải");
  const data = await fetchJson("/demo/vault");
  setBadge("vaultStatus", "good", "loaded");
  byId("vaultOutput").textContent = prettyJson(data);
}

async function runCompare() {
  const query = encodeURIComponent(promptValue());
  const data = await fetchJson(`/demo/compare?prompt=${query}`);
  renderCompare(data);
  return data;
}

byId("runRawButton").addEventListener("click", async () => {
  try {
    await runRaw();
    await runCompare();
  } catch (error) {
    setBadge("rawStatus", "bad", "error");
    byId("rawOutput").textContent = String(error.message || error);
  }
});

byId("runOptimizedButton").addEventListener("click", async () => {
  try {
    await runOptimized();
    await runCompare();
  } catch (error) {
    setBadge("optimizedStatus", "bad", "error");
    byId("optimizedOutput").textContent = String(error.message || error);
  }
});

byId("runSubagentButton").addEventListener("click", async () => {
  try {
    await runSubagent();
  } catch (error) {
    setBadge("subagentStatus", "bad", "error");
    byId("subagentOutput").textContent = String(error.message || error);
  }
});

byId("showVaultButton").addEventListener("click", async () => {
  try {
    await showVault();
  } catch (error) {
    setBadge("vaultStatus", "bad", "error");
    byId("vaultOutput").textContent = String(error.message || error);
  }
});

byId("runCompareButton").addEventListener("click", async () => {
  try {
    const data = await runCompare();
    if (data.raw) {
      setBadge("rawStatus", "bad", data.raw.status);
      byId("rawOutput").textContent = prettyJson(data.raw);
    }
    if (data.optimized) {
      setBadge("optimizedStatus", "good", data.optimized.status);
      byId("optimizedOutput").textContent = prettyJson(data.optimized);
    }
  } catch (error) {
    byId("cmpModelResponse").textContent = String(error.message || error);
  }
});

byId("promptInput").addEventListener("input", () => {
  resetPanelsForPromptChange();
});

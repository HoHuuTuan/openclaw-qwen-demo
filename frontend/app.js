const formatNumber = new Intl.NumberFormat("vi-VN");

function byId(id) {
  return document.getElementById(id);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

function setProviderStatus(provider, model, usedMock) {
  const isGemini = provider === "gemini";
  const badge = byId("providerBadge");
  badge.className = `badge ${isGemini ? "gemini" : "mock"}`;
  badge.textContent = isGemini ? "Gemini live" : "Mock fallback";
  byId("modelBadge").textContent = `model: ${model || "--"}`;
  byId("mockBadge").textContent = `used_mock: ${usedMock}`;
}

function setWarning(warning, provider) {
  const box = byId("warningBox");
  if (!warning && provider === "gemini") {
    box.classList.add("hidden");
    return;
  }
  byId("warningText").textContent = warning
    ? `Gemini key missing or API failed, using mock fallback. ${warning}`
    : "Gemini key missing or API failed, using mock fallback.";
  box.classList.remove("hidden");
}

function addMessage(role, text, warning) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  const label = role === "user" ? "Bạn" : "Assistant";
  node.innerHTML = `<strong>${label}</strong><p></p>${warning ? "<small></small>" : ""}`;
  node.querySelector("p").textContent = text;
  if (warning) node.querySelector("small").textContent = warning;
  byId("messages").appendChild(node);
  node.scrollIntoView({ behavior: "smooth", block: "end" });
}

function renderContext(context) {
  byId("beforeChars").textContent = formatNumber.format(context.before_chars);
  byId("afterChars").textContent = formatNumber.format(context.after_chars);
  byId("tokensBefore").textContent = formatNumber.format(context.tokens_before);
  byId("tokensAfter").textContent = formatNumber.format(context.tokens_after);
  byId("reduction").textContent = `${context.reduction_percent}%`;
  byId("crashRisk").textContent = context.crash_risk;
}

function renderSteps(steps) {
  byId("steps").innerHTML = steps.map((step) => `<li>${step}</li>`).join("");
}

async function loadHealthAndStrategy() {
  const [health, strategy] = await Promise.all([fetchJson("/health"), fetchJson("/strategy")]);
  setProviderStatus(health.provider, health.model, health.provider !== "gemini");
  setWarning(null, health.provider);
  byId("strategyText").textContent = strategy.optimized_runtime;
}

byId("chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = byId("messageInput");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  byId("sendButton").disabled = true;
  addMessage("user", message);

  try {
    const data = await fetchJson("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    setProviderStatus(data.provider, data.model, data.used_mock);
    setWarning(data.warning, data.provider);
    renderContext(data.context);
    renderSteps(data.optimization_steps);
    addMessage("assistant", data.answer, data.warning);
  } catch (error) {
    setProviderStatus("mock", "mock-optimized-context", true);
    setWarning("Mock fallback because Gemini key is missing or failed.", "mock");
    addMessage("assistant", String(error.message || error));
  } finally {
    byId("sendButton").disabled = false;
    input.focus();
  }
});

loadHealthAndStrategy().catch(() => {
  setProviderStatus("mock", "mock-optimized-context", true);
  setWarning("Mock fallback because Gemini key is missing or failed.", "mock");
});

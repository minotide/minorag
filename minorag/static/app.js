const chat = document.getElementById("chat");
const input = document.getElementById("question");
const btnSend = document.getElementById("btn-send");
let hasMessages = false;

function addMsg(text, cls) {
    if (!hasMessages) {
        chat.innerHTML = "";
        hasMessages = true;
    }
    const div = document.createElement("div");
    div.className = "msg " + cls;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
}

function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
}

// ---- Panel helpers ----

const _PANELS = ["git", "llm", "indexing"];

function togglePanel(name) {
    const panel = document.getElementById(name + "-panel");
    const isHidden = panel.classList.contains("hidden");
    // Fecha todos os painéis
    _PANELS.forEach(p => document.getElementById(p + "-panel").classList.add("hidden"));
    if (isHidden) {
        panel.classList.remove("hidden");
        if (name === "git") loadGitConfig();
        if (name === "llm") loadLlmConfig();
        if (name === "indexing") loadIndexingConfig();
    }
    // Oculta ou exibe a área de chat conforme painel aberto
    const anyOpen = _PANELS.some(p => !document.getElementById(p + "-panel").classList.contains("hidden"));
    document.getElementById("chat").classList.toggle("hidden", anyOpen);
    document.getElementById("input-area").classList.toggle("hidden", anyOpen);
}

// ---- Git Panel ----

async function loadGitConfig() {
    try {
        const res = await fetch("/api/git/config");
        const data = await res.json();
        document.getElementById("git-url").value = data.GIT_REPO_URL || "";
        document.getElementById("git-branch").value = data.GIT_BRANCH || "";
        document.getElementById("git-token").value = data.GIT_ACCESS_TOKEN || "";
        document.getElementById("git-ssh").value = data.GIT_SSH_KEY_PATH || "";
        document.getElementById("git-auto-update").checked =
            (data.GIT_AUTO_UPDATE || "").toLowerCase() === "true";
    } catch (err) {
        console.error("Erro ao carregar config git:", err);
    }
}

async function saveGitConfig() {
    const btn = document.getElementById("btn-save-git");
    const statusEl = document.getElementById("git-status");
    btn.disabled = true;
    btn.textContent = "Salvando...";
    statusEl.textContent = "";
    statusEl.className = "config-status-msg";

    try {
        const res = await fetch("/api/git/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                GIT_REPO_URL: document.getElementById("git-url").value,
                GIT_BRANCH: document.getElementById("git-branch").value,
                GIT_ACCESS_TOKEN: document.getElementById("git-token").value,
                GIT_SSH_KEY_PATH: document.getElementById("git-ssh").value,
                GIT_AUTO_UPDATE: document.getElementById("git-auto-update").checked ? "true" : "false",
            }),
        });
        const data = await res.json();
        statusEl.textContent = res.ok ? "✓ " + data.message : "✗ " + (data.error || "Erro ao salvar");
        statusEl.className = "config-status-msg " + (res.ok ? "success" : "error");
    } catch (err) {
        statusEl.textContent = "✗ Erro: " + err.message;
        statusEl.className = "config-status-msg error";
    }

    btn.disabled = false;
    btn.textContent = "Salvar no .env";
}

async function gitSync() {
    const btn = document.getElementById("btn-sync");
    const statusEl = document.getElementById("git-status");
    btn.disabled = true;
    btn.textContent = "Sincronizando...";
    statusEl.textContent = "";
    statusEl.className = "config-status-msg";

    const payload = {
        repo_url: document.getElementById("git-url").value,
        branch: document.getElementById("git-branch").value,
        token: document.getElementById("git-token").value,
    };

    try {
        const response = await fetch("/api/git/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const data = JSON.parse(line.slice(6));
                if (data.type === "log") {
                    statusEl.textContent = data.text;
                } else if (data.type === "done") {
                    statusEl.textContent = "✓ " + data.text;
                    statusEl.className = "config-status-msg success";
                } else if (data.type === "error") {
                    statusEl.textContent = "✗ " + data.text;
                    statusEl.className = "config-status-msg error";
                }
            }
        }
    } catch (err) {
        statusEl.textContent = "✗ Erro: " + err.message;
        statusEl.className = "config-status-msg error";
    }

    btn.disabled = false;
    btn.textContent = "Sincronizar Codebase";
}

// ---- LLM Panel ----

async function loadLlmConfig() {
    try {
        const res = await fetch("/api/llm/config");
        const data = await res.json();
        document.getElementById("llm-url").value = data.OLLAMA_URL || "";
        document.getElementById("llm-embed-model").value = data.EMBED_MODEL || "";
        document.getElementById("llm-model").value = data.LLM_MODEL || "";
        document.getElementById("llm-top-k").value = data.TOP_K || "";
        document.getElementById("llm-num-ctx").value = data.OLLAMA_NUM_CTX || "";
        document.getElementById("llm-num-predict").value = data.OLLAMA_NUM_PREDICT || "";
        document.getElementById("llm-num-thread").value = data.OLLAMA_NUM_THREAD || "";
        document.getElementById("llm-num-batch").value = data.OLLAMA_NUM_BATCH || "";
        document.getElementById("llm-temperature").value = data.OLLAMA_TEMPERATURE || "";
        document.getElementById("llm-repeat-penalty").value = data.OLLAMA_REPEAT_PENALTY || "";
        document.getElementById("llm-prompt-template").value = data.PROMPT_TEMPLATE || "";
    } catch (err) {
        console.error("Erro ao carregar config LLM:", err);
    }
}

async function saveLlmConfig() {
    const btn = document.getElementById("btn-save-llm");
    const statusEl = document.getElementById("llm-status");
    btn.disabled = true;
    btn.textContent = "Salvando...";
    statusEl.textContent = "";
    statusEl.className = "config-status-msg";

    try {
        const res = await fetch("/api/llm/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                OLLAMA_URL: document.getElementById("llm-url").value,
                EMBED_MODEL: document.getElementById("llm-embed-model").value,
                LLM_MODEL: document.getElementById("llm-model").value,
                TOP_K: document.getElementById("llm-top-k").value,
                OLLAMA_NUM_CTX: document.getElementById("llm-num-ctx").value,
                OLLAMA_NUM_PREDICT: document.getElementById("llm-num-predict").value,
                OLLAMA_NUM_THREAD: document.getElementById("llm-num-thread").value,
                OLLAMA_NUM_BATCH: document.getElementById("llm-num-batch").value,
                OLLAMA_TEMPERATURE: document.getElementById("llm-temperature").value,
                OLLAMA_REPEAT_PENALTY: document.getElementById("llm-repeat-penalty").value,
                PROMPT_TEMPLATE: document.getElementById("llm-prompt-template").value,
            }),
        });
        const data = await res.json();
        statusEl.textContent = res.ok ? "✓ " + data.message : "✗ " + (data.error || "Erro ao salvar");
        statusEl.className = "config-status-msg " + (res.ok ? "success" : "error");
    } catch (err) {
        statusEl.textContent = "✗ Erro: " + err.message;
        statusEl.className = "config-status-msg error";
    }

    btn.disabled = false;
    btn.textContent = "Salvar no .env";
}

// ---- Indexing Panel ----

async function loadIndexingConfig() {
    try {
        const res = await fetch("/api/indexing/config");
        const data = await res.json();
        document.getElementById("idx-extensions").value = data.FILE_EXTENSIONS || "";
        document.getElementById("idx-include-names").value = data.INCLUDE_FILENAMES || "";
        document.getElementById("idx-ignore-dirs").value = data.IGNORE_DIRS || "";
        document.getElementById("idx-chunk-size").value = data.CHUNK_SIZE || "";
        document.getElementById("idx-chunk-overlap").value = data.CHUNK_OVERLAP || "";
    } catch (err) {
        console.error("Erro ao carregar config indexação:", err);
    }
}

async function saveIndexingConfig() {
    const btn = document.getElementById("btn-save-indexing");
    const statusEl = document.getElementById("indexing-status");
    btn.disabled = true;
    btn.textContent = "Salvando...";
    statusEl.textContent = "";
    statusEl.className = "config-status-msg";

    try {
        const res = await fetch("/api/indexing/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                FILE_EXTENSIONS: document.getElementById("idx-extensions").value,
                INCLUDE_FILENAMES: document.getElementById("idx-include-names").value,
                IGNORE_DIRS: document.getElementById("idx-ignore-dirs").value,
                CHUNK_SIZE: document.getElementById("idx-chunk-size").value,
                CHUNK_OVERLAP: document.getElementById("idx-chunk-overlap").value,
            }),
        });
        const data = await res.json();
        statusEl.textContent = res.ok ? "✓ " + data.message : "✗ " + (data.error || "Erro ao salvar");
        statusEl.className = "config-status-msg " + (res.ok ? "success" : "error");
    } catch (err) {
        statusEl.textContent = "✗ Erro: " + err.message;
        statusEl.className = "config-status-msg error";
    }

    btn.disabled = false;
    btn.textContent = "Salvar no .env";
}

// ---- Chat ----

async function sendQuestion() {
    const question = input.value.trim();
    if (!question) return;

    input.value = "";
    btnSend.disabled = true;

    addMsg(question, "user");
    const thinking = addMsg("Pensando...", "bot typing");

    try {
        const response = await fetch("/api/query/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let answerEl = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const data = JSON.parse(line.slice(6));
                if (data.type === "log") {
                    thinking.textContent = data.text;
                } else if (data.type === "token") {
                    if (!answerEl) {
                        thinking.remove();
                        answerEl = addMsg("", "bot");
                    }
                    answerEl.textContent += data.text;
                    chat.scrollTop = chat.scrollHeight;
                } else if (data.type === "error") {
                    thinking.remove();
                    addMsg(data.text, "bot error");
                }
            }
        }
    } catch (err) {
        thinking.remove();
        addMsg("Erro de conexão: " + err.message, "bot error");
    }

    btnSend.disabled = false;
    input.focus();
}

// Auto-resize textarea
input.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
});

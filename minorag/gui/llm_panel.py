"""Painel de configuração LLM."""

from PySide6.QtWidgets import (
    QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from minorag import config as _cfg
from minorag.gui.env_helpers import save_env_vars
from minorag.gui.widgets import make_label


class LlmPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Row 0-1: URL, Embed Model, LLM Model
        grid.addWidget(make_label("URL do Ollama"), 0, 0)
        self._url = QLineEdit()
        self._url.setPlaceholderText("http://localhost:11434")
        grid.addWidget(self._url, 1, 0)

        grid.addWidget(make_label("Modelo de Embedding"), 0, 1)
        self._embed_model = QLineEdit()
        self._embed_model.setPlaceholderText("nomic-embed-text")
        grid.addWidget(self._embed_model, 1, 1)

        grid.addWidget(make_label("Modelo LLM"), 0, 2)
        self._llm_model = QLineEdit()
        self._llm_model.setPlaceholderText("qwen2.5-coder:3b")
        grid.addWidget(self._llm_model, 1, 2)

        # Row 2-3: Top K, num_ctx, num_predict
        grid.addWidget(make_label("Top K (chunks por consulta)"), 2, 0)
        self._top_k = QSpinBox()
        self._top_k.setRange(1, 50)
        self._top_k.setValue(5)
        grid.addWidget(self._top_k, 3, 0)

        grid.addWidget(make_label("Contexto (num_ctx)"), 2, 1)
        self._num_ctx = QSpinBox()
        self._num_ctx.setRange(512, 131072)
        self._num_ctx.setValue(4096)
        grid.addWidget(self._num_ctx, 3, 1)

        grid.addWidget(make_label("Tokens gerados (num_predict)"), 2, 2)
        self._num_predict = QSpinBox()
        self._num_predict.setRange(64, 131072)
        self._num_predict.setValue(768)
        grid.addWidget(self._num_predict, 3, 2)

        # Row 4-5: num_thread, num_batch, temperature
        grid.addWidget(make_label("Threads (num_thread)"), 4, 0)
        self._num_thread = QSpinBox()
        self._num_thread.setRange(1, 128)
        self._num_thread.setValue(8)
        grid.addWidget(self._num_thread, 5, 0)

        grid.addWidget(make_label("Batch (num_batch)"), 4, 1)
        self._num_batch = QSpinBox()
        self._num_batch.setRange(1, 4096)
        self._num_batch.setValue(256)
        grid.addWidget(self._num_batch, 5, 1)

        grid.addWidget(make_label("Temperature"), 4, 2)
        self._temperature = QDoubleSpinBox()
        self._temperature.setRange(0.0, 2.0)
        self._temperature.setSingleStep(0.05)
        self._temperature.setDecimals(2)
        self._temperature.setValue(0.2)
        grid.addWidget(self._temperature, 5, 2)

        # Row 6-7: repeat_penalty
        grid.addWidget(make_label("Repeat Penalty"), 6, 0)
        self._repeat_penalty = QDoubleSpinBox()
        self._repeat_penalty.setRange(0.5, 2.0)
        self._repeat_penalty.setSingleStep(0.05)
        self._repeat_penalty.setDecimals(2)
        self._repeat_penalty.setValue(1.15)
        grid.addWidget(self._repeat_penalty, 7, 0)

        layout.addLayout(grid)

        # Prompt template
        layout.addWidget(make_label("Prompt Template"))
        self._prompt = QPlainTextEdit()
        self._prompt.setMinimumHeight(180)
        layout.addWidget(self._prompt)

        hint = QLabel(
            "Use {chunks} e {question} como marcadores obrigatórios.")
        hint.setStyleSheet("color: #484f58; font-size: 11px;")
        layout.addWidget(hint)

        # Botões
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Salvar no .env")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self._save_config)
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        layout.addStretch()

        self._load_config()

    def _load_config(self) -> None:
        self._url.setText(_cfg.OLLAMA_URL)
        self._embed_model.setText(_cfg.EMBED_MODEL)
        self._llm_model.setText(_cfg.LLM_MODEL)
        self._top_k.setValue(_cfg.TOP_K)
        self._num_ctx.setValue(int(_cfg.OLLAMA_OPTIONS.get("num_ctx", 4096)))
        self._num_predict.setValue(
            int(_cfg.OLLAMA_OPTIONS.get("num_predict", 768)))
        self._num_thread.setValue(
            int(_cfg.OLLAMA_OPTIONS.get("num_thread", 8)))
        self._num_batch.setValue(
            int(_cfg.OLLAMA_OPTIONS.get("num_batch", 256)))
        self._temperature.setValue(_cfg.OLLAMA_OPTIONS.get("temperature", 0.2))
        self._repeat_penalty.setValue(
            _cfg.OLLAMA_OPTIONS.get("repeat_penalty", 1.15))
        self._prompt.setPlainText(_cfg.PROMPT_TEMPLATE)

    def _save_config(self) -> None:
        prompt_encoded = self._prompt.toPlainText().replace("\n", "\\n")
        updates = {
            "OLLAMA_URL": self._url.text(),
            "EMBED_MODEL": self._embed_model.text(),
            "LLM_MODEL": self._llm_model.text(),
            "TOP_K": str(self._top_k.value()),
            "OLLAMA_NUM_CTX": str(self._num_ctx.value()),
            "OLLAMA_NUM_PREDICT": str(self._num_predict.value()),
            "OLLAMA_NUM_THREAD": str(self._num_thread.value()),
            "OLLAMA_NUM_BATCH": str(self._num_batch.value()),
            "OLLAMA_TEMPERATURE": str(self._temperature.value()),
            "OLLAMA_REPEAT_PENALTY": str(self._repeat_penalty.value()),
            "PROMPT_TEMPLATE": prompt_encoded,
        }
        save_env_vars(updates)

        _cfg.OLLAMA_URL = updates["OLLAMA_URL"]
        _cfg.EMBED_MODEL = updates["EMBED_MODEL"]
        _cfg.LLM_MODEL = updates["LLM_MODEL"]
        _cfg.TOP_K = self._top_k.value()
        _cfg.OLLAMA_OPTIONS["num_ctx"] = self._num_ctx.value()
        _cfg.OLLAMA_OPTIONS["num_predict"] = self._num_predict.value()
        _cfg.OLLAMA_OPTIONS["num_thread"] = self._num_thread.value()
        _cfg.OLLAMA_OPTIONS["num_batch"] = self._num_batch.value()
        _cfg.OLLAMA_OPTIONS["temperature"] = self._temperature.value()
        _cfg.OLLAMA_OPTIONS["repeat_penalty"] = self._repeat_penalty.value()
        _cfg.PROMPT_TEMPLATE = self._prompt.toPlainText()

        self._status.setObjectName("statusSuccess")
        self._status.setText("✓ Configuração LLM salva com sucesso!")
        self._status.setStyleSheet("")
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

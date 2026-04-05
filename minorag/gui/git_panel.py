"""Painel de configuração Git."""

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import (
    QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from minorag import config as _cfg
from minorag.gui.env_helpers import clear_codebase, save_env_vars
from minorag.gui.widgets import make_label
from minorag.gui.workers import SyncWorker


class GitPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sync_worker: SyncWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(make_label("URL do repositório *"), 0, 0)
        self._url = QLineEdit()
        self._url.setPlaceholderText("https://github.com/usuario/projeto.git")
        grid.addWidget(self._url, 1, 0)

        grid.addWidget(make_label("Branch *"), 0, 1)
        self._branch = QLineEdit()
        self._branch.setPlaceholderText("main")
        grid.addWidget(self._branch, 1, 1)

        grid.addWidget(make_label("Token de acesso pessoal (opcional)"), 2, 0)
        self._token = QLineEdit()
        self._token.setPlaceholderText("Para repositórios privados (HTTPS)")
        self._token.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(self._token, 3, 0)

        grid.addWidget(make_label("Caminho da Chave SSH (opcional)"), 2, 1)
        self._ssh = QLineEdit()
        self._ssh.setPlaceholderText("~/.ssh/id_rsa")
        grid.addWidget(self._ssh, 3, 1)

        self._auto_update = QCheckBox(
            "Atualizar repositório automaticamente no startup")
        grid.addWidget(self._auto_update, 4, 0, 1, 2)

        layout.addLayout(grid)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._btn_sync = QPushButton("Sincronizar Codebase")
        self._btn_sync.setObjectName("btnSync")
        self._btn_sync.clicked.connect(self._sync)
        btn_layout.addWidget(self._btn_sync)

        btn_clear = QPushButton("Limpar Codebase")
        btn_clear.setObjectName("btnDanger")
        btn_clear.clicked.connect(self._clear)
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        layout.addStretch()

        self.reload_config()

        # Auto-save com debounce de 700 ms
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(700)
        self._save_timer.timeout.connect(self._save_config)
        self._url.textChanged.connect(self._schedule_save)
        self._branch.textChanged.connect(self._schedule_save)
        self._token.textChanged.connect(self._schedule_save)
        self._ssh.textChanged.connect(self._schedule_save)
        self._auto_update.stateChanged.connect(self._schedule_save)

    def reload_config(self) -> None:
        for w in (self._url, self._branch, self._token, self._ssh, self._auto_update):
            w.blockSignals(True)
        self._url.setText(_cfg.GIT_REPO_URL)
        self._branch.setText(_cfg.GIT_BRANCH)
        self._token.setText(_cfg.GIT_ACCESS_TOKEN)
        self._ssh.setText(_cfg.GIT_SSH_KEY_PATH)
        self._auto_update.setChecked(_cfg.GIT_AUTO_UPDATE)
        for w in (self._url, self._branch, self._token, self._ssh, self._auto_update):
            w.blockSignals(False)

    def _save_config(self) -> None:
        updates = {
            "GIT_REPO_URL": self._url.text(),
            "GIT_BRANCH": self._branch.text(),
            "GIT_ACCESS_TOKEN": self._token.text(),
            "GIT_SSH_KEY_PATH": self._ssh.text(),
            "GIT_AUTO_UPDATE": "true" if self._auto_update.isChecked() else "false",
        }
        save_env_vars(updates)

        _cfg.GIT_REPO_URL = updates["GIT_REPO_URL"]
        _cfg.GIT_BRANCH = updates["GIT_BRANCH"]
        _cfg.GIT_ACCESS_TOKEN = updates["GIT_ACCESS_TOKEN"]
        _cfg.GIT_SSH_KEY_PATH = updates["GIT_SSH_KEY_PATH"]
        _cfg.GIT_AUTO_UPDATE = self._auto_update.isChecked()

    def _schedule_save(self) -> None:
        self._save_timer.start()

    def _flush_save(self) -> None:
        """Persiste imediatamente, cancelando qualquer debounce pendente."""
        self._save_timer.stop()
        self._save_config()

    def _sync(self) -> None:
        if self._sync_worker is not None:
            return
        self._flush_save()
        self._btn_sync.setEnabled(False)
        self._btn_sync.setText("Sincronizando...")
        self._set_status("")

        self._sync_worker = SyncWorker(
            repo_url=self._url.text() or None,
            branch=self._branch.text() or None,
            token=self._token.text() or None,
        )
        self._sync_worker.log_received.connect(self._on_sync_log)
        self._sync_worker.error_occurred.connect(self._on_sync_error)
        self._sync_worker.finished_signal.connect(self._on_sync_done)
        self._sync_worker.start()

    @Slot(str)
    def _on_sync_log(self, text: str) -> None:
        self._set_status(text)

    @Slot(str)
    def _on_sync_error(self, text: str) -> None:
        self._set_status(f"{text}", error=True)
        self._btn_sync.setEnabled(True)
        self._btn_sync.setText("Sincronizar Codebase")
        self._sync_worker = None

    @Slot(str)
    def _on_sync_done(self, text: str) -> None:
        self._set_status(f"{text}", success=True)
        self._btn_sync.setEnabled(True)
        self._btn_sync.setText("Sincronizar Codebase")
        self._sync_worker = None

    def _clear(self) -> None:
        reply = QMessageBox.question(
            self, "Limpar Codebase",
            "Isso irá remover todos os arquivos clonados (.codebase/) e o índice do ChromaDB.\n\n"
            "O repositório precisará ser sincronizado novamente.\n\nTem certeza?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_codebase()
            self._set_status(
                "Codebase e índice removidos com sucesso.", success=True)

    def _set_status(self, text: str, success: bool = False, error: bool = False) -> None:
        if success:
            self._status.setObjectName("statusSuccess")
        elif error:
            self._status.setObjectName("statusError")
        else:
            self._status.setObjectName("")
        self._status.setText(text)
        self._status.setStyleSheet("")
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)
        self._status.setStyleSheet("")  # force re-apply
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

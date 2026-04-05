"""Janela principal e ponto de entrada da GUI."""

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from minorag.gui.chat_panel import ChatPanel
from minorag.gui.env_helpers import reset_env_defaults
from minorag.gui.git_panel import GitPanel
from minorag.gui.indexing_panel import IndexingPanel
from minorag.gui.llm_panel import LlmPanel
from minorag.gui.widgets import make_separator


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("minorag — pergunte ao seu código")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(24, 16, 24, 16)

        title_layout = QHBoxLayout()
        title = QLabel("minorag")
        title.setObjectName("title")
        subtitle = QLabel("pergunte ao seu código")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addStretch()

        btn_reset = QPushButton("Restaurar .env")
        btn_reset.setObjectName("btnDanger")
        btn_reset.setToolTip("Apaga o .env e restaura todos os valores padrão")
        btn_reset.clicked.connect(self._reset_env)

        header.addLayout(title_layout)
        header.addWidget(btn_reset)

        header_widget = QWidget()
        header_widget.setLayout(header)
        main_layout.addWidget(header_widget)
        main_layout.addWidget(make_separator())

        # Nota local
        note = QLabel(
            "Configurações, codebase e índices são salvos apenas localmente "
            "no arquivo .env e nos diretórios .codebase e .chromadb do projeto."
        )
        note.setObjectName("localNote")
        note.setContentsMargins(24, 0, 24, 0)
        main_layout.addWidget(note)
        main_layout.addWidget(make_separator())

        # Tabs
        self._tabs = QTabWidget()

        self._chat = ChatPanel()
        self._git = GitPanel()
        self._llm = LlmPanel()
        self._indexing = IndexingPanel()

        self._tabs.addTab(self._chat, "💬 Chat")
        self._tabs.addTab(self._git, "⚙ Repositório")
        self._tabs.addTab(self._llm, "⚙ LLM")
        self._tabs.addTab(self._indexing, "⚙ Indexação")

        main_layout.addWidget(self._tabs, 1)

    def _reset_env(self) -> None:
        reply = QMessageBox.question(
            self, "Restaurar .env",
            "Isso irá apagar todas as configurações do .env e restaurar os valores padrão.\n\nTem certeza?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            reset_env_defaults()
            QMessageBox.information(
                self, "Restaurar .env",
                ".env restaurado para os valores padrão."
            )

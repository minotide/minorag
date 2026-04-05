"""Painel de configuração de Indexação."""

from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)

from minorag import config as _cfg
from minorag.gui.env_helpers import save_env_vars
from minorag.gui.widgets import make_label


class IndexingPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(make_label(
            "Extensões de arquivo (separadas por vírgula)"))
        self._extensions = QLineEdit()
        self._extensions.setPlaceholderText(".java,.py,.js,.ts,...")
        layout.addWidget(self._extensions)

        layout.addWidget(make_label(
            "Nomes de arquivo incluídos (separados por vírgula)"))
        self._include_names = QLineEdit()
        self._include_names.setPlaceholderText("architecture.md")
        layout.addWidget(self._include_names)

        layout.addWidget(make_label(
            "Diretórios ignorados (separados por vírgula)"))
        self._ignore_dirs = QLineEdit()
        self._ignore_dirs.setPlaceholderText("target,.git,node_modules,...")
        layout.addWidget(self._ignore_dirs)

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(make_label("Tamanho do chunk (caracteres)"), 0, 0)
        self._chunk_size = QSpinBox()
        self._chunk_size.setRange(200, 10000)
        self._chunk_size.setValue(1500)
        grid.addWidget(self._chunk_size, 1, 0)

        grid.addWidget(make_label("Sobreposição do chunk (caracteres)"), 0, 1)
        self._chunk_overlap = QSpinBox()
        self._chunk_overlap.setRange(0, 5000)
        self._chunk_overlap.setValue(200)
        grid.addWidget(self._chunk_overlap, 1, 1)

        layout.addLayout(grid)

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

        self.reload_config()

    def reload_config(self) -> None:
        self._extensions.setText(",".join(_cfg.FILE_EXTENSIONS))
        self._include_names.setText(",".join(_cfg.INCLUDE_FILENAMES))
        self._ignore_dirs.setText(",".join(_cfg.IGNORE_DIRS))
        self._chunk_size.setValue(_cfg.CHUNK_SIZE)
        self._chunk_overlap.setValue(_cfg.CHUNK_OVERLAP)

    def _save_config(self) -> None:
        updates = {
            "FILE_EXTENSIONS": self._extensions.text(),
            "INCLUDE_FILENAMES": self._include_names.text(),
            "IGNORE_DIRS": self._ignore_dirs.text(),
            "CHUNK_SIZE": str(self._chunk_size.value()),
            "CHUNK_OVERLAP": str(self._chunk_overlap.value()),
        }
        save_env_vars(updates)

        _cfg.FILE_EXTENSIONS = [
            x.strip() for x in updates["FILE_EXTENSIONS"].split(",") if x.strip()
        ]
        _cfg.INCLUDE_FILENAMES = [
            x.strip() for x in updates["INCLUDE_FILENAMES"].split(",") if x.strip()
        ]
        _cfg.IGNORE_DIRS = [
            x.strip() for x in updates["IGNORE_DIRS"].split(",") if x.strip()
        ]
        _cfg.CHUNK_SIZE = self._chunk_size.value()
        _cfg.CHUNK_OVERLAP = self._chunk_overlap.value()

        self._status.setObjectName("statusSuccess")
        self._status.setText("✓ Configuração de indexação salva com sucesso!")
        self._status.setStyleSheet("")
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

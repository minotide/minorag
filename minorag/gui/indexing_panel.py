"""Painel de configuração de Indexação."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QLineEdit,
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
        self._extensions.textChanged.connect(self._schedule_save)
        self._include_names.textChanged.connect(self._schedule_save)
        self._ignore_dirs.textChanged.connect(self._schedule_save)
        self._chunk_size.valueChanged.connect(self._schedule_save)
        self._chunk_overlap.valueChanged.connect(self._schedule_save)

    def reload_config(self) -> None:
        for w in (self._extensions, self._include_names, self._ignore_dirs,
                  self._chunk_size, self._chunk_overlap):
            w.blockSignals(True)
        self._extensions.setText(",".join(_cfg.FILE_EXTENSIONS))
        self._include_names.setText(",".join(_cfg.INCLUDE_FILENAMES))
        self._ignore_dirs.setText(",".join(_cfg.IGNORE_DIRS))
        self._chunk_size.setValue(_cfg.CHUNK_SIZE)
        self._chunk_overlap.setValue(_cfg.CHUNK_OVERLAP)
        for w in (self._extensions, self._include_names, self._ignore_dirs,
                  self._chunk_size, self._chunk_overlap):
            w.blockSignals(False)

    def _schedule_save(self) -> None:
        self._save_timer.start()

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

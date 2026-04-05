"""
Interface gráfica do minorag usando PySide6.

Janela desktop com chat, painéis de configuração (Git, LLM, Indexação)
e streaming de tokens via QThread.
"""

from minorag.gui.widgets import load_style
from minorag.gui.main_window import MainWindow


def run_gui() -> None:
    """Inicia a aplicação PySide6."""
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyleSheet(load_style())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

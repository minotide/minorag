"""Widgets auxiliares e carregamento de estilo."""

import os

from PySide6.QtWidgets import QFrame, QLabel

_STYLE_PATH = os.path.join(os.path.dirname(__file__), "style.qss")


def load_style() -> str:
    with open(_STYLE_PATH, encoding="utf-8") as f:
        return f.read()


def make_separator() -> QFrame:
    sep = QFrame()
    sep.setObjectName("separator")
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setFixedHeight(1)
    return sep


def make_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    return lbl

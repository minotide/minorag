"""Painel de Chat com streaming de tokens."""

from PySide6.QtCore import QEvent, QObject, Qt, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from minorag.gui.widgets import make_separator
from minorag.gui.workers import QueryWorker


class ChatPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: QueryWorker | None = None
        self._current_answer_label: QLabel | None = None
        self._current_answer_text: str = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Área de mensagens com scroll
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._messages_widget = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._messages_layout.setContentsMargins(24, 24, 24, 24)
        self._messages_layout.setSpacing(16)

        self._empty_label = QLabel(
            "Indexe o código e faça perguntas sobre o projeto.")
        self._empty_label.setObjectName("emptyState")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._messages_layout.addWidget(self._empty_label)

        self._scroll.setWidget(self._messages_widget)
        layout.addWidget(self._scroll, 1)

        # Separador
        layout.addWidget(make_separator())

        # Área de input
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(24, 16, 24, 16)
        input_layout.setSpacing(12)

        self._input = QPlainTextEdit()
        self._input.setPlaceholderText("Faça uma pergunta sobre o código...")
        self._input.setMaximumHeight(120)
        self._input.setFixedHeight(44)
        self._input.installEventFilter(self)

        self._btn_send = QPushButton("Enviar")
        self._btn_send.setObjectName("btnSend")
        self._btn_send.setFixedHeight(44)
        self._btn_send.clicked.connect(self._send_question)

        input_layout.addWidget(self._input, 1)
        input_layout.addWidget(self._btn_send)

        input_container = QWidget()
        input_container.setLayout(input_layout)
        layout.addWidget(input_container)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._input and isinstance(event, QKeyEvent):
            if (event.key() == Qt.Key.Key_Return
                    and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._send_question()
                return True
        return super().eventFilter(obj, event)

    def _add_message(self, text: str, object_name: str) -> QLabel:
        if self._empty_label.isVisible():
            self._empty_label.hide()

        label = QLabel(text)
        label.setObjectName(object_name)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Preferred,
                            QSizePolicy.Policy.Minimum)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        if object_name == "msgUser":
            wrapper.addStretch()
            wrapper.addWidget(label)
            label.setMaximumWidth(700)
        else:
            wrapper.addWidget(label)
            wrapper.addStretch()
            label.setMaximumWidth(700)

        container = QWidget()
        container.setLayout(wrapper)
        self._messages_layout.addWidget(container)

        # Scroll to bottom
        QApplication.processEvents()
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

        return label

    def _send_question(self) -> None:
        question = self._input.toPlainText().strip()
        if not question or self._worker is not None:
            return

        self._input.clear()
        self._input.setFixedHeight(44)
        self._btn_send.setEnabled(False)

        self._add_message(question, "msgUser")
        self._current_answer_label = self._add_message(
            "⏳ Pensando...", "msgBot")
        self._current_answer_text = ""

        self._worker = QueryWorker(question)
        self._worker.log_received.connect(self._on_log)
        self._worker.token_received.connect(self._on_token)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    @Slot(str)
    def _on_log(self, text: str) -> None:
        if self._current_answer_label:
            self._current_answer_label.setText(f"⏳ {text}")

    @Slot(str)
    def _on_token(self, token: str) -> None:
        if self._current_answer_label:
            if self._current_answer_text == "":
                self._current_answer_label.setText("")
            self._current_answer_text += token
            self._current_answer_label.setText(self._current_answer_text)
            # Scroll to bottom
            sb = self._scroll.verticalScrollBar()
            sb.setValue(sb.maximum())

    @Slot(str)
    def _on_error(self, text: str) -> None:
        if self._current_answer_label:
            self._current_answer_label.setObjectName("msgError")
            self._current_answer_label.setStyleSheet(
                "background: #161b22; border: 1px solid #f85149; "
                "padding: 12px 16px; border-radius: 12px; font-size: 14px; color: #f85149;"
            )
            self._current_answer_label.setText(text)

    @Slot()
    def _on_finished(self) -> None:
        self._worker = None
        self._btn_send.setEnabled(True)
        self._input.setFocus()

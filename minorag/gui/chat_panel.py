"""Painel de Chat com streaming de tokens."""

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from minorag.gui.md_renderer import render_md as _render_md
from minorag.gui.widgets import make_separator
from minorag.gui.workers import QueryWorker


class _BotWidget(QWidget):
    """Bolha de resposta do bot com renderização Markdown e botão de cópia."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = ""

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.setMaximumWidth(700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._label = QLabel("⏳ Pensando...")
        self._label.setObjectName("msgBot")
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._label.setOpenExternalLinks(True)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        layout.addWidget(self._label)

        self._btn_copy = QPushButton("⎘  Copiar resposta")
        self._btn_copy.setObjectName("btnCopy")
        self._btn_copy.setVisible(False)
        layout.addWidget(
            self._btn_copy, alignment=Qt.AlignmentFlag.AlignLeft
        )
        self._btn_copy.clicked.connect(self._copy)

    def set_log(self, text: str) -> None:
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setText(f"⏳ {text}")

    def append_token(self, token: str) -> None:
        self._text += token
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setText(self._text)

    def finish(self) -> None:
        if self._text:
            self._label.setTextFormat(Qt.TextFormat.RichText)
            self._label.setText(_render_md(self._text))
        self._btn_copy.setVisible(True)

    def set_error(self, text: str) -> None:
        self._label.setObjectName("msgError")
        self._label.setStyleSheet(
            "background: #161b22; border: 1px solid #f85149; "
            "padding: 12px 16px; border-radius: 12px; font-size: 14px; color: #f85149;"
        )
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setText(text)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self._text)
        self._btn_copy.setText("Copiado!")
        QTimer.singleShot(2000, lambda: self._btn_copy.setText("⎘  Copiar resposta"))


class ChatPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: QueryWorker | None = None
        self._current_bot_widget: _BotWidget | None = None
        self._auto_scroll = True
        self._programmatic_scroll = False

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

        # Detecta scroll manual do usuário
        self._scroll.verticalScrollBar().valueChanged.connect(
            self._on_scroll_value_changed)

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

    @Slot(int)
    def _on_scroll_value_changed(self, value: int) -> None:
        if self._programmatic_scroll:
            return
        sb = self._scroll.verticalScrollBar()
        self._auto_scroll = value >= sb.maximum() - 20

    def _scroll_to_bottom(self) -> None:
        if not self._auto_scroll:
            return
        self._programmatic_scroll = True
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
        self._programmatic_scroll = False

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._input and isinstance(event, QKeyEvent):
            if (event.key() == Qt.Key.Key_Return
                    and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._send_question()
                return True
        return super().eventFilter(obj, event)

    def _add_user_message(self, text: str) -> None:
        if self._empty_label.isVisible():
            self._empty_label.hide()

        label = QLabel(text)
        label.setObjectName("msgUser")
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Preferred,
                            QSizePolicy.Policy.Minimum)
        label.setMaximumWidth(700)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addStretch()
        wrapper.addWidget(label)

        container = QWidget()
        container.setLayout(wrapper)
        self._messages_layout.addWidget(container)

    def _add_bot_widget(self) -> _BotWidget:
        if self._empty_label.isVisible():
            self._empty_label.hide()

        widget = _BotWidget()

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(widget)
        wrapper.addStretch()

        container = QWidget()
        container.setLayout(wrapper)
        self._messages_layout.addWidget(container)

        QApplication.processEvents()
        self._scroll_to_bottom()
        return widget

    def _send_question(self) -> None:
        question = self._input.toPlainText().strip()
        if not question or self._worker is not None:
            return

        self._input.clear()
        self._input.setFixedHeight(44)
        self._btn_send.setEnabled(False)

        # Ao enviar nova pergunta, retoma o scroll automático
        self._auto_scroll = True

        self._add_user_message(question)
        QApplication.processEvents()
        self._scroll_to_bottom()

        self._current_bot_widget = self._add_bot_widget()

        self._worker = QueryWorker(question)
        self._worker.log_received.connect(self._on_log)
        self._worker.token_received.connect(self._on_token)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    @Slot(str)
    def _on_log(self, text: str) -> None:
        if self._current_bot_widget:
            self._current_bot_widget.set_log(text)

    @Slot(str)
    def _on_token(self, token: str) -> None:
        if self._current_bot_widget:
            self._current_bot_widget.append_token(token)
            self._scroll_to_bottom()

    @Slot(str)
    def _on_error(self, text: str) -> None:
        if self._current_bot_widget:
            self._current_bot_widget.set_error(text)

    @Slot()
    def _on_finished(self) -> None:
        if self._current_bot_widget:
            self._current_bot_widget.finish()
        self._worker = None
        self._btn_send.setEnabled(True)
        self._input.setFocus()
        self._scroll_to_bottom()

"""可复用的聊天气泡、工具卡片、推理链与输入控件。"""

from __future__ import annotations

import json

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QFrame,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .locale import tr


def strip_text_blocks(content) -> str:
    """从 LLM 消息的 content blocks（list[dict]）里拼纯文本。"""
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") in ("text", "text-delta"):
            parts.append(str(block.get("text", "")))
        elif block.get("type") == "tool-call":
            name = block.get("name", "")
            args = block.get("arguments", "")
            parts.append(f"[tool call: {name}({args})]")
    return "".join(parts)


class AutoFitTextBrowser(QTextBrowser):
    """随内容自动撑高的 QTextBrowser：不内嵌滚动条，交给外层对话滚动区。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        self.document().setTextWidth(max(width, 40))
        return int(self.document().size().height()) + 2

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setFixedHeight(self.heightForWidth(self.viewport().width()))


class AssistantBubble(QFrame):
    """助手回复气泡：AutoFitTextBrowser 渲染 Markdown，支持流式增量。

    代码块/标题/列表/链接均由 Qt 的 markdown 渲染；链接在外部浏览器打开。
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("assistantBubble")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.browser = AutoFitTextBrowser()
        self.browser.setObjectName("assistantMd")
        self.browser.setOpenExternalLinks(True)
        self.browser.setOpenLinks(True)
        # markdown 代码块/链接的配色（浅色主题）
        self.browser.document().setDefaultStyleSheet(
            "pre { background: #F2F4F7; border-radius: 6px; padding: 8px; }"
            "code { background: #EEF1F6; border-radius: 3px; padding: 1px 3px; }"
            "a { color: #2F6FED; }"
        )
        self.set_markdown(text)
        layout.addWidget(self.browser)

    def set_markdown(self, text: str):
        self.browser.setMarkdown(text)
        self.browser.resize(self.browser.width(), self.browser.heightForWidth(max(self.browser.viewport().width(), 40)))

    def full_text(self) -> str:
        return self.browser.toPlainText()


class MarkdownBubble(QWidget):
    """带左侧对齐包裹的 Markdown 气泡（等同 make_bubble 的助手版）。"""

    def __init__(self, text: str = ""):
        super().__init__()
        self.bubble = AssistantBubble(text)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 2, 0, 2)
        h.addWidget(self.bubble, 0)
        h.addStretch(1)
        self.bubble.setMaximumWidth(720)


def make_bubble(text: str, *, role: str) -> QWidget:
    """构建一个聊天气泡 widget。

    role: 'user' | 'assistant' | 'tool'
    assistant 使用 Markdown 渲染；user 使用纯文本 QLabel。
    """
    if role == "assistant":
        return MarkdownBubble(text)
    bubble = QFrame()
    bubble.setObjectName("userBubble" if role == "user" else "assistantBubble")
    layout = QHBoxLayout(bubble)
    layout.setContentsMargins(14, 10, 14, 10)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setObjectName("userText" if role == "user" else "assistantText")
    layout.addWidget(label)

    wrap = QWidget()
    h = QHBoxLayout(wrap)
    h.setContentsMargins(0, 2, 0, 2)
    if role == "user":
        h.addStretch(1)
        h.addWidget(bubble, 0)
        h.setSpacing(0)
        # 用户气泡宽度上限约 70%
        bubble.setMaximumWidth(560)
    else:
        h.addWidget(bubble, 0)
        h.addStretch(1)
        bubble.setMaximumWidth(680)
    return wrap


class ToolCallCard(QWidget):
    """可展开的工具调用卡片，显示名称、参数、状态、结果。

    状态: pending (蓝色) → running (转圈) → success (绿色) / error (红色)。
    """

    def __init__(self, call_id: str, name: str, arguments: str = "",
                 parent=None):
        super().__init__(parent)
        self._call_id = call_id
        self._name = name
        self._state = "pending"
        self.setObjectName("toolCallCard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)

        # 主卡片区域
        self.card = QFrame()
        self.card.setObjectName("toolCardInner")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(4)

        # 头部：名称 + 状态标签
        header = QHBoxLayout()
        self.status_label = QLabel("待处理")
        self.status_label.setObjectName("toolCardStatus")
        self.name_label = QLabel(name)
        self.name_label.setObjectName("toolCardName")
        header.addWidget(self.name_label, 1)
        header.addWidget(self.status_label, 0)
        card_layout.addLayout(header)

        # 参数（可折叠）
        self.args_toggle = QPushButton("查看参数")
        self.args_toggle.setObjectName("toolCardToggle")
        self.args_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.args_body = QLabel(arguments)
        self.args_body.setObjectName("toolCardArgs")
        self.args_body.setWordWrap(True)
        self.args_body.setVisible(False)
        self.args_toggle.clicked.connect(
            lambda: self.args_body.setVisible(not self.args_body.isVisible()))
        card_layout.addWidget(self.args_toggle)
        card_layout.addWidget(self.args_body)

        # 结果区
        self.result_body = QLabel()
        self.result_body.setObjectName("toolCardResult")
        self.result_body.setWordWrap(True)
        self.result_body.setVisible(False)
        card_layout.addWidget(self.result_body)

        outer.addWidget(self.card)

        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(4, 2, 4, 2)
        h.addWidget(self, 0)
        h.addStretch(1)
        self._wrap = wrap
        self.setMaximumWidth(680)

    def set_pending(self):
        self._state = "pending"
        self.status_label.setText("待处理")
        self.card.setObjectName("toolCardInner")

    def set_running(self):
        self._state = "running"
        self.status_label.setText("进行中")
        self.card.setObjectName("toolCardRunning")

    def set_success(self):
        self._state = "success"
        self.status_label.setText("完成")
        self.card.setObjectName("toolCardSuccess")

    def set_error(self, msg=""):
        self._state = "error"
        self.status_label.setText(f"出错: {msg}")
        self.card.setObjectName("toolCardError")

    def set_result(self, content: str, is_error: bool = False):
        if is_error:
            self.set_error(content)
        else:
            self.set_success()
        snippet = " ".join(content.split())[:200]
        self.result_body.setText(snippet + ("…" if len(content) > 200 else ""))
        self.result_body.setVisible(True)

    @property
    def wrap(self):
        return self._wrap

    @property
    def call_id(self):
        return self._call_id


class ReasoningBlock(QWidget):
    """可折叠的推理链展示。点击 toggle 展开/收起。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("reasoningBlock")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)

        self.card = QFrame()
        self.card.setObjectName("reasoningCard")
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(12, 6, 12, 6)
        cl.setSpacing(4)

        # 头部：图标 + 状态 + toggle
        header = QHBoxLayout()
        self.toggle_btn = QPushButton("思考过程")
        self.toggle_btn.setObjectName("reasoningToggle")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self._on_toggle)
        header.addWidget(self.toggle_btn, 1)
        cl.addLayout(header)

        # 推理内容
        self.body = QTextBrowser()
        self.body.setObjectName("reasoningBody")
        self.body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.body.setVisible(False)
        cl.addWidget(self.body)

        outer.addWidget(self)

        self._text = ""

    def _on_toggle(self, checked: bool):
        self.body.setVisible(checked)

    def append_delta(self, piece: str):
        self._text += piece
        self.body.setPlainText(self._text)
        self.body.setVisible(self.toggle_btn.isChecked())

    def set_final_text(self, text: str):
        self._text = text
        self.body.setPlainText(text)


def make_tool_line(text: str) -> QWidget:
    """工具调用/结果的小字灰行（兼容旧代码）。"""
    wrap = QWidget()
    h = QHBoxLayout(wrap)
    h.setContentsMargins(4, 2, 4, 2)
    label = QLabel(text)
    label.setObjectName("toolLine")
    label.setWordWrap(True)
    h.addWidget(label)
    h.addStretch(1)
    return wrap


class StatusLabel(QLabel):
    """无动画的纯文本状态标签，用颜色区分状态。"""

    STYLES = {
        "green": f"color: #16A34A; font-size: 12px; padding: 4px 12px;",
        "red":   f"color: #DC2626; font-size: 12px; padding: 4px 12px;",
        "gray":  f"color: #9CA3AF; font-size: 12px; padding: 4px 12px;",
        "blue":  f"color: #2F6FED; font-size: 12px; padding: 4px 12px;",
    }

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("statusDot")
        self.set_gray()

    def set_green(self):
        self.setStyleSheet(self.STYLES["green"])

    def set_red(self):
        self.setStyleSheet(self.STYLES["red"])

    def set_gray(self):
        self.setStyleSheet(self.STYLES["gray"])

    def set_blue(self):
        self.setStyleSheet(self.STYLES["blue"])

    def set_text(self, text: str):
        self.setText(text)


class Composer(QWidget):
    """底部输入区: 自动扩展输入框 + 发送按钮。"""

    def __init__(self, on_send, parent=None):
        super().__init__(parent)
        self._on_send = on_send
        self.setObjectName("composer")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 14)
        self.input = QPlainTextEdit()
        self.input.setObjectName("input")
        self.input.setPlaceholderText(tr("input_placeholder"))
        self.input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input.document().contentsChanged.connect(self._auto_resize)
        self._min_h = 42
        self._max_h = 150
        self.input.setFixedHeight(self._min_h)

        self.send_btn = QPushButton(tr("send"))
        self.send_btn.setObjectName("send")
        self.send_btn.setFixedHeight(42)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._emit)
        self.input.installEventFilter(self)

        layout.addWidget(self.input, 1)
        layout.addWidget(self.send_btn, 0)

    def _auto_resize(self):
        doc = self.input.document()
        doc.setTextWidth(self.input.viewport().width())
        h = int(doc.size().height()) + 12
        h = max(self._min_h, min(h, self._max_h))
        self.input.setFixedHeight(h)
        self.send_btn.setFixedHeight(h)

    def _emit(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self._on_send(text)

    def set_enabled(self, enabled: bool):
        self.input.setReadOnly(not enabled)
        self.send_btn.setEnabled(enabled)

    def focus(self):
        self.input.setFocus()

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not (
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            ):
                self._emit()
                return True
        return super().eventFilter(obj, event)
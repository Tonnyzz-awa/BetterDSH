"""BetterDSH 视觉组件库。

从参考设计移植的像素级一致的组件：颜色、字体、Markdown 渲染、矢量图标、
以及 SendButton / Switch / PulseDots / RichText / ThinkBlock / SuggCard /
EmptyState / ConvItem / Sidebar / MessageRow / MessagesArea / ComposerInput /
Toaster。

这里只包含"外观"。与后端 / 设置的接线在 main_window.py 中完成。
所有可见控件都对应真实功能，不含纯装饰件。
"""
from __future__ import annotations

import re
import html
import math
from functools import lru_cache
from datetime import datetime

from PyQt6.QtCore import (
    Qt, QSize, QPointF, QRectF, QTimer, QPropertyAnimation,
    QEasingCurve, pyqtProperty, pyqtSignal, QByteArray,
)
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QPainter, QPixmap, QIcon,
    QFont, QFontMetrics, QImage,
)
from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QAbstractButton, QToolButton,
    QLineEdit, QTextEdit, QTextBrowser, QScrollArea, QVBoxLayout, QHBoxLayout,
    QGridLayout, QStackedLayout, QMenu, QSizePolicy,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
)
from PyQt6.QtSvg import QSvgRenderer

from ui.locale import tr

# ---- 主题 ----
# 两套调色板；dark 为同族深色版。set_theme 把当前调色板写回下面的模块级常量，
# 已有 100+ 处引用（QPainter / markdown 内联样式 / 控件样式表）随之生效，无需逐一改。
_LIGHT = {
    "bg": "#ffffff", "surface": "#f5f5f7", "surface_w": "#fbfbfd",
    "fg": "#1d1d1f", "fg2": "#424245", "muted": "#6e6e73", "meta": "#86868b",
    "border": "#d2d2d7", "border_s": "#e8e8ed", "accent": "#0071e3",
    "accent_h": "#0077ed", "accent_a": "#0066cc", "accent_on": "#ffffff",
    "success": "#16a34a", "danger": "#dc2626", "hover": "#e9e9ee",
}
_DARK = {
    "bg": "#1d1d1f", "surface": "#2c2c2e", "surface_w": "#3a3a3c",
    "fg": "#f5f5f7", "fg2": "#d2d2d7", "muted": "#a1a1a6", "meta": "#8e8e93",
    "border": "#3a3a3c", "border_s": "#48484a", "accent": "#0a84ff",
    "accent_h": "#409cff", "accent_a": "#0066cc", "accent_on": "#ffffff",
    "success": "#30d158", "danger": "#ff453a", "hover": "#3a3a3c",
}
THEME = "light"


def _apply_palette(pal: dict) -> None:
    global BG, SURFACE, SURFACE_W, FG, FG2, MUTED, META, BORDER, BORDER_S, \
        ACCENT, ACCENT_H, ACCENT_A, ACCENT_ON, SUCCESS, DANGER, HOVER
    BG = pal["bg"]; SURFACE = pal["surface"]; SURFACE_W = pal["surface_w"]
    FG = pal["fg"]; FG2 = pal["fg2"]; MUTED = pal["muted"]; META = pal["meta"]
    BORDER = pal["border"]; BORDER_S = pal["border_s"]; ACCENT = pal["accent"]
    ACCENT_H = pal["accent_h"]; ACCENT_A = pal["accent_a"]; ACCENT_ON = pal["accent_on"]
    SUCCESS = pal["success"]; DANGER = pal["danger"]; HOVER = pal["hover"]


def set_theme(name: str) -> None:
    """切换主题（'light' / 'dark'）并刷新模块级常量与 QSS 源。"""
    global THEME, APP_QSS
    THEME = "dark" if name == "dark" else "light"
    _apply_palette(_DARK if THEME == "dark" else _LIGHT)
    APP_QSS = app_qss()


def is_dark() -> bool:
    return THEME == "dark"


def app_qss() -> str:
    """由当前调色板生成全局 QSS。控件在 __init__ 固化配色，切换主题需重建控件。"""
    return f"""
* {{ font-family: 'SF Pro Text', 'Segoe UI', 'Microsoft YaHei UI', 'PingFang SC', sans-serif; }}
QMainWindow, QDialog {{ background: {BG}; }}
QWidget {{ color: {FG}; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; margin: 2px; }}
QScrollBar::handle:vertical:hover {{ background: {META}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QMenu {{ background: {BG}; border: 1px solid {BORDER_S}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 8px 14px; border-radius: 7px; font-size: 13px; color: {FG}; }}
QMenu::item:selected {{ background: {SURFACE}; }}
QMenu::separator {{ height: 1px; background: {BORDER_S}; margin: 4px 8px; }}
QMenu::item:disabled {{ color: {META}; }}

QToolTip {{ background: {FG}; color: {BG}; border: none; padding: 6px 9px; font-size: 12px; }}

QSlider {{ height: 24px; }}
QSlider::groove:horizontal {{ height: 4px; border-radius: 2px; background: {BORDER_S}; }}
QSlider::sub-page:horizontal {{ background: {META}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 18px; height: 18px; margin: -7px 0; border-radius: 9px;
  background: {BG}; border: 1px solid {BORDER}; }}
QSlider::handle:horizontal:hover {{ background: {SURFACE}; }}
QSlider::handle:horizontal:focus {{ border: 2px solid {ACCENT}; }}

QComboBox {{ border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 12px; font-size: 13px;
  background: {BG}; color: {FG}; }}
QComboBox:hover {{ border-color: {META}; }}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: {BG}; border: 1px solid {BORDER_S}; outline: 0;
  selection-background-color: {SURFACE}; selection-color: {FG}; }}

QProgressBar {{ background: {BORDER_S}; border: none; border-radius: 4px; height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {FG}; border-radius: 4px; }}

QLineEdit {{ background: transparent; border: none; font-size: 13px; color: {FG}; }}
QStatusBar {{ background: {SURFACE}; border-top: 1px solid {BORDER_S}; font-size: 12px; color: {MUTED}; }}
QStatusBar::item {{ border: none; }}

QToolButton {{ background: transparent; border: none; border-radius: 8px; padding: 6px; }}
QToolButton:hover {{ background-color: {HOVER}; }}
"""

_apply_palette(_LIGHT)   # 默认 light
APP_QSS = app_qss()

FONT_STACK  = ["SF Pro Text", "Segoe UI", "Microsoft YaHei UI", "PingFang SC", "Helvetica Neue", "sans-serif"]
MONO_STACK  = ["SF Mono", "Consolas", "JetBrains Mono", "Menlo", "Courier New", "monospace"]

@lru_cache(maxsize=None)
def ui_font(px: int, weight: int = 400) -> QFont:
    f = QFont()
    try:
        f.setFamilies(FONT_STACK)
    except TypeError:
        f.setFamily("Segoe UI")
    f.setPointSizeF(px * 0.75)
    f.setWeight(weight)
    return f


def esc(s: str) -> str:
    # 默认转义引号：inline() 在 href 里拼 URL，引号不转义会逃逸属性。
    return html.escape(s)


def inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def _is_fence(l: str) -> bool:
    t = l.strip()
    return t.startswith("```") or t.startswith("~~~")


def md_to_html(src: str) -> str:
    lines = src.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        l = lines[i]
        t = l.strip()
        if _is_fence(l):
            lang = t.lstrip("`~")
            buf = []
            i += 1
            while i < n and not _is_fence(lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(buf)
            head = f'<span style="color:{META}; font-size:10px;">{esc(lang or "code")}</span><br/>'
            out.append(f'<table width="100%" cellspacing="0" cellpadding="10" '
                       f'style="background-color:{SURFACE}; margin-top:6px; margin-bottom:14px;">'
                       f'<tr><td><pre style="font-family:\'SF Mono\',Consolas,monospace; font-size:13px; '
                       f'color:{FG}; white-space:pre-wrap; margin:0;">{head}{esc(code)}</pre></td></tr></table>')
            continue
        if not t:
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", l)
        if m:
            lvl = len(m.group(1))
            size = {1: 24, 2: 20, 3: 17, 4: 15}.get(lvl, 15)
            out.append(f'<p style="font-size:{size}px; font-weight:600; color:{FG}; '
                       f'margin-top:20px; margin-bottom:8px;">{inline(m.group(2))}</p>')
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", l):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append("<li>%s</li>" % inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            out.append('<ul style="margin-top:0; margin-bottom:12px; padding-left:22px;">%s</ul>' % "".join(items))
            continue
        if re.match(r"^\s*\d+\.\s+", l):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append("<li>%s</li>" % inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append('<ol style="margin-top:0; margin-bottom:12px; padding-left:22px;">%s</ol>' % "".join(items))
            continue
        if t.startswith("|"):
            rows = []
            is_head = False
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].split("|")[1:-1]]
                if cells and all(re.match(r"^:?-+:?$", c) for c in cells):
                    is_head = True
                    i += 1
                    continue
                rows.append(cells)
                i += 1
            tbl = '<table cellspacing="0" cellpadding="8" style="margin-bottom:14px;">'
            if is_head and rows:
                tbl += "<tr>" + "".join(f"<th style=\"border:1px solid {BORDER}; background-color:{SURFACE}; "
                                        "font-weight:600; font-size:13px; text-align:left;\">%s</th>" % inline(c)
                                        for c in rows[0]) + "</tr>"
                rows = rows[1:]
            for r in rows:
                tbl += "<tr>" + "".join(f"<td style=\"border:1px solid {BORDER}; font-size:13px; text-align:left;"
                                        " padding:8px 12px;\">%s</td>" % inline(c) for c in r) + "</tr>"
            out.append(tbl + "</table>")
            continue
        if t.startswith(">"):
            quotes = []
            while i < n and lines[i].strip().startswith(">"):
                quotes.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            inner = md_to_html("\n".join(quotes))
            out.append(
                f'<blockquote style="border-left:3px solid {BORDER}; '
                f'margin:0 0 12px; padding:4px 14px; color:{FG2};">{inner}</blockquote>'
            )
            continue
        para = [l]
        i += 1
        while i < n and lines[i].strip() and not _is_fence(lines[i]) \
                and not re.match(r"^(#{1,4})\s", lines[i]) and not lines[i].strip().startswith("|"):
            para.append(lines[i])
            i += 1
        out.append('<p style="margin:0 0 12px; line-height:1.7;">%s</p>' % inline(" ".join(para)))
    return "".join(out)

def _svg_icon(inner, size=18, color=None, *, width=1.7, fill=False):
    """按 webgui 同一套 Feather SVG 渲染图标。

    直接把原始 SVG 字符串交给 QSvgRenderer，圆弧 / 描边与 webgui 像素一致
    （不再手写 path 解析，避免椭圆弧被近似成直线，齿轮 / 回形针不再棱角分明）。
    inner 为 SVG 内部元素（<path/> / <circle/> 等）；颜色注入 stroke / fill。
    """
    if color is None:
        color = MUTED
    stroke = "none" if fill else color
    fill_attr = color if fill else "none"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="{fill_attr}" stroke="{stroke}" stroke-width="{width}" '
        'stroke-linecap="round" stroke-linejoin="round">' + inner + "</svg>"
    )
    dpr = 2.0
    s = int(size * dpr)
    img = QImage(s, s, QImage.Format.Format_ARGB32)
    img.fill(0)
    r = QSvgRenderer()
    r.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
    r.load(QByteArray(svg.encode("utf-8")))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r.render(p, QRectF(0, 0, s, s))
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(dpr)
    return QIcon(pm)


def icon_plus(color=None):
    return _svg_icon('<path d="M12 5v14M5 12h14"/>', color=color or FG)


def icon_search(color=None):
    return _svg_icon('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>',
                     color=color or META)


def icon_close(color=None):
    return _svg_icon('<path d="M6 6l12 12M18 6L6 18"/>', color=color or META)


def icon_gear(color=None):
    # webgui 设置齿轮（Feather settings）
    return _svg_icon(
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06'
        'a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09'
        'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83'
        'l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09'
        'A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83'
        'l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09'
        'a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83'
        'l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09'
        'a1.65 1.65 0 0 0-1.51 1z"/>',
        color=color or META)


def icon_export(color=None):
    # webgui 导出（download）
    return _svg_icon('<path d="M12 3v12M8 11l4 4 4-4M4 20h16"/>', color=color or META)


def icon_sparkle(color=None):
    # webgui 深度思考：双五角星
    return _svg_icon(
        '<path d="M12 3l1.8 4.8L19 9l-5.2 1.2L12 15l-1.8-4.8L5 9l5.2-1.2L12 3z"/>'
        '<path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15z"/>',
        color=color or META)


def icon_attach(color=None):
    # webgui 附件（paperclip）
    return _svg_icon(
        '<path d="M21 12.5l-8.8 8.8a5.5 5.5 0 0 1-7.78-7.78L12 6.15a3.5 3.5 0 0 1 4.95 4.95l-7.5 7.5a1.5 1.5 0 0 1-2.12-2.12l7.07-7.07"/>',
        color=color or META)


class SendButton(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setEnabled(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._busy = False
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._tick)

    def set_busy(self, b):
        self._busy = b
        if b and not self._timer.isActive():
            self._timer.start()
        elif not b:
            self._timer.stop()
        self.update()

    def _tick(self):
        self._phase += 0.7
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._busy:
            bg = QColor(ACCENT_H if self.underMouse() else ACCENT)
            ink = QColor(ACCENT_ON)
        elif not self.isEnabled():
            bg = QColor(BORDER_S)
            ink = QColor(META)
        else:
            bg = QColor(ACCENT_H if self.underMouse() else ACCENT)
            ink = QColor(ACCENT_ON)
        if self.isDown() and self.isEnabled():
            bg = QColor(ACCENT_A)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(r, 12, 12)
        p.setPen(QPen(ink, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self._busy:
            c = self.width() / 2.0
            y = self.height() / 2.0
            for i in range(3):
                a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self._phase + i * 2.1))
                p.setBrush(QColor.fromRgbF(1, 1, 1, a))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(c - 7 + i * 7, y), 2.4, 2.4)
        else:
            x = self.width() / 2.0
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(QPointF(x, self.height() - 10.5), QPointF(x, self.height() / 2.0 - 1.5))
            p.drawLine(QPointF(x - 3.2, self.height() / 2.0 + 1.8), QPointF(x, self.height() / 2.0 - 1.5))
            p.drawLine(QPointF(x + 3.2, self.height() / 2.0 + 1.8), QPointF(x, self.height() / 2.0 - 1.5))
            p.drawLine(QPointF(x - 6, self.height() - 5.5), QPointF(x + 6, self.height() - 5.5))
        p.end()

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return) and self.isEnabled():
            self.click()
        else:
            super().keyPressEvent(ev)


class ReasoningSlider(QWidget):
    """N 段式推理强度滑块，可配置档位列表，可拖动选择。"""
    valueChanged = pyqtSignal(int)

    def __init__(self, levels=None, parent=None):
        super().__init__(parent)
        self._levels = list(levels) if levels else ["off", "medium", "high"]
        self._n = len(self._levels)
        self._value = max(0, self._n // 2)
        self._dragging = False
        self._hover = False
        w = max(100, self._n * 40 + 20)
        self.setFixedSize(w, 38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def levels(self) -> list[str]:
        return self._levels

    def setLevels(self, levels: list[str]):
        self._levels = list(levels)
        self._n = len(self._levels)
        w = max(100, self._n * 40 + 20)
        self.setFixedSize(w, 38)
        self._value = min(self._value, self._n - 1)
        self.update()

    def setValue(self, v):
        v = max(0, min(self._n - 1, int(v)))
        if v != self._value:
            self._value = v
            self.valueChanged.emit(v)
            self.update()

    def value(self):
        return self._value

    def enterEvent(self, ev):
        self._hover = True
        self.update()

    def leaveEvent(self, ev):
        self._hover = False
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 12
        tx0, tx1 = margin, w - margin
        tw = tx1 - tx0
        track_y = 24
        track_h = 4
        n = self._n
        n1 = max(1, n - 1)

        # 标签
        p.setFont(ui_font(10, 500))
        for i in range(n):
            lx = tx0 + (tw / n1) * i
            color = FG if i == self._value else MUTED
            p.setPen(QColor(color))
            lbl = self._levels[i]
            # 短标签居中，长标签用更多空间
            lw = max(40, min(80, len(lbl) * 8))
            p.drawText(QRectF(lx - lw / 2, 1, lw, 18),
                       Qt.AlignmentFlag.AlignHCenter, lbl)

        # 轨道背景
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(BORDER_S))
        p.drawRoundedRect(QRectF(tx0, track_y, tw, track_h), 2, 2)

        # 已填充轨道
        if self._value > 0:
            fill_end = tx0 + (tw / n1) * self._value
            p.setBrush(QColor(ACCENT))
            p.drawRoundedRect(QRectF(tx0, track_y, fill_end - tx0, track_h), 2, 2)

        # 手柄
        hx = tx0 + (tw / n1) * self._value - 8
        hy = track_y - 6
        p.setBrush(QColor(BG))
        p.setPen(QPen(QColor(BORDER), 1.0))
        p.drawEllipse(QRectF(hx, hy, 16, 16))
        if self._hover or self.hasFocus():
            p.setPen(QPen(QColor(ACCENT), 1.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(hx, hy, 16, 16))
        p.end()

    def mousePressEvent(self, ev):
        self._dragging = True
        self._set_from_x(ev.position().x())
        self.setFocus()

    def mouseMoveEvent(self, ev):
        if self._dragging:
            self._set_from_x(ev.position().x())

    def mouseReleaseEvent(self, ev):
        self._dragging = False

    def _set_from_x(self, x):
        margin = 12
        tw = self.width() - margin * 2
        n1 = max(1, self._n - 1)
        ratio = (x - margin) / max(1, tw)
        self.setValue(round(max(0, min(self._n - 1, ratio * n1))))

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Right, Qt.Key.Key_Up):
            self.setValue(self._value + 1)
        elif ev.key() in (Qt.Key.Key_Left, Qt.Key.Key_Down):
            self.setValue(self._value - 1)
        else:
            super().keyPressEvent(ev)


class Switch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(42, 25)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pos = 1.0 if self.isChecked() else 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(lambda v: self._animate(v))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _animate(self, on):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    @pyqtProperty(float)
    def knob(self):
        return self._pos

    @knob.setter
    def knob(self, v):
        self._pos = v
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        r = QRectF(0, 0, self.width(), h)
        bg = QColor(BORDER)
        if self.isChecked():
            bg = QColor(FG)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(r, h / 2, h / 2)
        pad = 3.0
        d = h - pad * 2
        x = pad + self._pos * (self.width() - d - pad * 2)
        p.setBrush(QColor(BG))
        p.drawEllipse(QRectF(x, pad, d, d))
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(ACCENT), 2.0))
            p.drawRoundedRect(r.adjusted(2, 2, -2, -2), h / 2 - 2, h / 2 - 2)
        p.end()


class PulseDots(QWidget):
    def __init__(self, color=MUTED, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._phase = 0.0
        self.setFixedSize(30, 10)
        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._tick)

    def start(self):
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        self._timer.stop()

    def _tick(self):
        self._phase += 0.6
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(3):
            a = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self._phase + i * 2.1))
            p.setBrush(QColor.fromRgbF(self._color.redF(), self._color.greenF(),
                                       self._color.blueF(), a))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(4 + i * 11, 5), 2.8, 2.8)
        p.end()

class RichText(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("QTextBrowser { background: transparent; }")
        self.document().setDocumentMargin(0)
        self.document().setDefaultStyleSheet(
            f"body {{ color: {FG}; }} "
            f"a {{ color: {ACCENT}; text-decoration: none; }} "
            f"code {{ background-color: {SURFACE}; }} "
            "b { font-weight: 600; }"
        )
        self._html = ""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def render(self, src_html):
        if src_html == self._html:
            return
        self._html = src_html
        self.setHtml(src_html)
        self.fit()

    def render_md(self, src_text):
        self.render(md_to_html(src_text))

    def fit(self):
        w = max(80, self.width() - 2)
        doc = self.document()
        doc.setTextWidth(w)
        doc.adjustSize()
        self.setFixedHeight(int(doc.size().height()) + 2)


class ThinkBlock(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._open = True
        self._running = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._head = QWidget(self)
        self._head.setCursor(Qt.CursorShape.PointingHandCursor)
        self._head.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        hl = QHBoxLayout(self._head)
        hl.setContentsMargins(14, 11, 14, 11)
        hl.setSpacing(8)
        self._spark = QLabel(self._head)
        self._spark.setPixmap(icon_sparkle(color=FG2).pixmap(15, 15))
        self._label = QLabel(tr("thinking_done"), self._head)
        self._label.setStyleSheet(f"font-size:13px; color:{FG2}; font-weight:500; border:none;")
        self._dots = PulseDots(color=MUTED, parent=self._head)
        self._dots.hide()
        self._chev = QLabel("▾", self._head)
        self._chev.setStyleSheet(f"font-size:12px; color:{META}; border:none;")
        hl.addWidget(self._spark)
        hl.addWidget(self._label)
        hl.addWidget(self._dots)
        hl.addStretch(1)
        hl.addWidget(self._chev)

        self._body = QLabel(self)
        self._body.setWordWrap(True)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._body.setStyleSheet(
            f"QLabel {{ background-color:{SURFACE}; border-radius:10px; color:{MUTED}; "
            "font-size:13px; line-height:150%; padding:12px 14px; }")
        self._body.setContentsMargins(0, 0, 0, 10)

        lay.addWidget(self._head)
        lay.addWidget(self._body)

        self._head.mousePressEvent = lambda e: self._toggle()
        self._head.keyPressEvent = self._on_key

        shell = QGraphicsDropShadowEffect(self)
        shell.setBlurRadius(0)
        shell.setOffset(0, 0)
        shell.setColor(QColor(BORDER))
        self.setGraphicsEffect(shell)

        self._reflow()

    def _on_key(self, ev):
        if ev.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Space):
            self._toggle()
        else:
            QWidget.keyPressEvent(self._head, ev)

    def _toggle(self):
        self._open = not self._open
        self.toggled.emit(self._open)
        self._reflow()

    def _reflow(self):
        self._body.setVisible(self._open)
        self._chev.setText("▴" if self._open else "▾")

    def set_running(self, run):
        self._running = run
        if run:
            self._label.setText(tr("thinking_running"))
            self._dots.show()
            self._dots.start()
            if not self._open:
                self._open = True
                self._reflow()
        else:
            self._label.setText(tr("thinking_done"))
            self._dots.stop()
            self._dots.hide()

    def is_running(self):
        return self._running

    def set_text(self, text):
        self._body.setText(text if text else "…")
        self._body.adjustSize()

    def set_open(self, on):
        if self._open != on:
            self._open = on
            self._reflow()


class ToolCallCard(QWidget):
    """可折叠的工具调用卡片：显示工具名、参数、结果与状态。

    与 ThinkBlock 同构：点击头部展开/收起。状态用彩色圆点 + 文字标识
    运行中/已完成/出错。call_id 用于把 tool/call 与 tool/result 配对。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._open = True
        self._status = "running"  # running | success | error
        self._call_id = ""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(0)

        self._head = QWidget(self)
        self._head.setCursor(Qt.CursorShape.PointingHandCursor)
        self._head.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        hl = QHBoxLayout(self._head)
        hl.setContentsMargins(12, 9, 12, 9)
        hl.setSpacing(8)
        self._dot = QLabel(self._head)
        self._dot.setFixedSize(8, 8)
        self._dot.setStyleSheet(f"border-radius:4px; background:{META};")
        self._name = QLabel("tool", self._head)
        self._name.setStyleSheet(f"font-size:13px; color:{FG2}; font-weight:600; border:none;")
        self._status_lbl = QLabel(tr("tool_running"), self._head)
        self._status_lbl.setStyleSheet(f"font-size:12px; color:{META}; border:none;")
        self._chev = QLabel("▾", self._head)
        self._chev.setStyleSheet(f"font-size:12px; color:{META}; border:none;")
        hl.addWidget(self._dot)
        hl.addWidget(self._name)
        hl.addWidget(self._status_lbl)
        hl.addStretch(1)
        hl.addWidget(self._chev)

        self._body = QWidget(self)
        self._body.setStyleSheet(
            f"QWidget#toolBody {{ background-color:{SURFACE}; border:1px solid {BORDER_S}; "
            f"border-radius:10px; }}")
        self._body.setObjectName("toolBody")
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(14, 10, 14, 10)
        bl.setSpacing(8)

        self._args_lbl = QLabel(self._body)
        self._args_lbl.setWordWrap(True)
        self._args_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._args_lbl.setFont(QFont("Anthropic Mono", 12))
        self._args_lbl.setStyleSheet(
            f"QLabel {{ font-size:12px; color:{FG2}; border:none; }}")
        self._args_wrap = QWidget(self._body)
        al = QVBoxLayout(self._args_wrap)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(2)
        self._args_title = QLabel(tr("tool_args"), self._args_wrap)
        self._args_title.setStyleSheet(f"font-size:11px; color:{META}; border:none;")
        al.addWidget(self._args_title)
        al.addWidget(self._args_lbl)
        self._args_wrap.hide()

        self._result_lbl = QLabel(self._body)
        self._result_lbl.setWordWrap(True)
        self._result_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._result_lbl.setStyleSheet(f"font-size:12px; color:{MUTED}; border:none;")
        self._result_wrap = QWidget(self._body)
        rl = QVBoxLayout(self._result_wrap)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(2)
        self._result_title = QLabel(tr("tool_output"), self._result_wrap)
        self._result_title.setStyleSheet(f"font-size:11px; color:{META}; border:none;")
        rl.addWidget(self._result_title)
        rl.addWidget(self._result_lbl)
        self._result_wrap.hide()

        bl.addWidget(self._args_wrap)
        bl.addWidget(self._result_wrap)

        lay.addWidget(self._head)
        lay.addWidget(self._body)
        self._head.mousePressEvent = lambda e: self._toggle()
        self._head.keyPressEvent = self._on_key
        self._reflow()

    def _on_key(self, ev):
        if ev.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Space):
            self._toggle()
        else:
            QWidget.keyPressEvent(self._head, ev)

    def _toggle(self):
        self._open = not self._open
        self._reflow()

    def _reflow(self):
        self._body.setVisible(self._open)
        self._chev.setText("▴" if self._open else "▾")

    def set_name(self, name: str):
        self._name.setText(name or "?")

    def set_args(self, args: str):
        if args and args.strip():
            self._args_lbl.setText(args)
            self._args_wrap.show()
        else:
            self._args_wrap.hide()

    def set_result(self, text: str):
        if text and text.strip():
            self._result_lbl.setText(text)
            self._result_wrap.show()
        else:
            self._result_wrap.hide()

    def set_running(self):
        self._status = "running"
        self._status_lbl.setText(tr("tool_running"))
        self._status_lbl.setStyleSheet(f"font-size:12px; color:{META}; border:none;")
        self._dot.setStyleSheet(f"border-radius:4px; background:{META};")

    def set_success(self):
        self._status = "success"
        self._status_lbl.setText(tr("tool_done"))
        self._status_lbl.setStyleSheet(f"font-size:12px; color:{SUCCESS}; border:none;")
        self._dot.setStyleSheet(f"border-radius:4px; background:{SUCCESS};")

    def set_error(self):
        self._status = "error"
        self._status_lbl.setText(tr("tool_failed"))
        self._status_lbl.setStyleSheet(f"font-size:12px; color:{DANGER}; border:none;")
        self._dot.setStyleSheet(f"border-radius:4px; background:{DANGER};")
        self._result_lbl.setStyleSheet(f"font-size:12px; color:{DANGER}; border:none;")

    @property
    def call_id(self) -> str:
        return self._call_id

    @call_id.setter
    def call_id(self, cid: str):
        self._call_id = cid or ""

    def set_open(self, on: bool):
        if self._open != on:
            self._open = on
            self._reflow()


class EmptyState(QWidget):
    promptClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(0)
        lay.addStretch(3)

        self._greet = QLabel("", self)
        self._greet.setStyleSheet("font-size:34px; font-weight:600; background:transparent;")
        self._greet.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._greet)

        self._sub = QLabel("", self)
        self._sub.setStyleSheet(f"font-size:16px; color:{MUTED}; background:transparent;")
        self._sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(14)
        lay.addWidget(self._sub)
        lay.addStretch(4)

    def set_greeting(self, text):
        self._greet.setText(text)

    def apply_lang(self):
        self._greet.setText(f"{greeting()}，{tr('empty_greet')}")
        self._sub.setText(tr("empty_sub"))


class ConvItem(QFrame):
    clicked = pyqtSignal(str)
    renameRequested = pyqtSignal(str)
    deleteRequested = pyqtSignal(str)

    def __init__(self, conv_id, title, time, active, parent=None):
        super().__init__(parent)
        self._id = conv_id
        self._title = title
        self._time = time
        self._active = active
        self._hover = False
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._id)

    def contextMenuEvent(self, ev):
        menu = QMenu(self)
        rn = menu.addAction(tr("session_rename"))
        dl = menu.addAction(tr("session_delete"))
        act = menu.exec(ev.globalPosition().toPoint())
        if act == rn:
            self.renameRequested.emit(self._id)
        elif act == dl:
            self.deleteRequested.emit(self._id)

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Space):
            self.clicked.emit(self._id)
        else:
            super().keyPressEvent(ev)

    def enterEvent(self, ev):
        self._hover = True
        self.update()

    def leaveEvent(self, ev):
        self._hover = False
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(4, 2, self.width() - 8, self.height() - 4)
        if self._active:
            p.setPen(QPen(QColor(BORDER), 1.0))
            p.setBrush(QColor(BG))
        elif self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(HOVER))
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 10, 10)
        fm = QFontMetrics(ui_font(14, 500))
        tw = self.width() - 16 - 62
        title = fm.elidedText(self._title, Qt.TextElideMode.ElideRight, tw)
        p.setPen(QColor(FG))
        p.setFont(ui_font(14, 500))
        p.drawText(QRectF(16, 0, tw, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title)
        p.setFont(ui_font(11, 400))
        p.setPen(QColor(MUTED))
        p.drawText(QRectF(self.width() - 66, 0, 52, self.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self._time)
        if self.hasFocus():
            p.setPen(QPen(QColor(ACCENT), 1.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 10, 10)
        p.end()

class Sidebar(QWidget):
    newChatRequested = pyqtSignal()
    convSelected = pyqtSignal(str)
    renameRequested = pyqtSignal(str)
    deleteRequested = pyqtSignal(str)
    settingsRequested = pyqtSignal()
    searchChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setObjectName("sidebar")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        head = QWidget(self)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(18, 18, 14, 10)
        hl.setSpacing(10)
        self._mark = QLabel("DS", head)
        self._mark.setFixedSize(30, 30)
        self._mark.setStyleSheet(
            f"QLabel {{ background-color:{FG}; color:{BG}; border-radius:9px; "
            "font-size:13px; font-weight:600; }")
        self._mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_box = QVBoxLayout()
        name_box.setSpacing(0)
        self._nm = QLabel("BetterDSH", head)
        self._nm.setStyleSheet(f"font-size:18px; font-weight:600; color:{FG}; background:transparent;")
        sub = QLabel("DEEPSEEK HARNESS", head)
        sub.setStyleSheet(f"font-size:10px; color:{MUTED}; background:transparent;")
        name_box.addWidget(self._nm)
        name_box.addWidget(sub)
        hl.addWidget(self._mark)
        hl.addLayout(name_box)
        hl.addStretch(1)
        lay.addWidget(head)

        self._new_btn = QPushButton(f"  {tr('new_chat')}", self)
        self._new_btn.setIcon(icon_plus(color=ACCENT_ON))
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._new_btn.setStyleSheet(
            f"QPushButton {{ background-color:{FG}; color:{BG}; border:none; border-radius:12px; "
            "padding:12px 14px; font-size:14px; font-weight:500; text-align:left; }"
            f"QPushButton:hover {{ background-color:#3a3a3c; }}"
            f"QPushButton:pressed {{ background-color:#2a2a2c; }}")
        self._new_btn.clicked.connect(self.newChatRequested)
        lay.addSpacing(6)
        lay.addWidget(self._new_btn, 0, Qt.AlignmentFlag.AlignTop)
        lay.addSpacing(12)

        search_box = QWidget(self)
        search_box.setStyleSheet(
            f"QWidget {{ background-color:transparent; border:1px solid {BORDER}; border-radius:10px; }}")
        sh = QHBoxLayout(search_box)
        sh.setContentsMargins(11, 9, 11, 9)
        sh.setSpacing(8)
        self._search_icon = QLabel(search_box)
        self._search_icon.setPixmap(icon_search().pixmap(15, 15))
        self._search = QLineEdit(search_box)
        self._search.setStyleSheet(f"QLineEdit {{ font-size:13px; color:{FG}; background:transparent; border:none; }}")
        self._search.setPlaceholderText(tr("search"))
        self._search.textChanged.connect(self.searchChanged.emit)
        sh.addWidget(self._search_icon)
        sh.addWidget(self._search)
        lay.addWidget(search_box, 0, Qt.AlignmentFlag.AlignTop)
        lay.addSpacing(10)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_host = QWidget(scroll)
        self._list_host.setStyleSheet("background:transparent;")
        self._list = QVBoxLayout(self._list_host)
        self._list.setContentsMargins(12, 4, 12, 8)
        self._list.setSpacing(2)
        self._list.addStretch(1)
        scroll.setWidget(self._list_host)
        lay.addWidget(scroll, 1)

        # 底部：状态点 + 文字 + 设置齿轮
        foot = QWidget(self)
        foot.setObjectName("sideFooter")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(18, 12, 12, 12)
        fl.setSpacing(10)
        self._dot = QLabel("●", foot)
        self._dot.setFixedWidth(14)
        self._dot.setStyleSheet("color:#86868b; font-size:11px; background:transparent;")
        meta = QVBoxLayout()
        meta.setSpacing(1)
        self._foot_title = QLabel("本地用户", foot)
        self._foot_title.setStyleSheet(f"font-size:13px; font-weight:600; color:{FG}; background:transparent;")
        self._foot_status = QLabel("未连接", foot)
        self._foot_status.setStyleSheet(f"font-size:11px; color:{MUTED}; background:transparent;")
        meta.addWidget(self._foot_title)
        meta.addWidget(self._foot_status)
        self._gear = QToolButton(foot)
        self._gear.setIcon(icon_gear())
        self._gear.setIconSize(QSize(18, 18))
        self._gear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gear.setStyleSheet(
            "QToolButton { background:transparent; border:none; border-radius:8px; padding:8px; }"
            f"QToolButton:hover {{ background-color:{HOVER}; }}")
        self._gear.clicked.connect(self.settingsRequested)
        fl.addWidget(self._dot)
        fl.addLayout(meta, 1)
        fl.addWidget(self._gear)
        lay.addWidget(foot)

    def set_status(self, color: str, text: str):
        self._dot.setStyleSheet(f"color:{color}; font-size:11px; background:transparent;")
        self._foot_status.setText(text)

    def clear_search(self):
        self._search.blockSignals(True)
        self._search.clear()
        self._search.blockSignals(False)

    def render(self, convs, active_id, query=""):
        while self._list.count():
            item = self._list.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        q = query.strip().lower()
        groups = []
        for c in convs:
            if q and q not in c["title"].lower():
                continue
            if c["group"] not in groups:
                groups.append(c["group"])
        for g in groups:
            if not q:
                lbl = QLabel(g, self._list_host)
                lbl.setStyleSheet(f"font-size:10px; font-weight:600; color:{MUTED}; padding:14px 6px 4px 6px; background:transparent;")
                self._list.addWidget(lbl)
            for c in convs:
                if c["group"] != g:
                    continue
                if q and q not in c["title"].lower():
                    continue
                item = ConvItem(c["id"], c["title"], c["time"], c["id"] == active_id, self._list_host)
                item.clicked.connect(self.convSelected)
                item.renameRequested.connect(self.renameRequested)
                item.deleteRequested.connect(self.deleteRequested)
                self._list.addWidget(item)
        self._list.addStretch(1)

class MessageRow(QWidget):
    def __init__(self, role, name, stamp, model_tag=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._role = role
        self._name = name
        self._model_tag = model_tag
        lay = QHBoxLayout(self)
        lay.setContentsMargins(40, 28, 40, 28)
        lay.setSpacing(16)

        self._av = QLabel(self)
        self._av.setFixedSize(34, 34)
        self._av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._av.setText(tr("me") if role == "u" else "DS")
        self._av.setStyleSheet(
            f"QLabel {{ background-color:{BORDER_S if role == 'u' else FG}; "
            f"color:{FG2 if role == 'u' else BG}; border-radius:{17 if role == 'u' else 10}px; "
            "font-size:13px; font-weight:600; }")
        lay.addWidget(self._av, 0, Qt.AlignmentFlag.AlignTop)

        body = QVBoxLayout()
        body.setSpacing(10)
        meta = QHBoxLayout()
        meta.setSpacing(9)
        self._nm = QLabel(name, self)
        self._nm.setObjectName("rowName")
        meta.addWidget(self._nm)
        if model_tag:
            self._tg = QLabel(model_tag, self)
            self._tg.setObjectName("rowModelTag")
            meta.addWidget(self._tg)
        self._st = QLabel(stamp, self)
        self._st.setObjectName("rowStamp")
        meta.addWidget(self._st)
        meta.addStretch(1)
        body.addLayout(meta)

        self.content = QVBoxLayout()
        self.content.setSpacing(10)
        body.addLayout(self.content)
        body.addStretch(1)
        lay.addLayout(body, 1)

    def add_widget(self, w):
        self.content.addWidget(w)


class MessagesArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"QScrollArea {{ background: {BG}; border: none; }}")
        self.viewport().setStyleSheet(f"background: {BG}; border: none;")
        self._host = QWidget(self)
        self._stack = QStackedLayout(self._host)
        self._host.setLayout(self._stack)
        self.setWidget(self._host)

        self._empty = EmptyState(self._host)
        self._stack.addWidget(self._empty)

        self._conv_host = QWidget(self._host)
        self._conv_layout = QVBoxLayout(self._conv_host)
        self._conv_layout.setContentsMargins(0, 0, 0, 0)
        self._conv_layout.setSpacing(0)
        self._conv_layout.addStretch(1)
        self._conv_host.setLayout(self._conv_layout)
        self._stack.addWidget(self._conv_host)

        self._rows = []
        self._scroll_pending = False

    def empty_state(self):
        return self._empty

    def show_empty(self):
        self._stack.setCurrentWidget(self._empty)

    def show_conv(self):
        self._stack.setCurrentWidget(self._conv_host)

    def clear(self):
        for w in self._rows:
            w.deleteLater()
        self._rows = []

    def add_row(self, row):
        self._conv_layout.insertWidget(self._conv_layout.count() - 1, row)
        self._rows.append(row)

    def last_row(self):
        return self._rows[-1] if self._rows else None

    def scroll_bottom(self):
        if self._scroll_pending:
            return
        self._scroll_pending = True
        QTimer.singleShot(0, self._do_scroll)

    def _do_scroll(self):
        self._scroll_pending = False
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        for row in self._rows:
            for i in range(row.content.count()):
                w = row.content.itemAt(i).widget()
                if isinstance(w, RichText):
                    w.fit()


class ComposerInput(QTextEdit):
    submitRequested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(tr("input_placeholder"))
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(44)
        self.document().setDocumentMargin(0)
        self.textChanged.connect(self._autosize)
        self.setStyleSheet(
            f"QTextEdit {{ background:transparent; border:none; font-size:16px; color:{FG}; }}"
            f"QTextEdit::placeholder {{ color:{META}; }}")

    def _autosize(self):
        doc = self.document()
        doc.setTextWidth(max(80, self.viewport().width()))
        h = int(doc.size().height()) + 6
        self.setFixedHeight(min(max(h, 44), 190))
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._autosize()

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return) and not (
                ev.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            text = self.toPlainText().strip()
            if text:
                self.submitRequested.emit(text)
                self.clear()
            ev.accept()
            return
        super().keyPressEvent(ev)


class Toaster(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(3200)
        self._hide_timer.timeout.connect(self._fade_out)
        self.hide()

    def show_text(self, text):
        self.setStyleSheet(
            f"QLabel {{ background-color:{SURFACE_W}; border:1px solid {BORDER_S}; border-radius:12px; "
            f"padding:12px 16px; font-size:13px; color:{FG2}; }}")
        self.setText(text)
        self.adjustSize()
        parent = self.parentWidget()
        if parent is not None:
            self.move(parent.width() - self.width() - 20, 16)
            self.resize(self.width(), self.height())
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._hide_timer.start()

    def _fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()
        try:
            self._anim.finished.disconnect(self.hide)
        except TypeError:
            pass
        self._anim.finished.connect(self.hide)


def now_stamp():
    return datetime.now().strftime("%H:%M")


def greeting():
    h = datetime.now().hour
    if h < 6:
        return tr("greet_dawn")
    if h < 12:
        return tr("greet_morning")
    if h < 14:
        return tr("greet_noon")
    if h < 18:
        return tr("greet_afternoon")
    return tr("greet_evening")


def trim_title(t):
    s = re.sub(r"[`*_#|]", "", t.strip())
    s = re.sub(r"\s+", " ", s)
    return (s[:22] + "…") if len(s) > 22 else (s or "新对话")








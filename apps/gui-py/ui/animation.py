"""非线性动画系统：缓动曲线、弹性动画、入场过渡。

配合 QPropertyAnimation 使用，提供以下效果：
- 侧栏展开/折叠：回弹缓动（QElasticCurve）
- 消息气泡入场：淡入 + 上移（QAnimationGroup + 渐出缓动）
- 按钮悬停：弹性缩放
- 设置面板：淡入弹出
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QParallelAnimationGroup, QPoint, QAbstractAnimation

# 缓动曲线常量
EASE_OUT_BACK = QEasingCurve.Type.OutBack       # 回弹，用于侧栏
EASE_OUT_CUBIC = QEasingCurve.Type.OutCubic      # 平滑渐出，用于消息
EASE_OUT_ELASTIC = QEasingCurve.Type.OutElastic   # 弹性，用于按钮
EASE_IN_OUT_QUINT = QEasingCurve.Type.InOutQuint  # 先慢后慢，用于面板
EASE_OUT_EXPO = QEasingCurve.Type.OutExpo         # 指数渐出，用于入场


def animate_sidebar(sidebar, collapsed: bool, *, duration: int = 300):
    """侧栏展开/收起动画（OutBack 回弹）。

    Args:
        sidebar: 侧栏 QWidget
        collapsed: 是否折叠
        duration: 动画时长（毫秒）
    Returns:
        QPropertyAnimation
    """
    anim = QPropertyAnimation(sidebar, b"minimumWidth")
    anim.setDuration(duration)
    anim.setStartValue(sidebar.width())
    anim.setEndValue(44 if collapsed else 260)
    anim.setEasingCurve(QEasingCurve.Type.OutBack)
    anim.start()
    return anim


def animate_message_bubble(widget, *, duration: int = 250, dy: int = 12):
    """消息气泡入场动画：淡入 + 上移。

    Args:
        widget: 气泡 QWidget
        duration: 动画时长（毫秒）
        dy: 上移距离（像素）
    Returns:
        QParallelAnimationGroup
    """
    group = QParallelAnimationGroup()

    # 位置动画：从下方滑入
    pos = QPropertyAnimation(widget, b"pos")
    start_pos = widget.pos() + QPoint(0, dy)
    pos.setStartValue(start_pos)
    pos.setEndValue(widget.pos())
    pos.setDuration(duration)
    pos.setEasingCurve(EASE_OUT_CUBIC)
    group.addAnimation(pos)

    # 透明度动画：淡入（需要窗口透明度支持）
    opacity = QPropertyAnimation(widget, b"windowOpacity")
    opacity.setStartValue(0.0)
    opacity.setEndValue(1.0)
    opacity.setDuration(duration)
    opacity.setEasingCurve(EASE_OUT_EXPO)
    group.addAnimation(opacity)

    group.start()
    return group


def animate_entrance(widget, *, duration: int = 200):
    """控件入场淡入动画。

    Args:
        widget: 目标 QWidget
        duration: 动画时长（毫秒）
    Returns:
        QPropertyAnimation
    """
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(EASE_OUT_CUBIC)
    anim.start()
    return anim


def animate_button_hover(button, hovered: bool, *, duration: int = 150):
    """按钮悬停弹性缩放。

    Args:
        button: QPushButton
        hovered: 是否悬停
        duration: 动画时长（毫秒）
    Returns:
        QPropertyAnimation
    """
    target = 1.05 if hovered else 1.0
    anim = QPropertyAnimation(button, b"scale")
    anim.setDuration(duration)
    anim.setStartValue(button.property("scale") or 1.0)
    anim.setEndValue(target)
    anim.setEasingCurve(EASE_OUT_ELASTIC)
    anim.start()
    return anim


def animate_fade_in(widget, *, duration: int = 200):
    """淡入动画（用于弹出面板/对话框）。

    Args:
        widget: 目标 QWidget
        duration: 动画时长（毫秒）
    Returns:
        QPropertyAnimation
    """
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(EASE_IN_OUT_QUINT)
    anim.start()
    return anim


def animate_sidebar_content(sidebar, children_widgets: list, collapsed: bool, *, duration: int = 250):
    """侧栏内容动画：折叠时淡出子控件，展开时淡入。

    Args:
        sidebar: 侧栏 QWidget
        children_widgets: 需要动画的子控件列表
        collapsed: 是否折叠
        duration: 动画时长（毫秒）
    Returns:
        list[QPropertyAnimation]
    """
    anims = []
    for w in children_widgets:
        if collapsed:
            w.setVisible(False)
        else:
            w.setVisible(True)
            a = animate_entrance(w, duration=duration)
            anims.append(a)
    return anims
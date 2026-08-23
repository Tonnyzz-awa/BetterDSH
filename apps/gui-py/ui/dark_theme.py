"""深色简洁主题：深底、蓝强调、护眼耐看。"""

BG_0 = "#111318"
BG_1 = "#1A1D23"
BG_2 = "#24272E"
BORDER = "#333842"
TEXT_0 = "#E4E7ED"
TEXT_1 = "#9CA3AF"
TEXT_2 = "#6B7280"
ACCENT = "#5B8EF4"
ACCENT_SOFT = "#1E2A4A"
BUBBLE_USER = "#2F6FED"
BUBBLE_USER_TEXT = "#FFFFFF"
BUBBLE_ASSISTANT = "#24272E"
BUBBLE_ASSISTANT_TEXT = "#E4E7ED"
TOOL_LINE = "#888888"
FONT_FAMILY = '"Segoe UI", "Microsoft YaHei", sans-serif'

DARK_QSS = f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 14px;
    color: {TEXT_0};
}}

QMainWindow, QWidget#root {{
    background: {BG_0};
}}

QWidget#sidebar {{
    background: {BG_1};
    border-right: 1px solid {BORDER};
}}

QLabel#brand {{
    font-size: 17px; font-weight: 600;
    padding: 18px 16px 4px 16px; color: {TEXT_0};
}}

QPushButton#newChat {{
    background: {ACCENT}; color: #FFFFFF;
    border: none; border-radius: 8px; padding: 9px 16px;
    margin: 6px 12px 10px 12px; font-weight: 600;
}}
QPushButton#newChat:hover {{ background: #4A7DE0; }}

QPlainTextEdit#searchEdit {{
    background: {BG_2}; border: 1px solid {BORDER};
    border-radius: 6px; margin: 4px 12px; padding: 2px 8px;
    color: {TEXT_1}; font-size: 12px;
}}

QListWidget#history {{
    background: transparent; border: none; outline: none; font-size: 13px;
}}
QListWidget#history::item {{
    border-radius: 6px; margin: 2px 8px; padding: 8px 12px; color: {TEXT_1};
}}
QListWidget#history::item:hover {{ background: {ACCENT_SOFT}; color: {TEXT_0}; }}
QListWidget#history::item:selected {{
    background: {ACCENT_SOFT}; color: {ACCENT}; font-weight: 600;
}}

QPushButton#settingsButton, QPushButton#runtimeToggle, QPushButton#themeToggle {{
    background: transparent; border: 1px solid {BORDER};
    border-radius: 6px; padding: 7px 12px; margin: 4px 12px;
    color: {TEXT_1}; font-size: 13px;
}}
QPushButton#settingsButton:hover, QPushButton#runtimeToggle:hover,
QPushButton#themeToggle:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}

QPushButton#toggleSidebar {{
    background: transparent; border: none; color: {TEXT_2};
    font-size: 12px; padding: 6px;
}}
QPushButton#toggleSidebar:hover {{ color: {ACCENT}; }}

QLabel#statusDot {{ font-size: 12px; padding: 2px 12px 4px 12px; color: {TEXT_2}; }}

QWidget#chatHeader {{
    background: {BG_1}; border-bottom: 1px solid {BORDER};
}}
QLabel#chatTitle {{
    font-size: 15px; font-weight: 600; padding: 12px 20px 2px; color: {TEXT_0};
}}
QLabel#chatSubtitle {{
    font-size: 12px; color: {TEXT_1}; padding: 0 20px 10px;
}}

QProgressBar#contextMeter, QProgressBar#contextMeterWarn {{
    background: {BG_2}; border: none; border-radius: 2px;
    margin: 0 20px; max-height: 4px;
}}
QProgressBar#contextMeter::chunk {{ background: {ACCENT}; }}
QProgressBar#contextMeterWarn::chunk {{ background: #F59E0B; }}

QScrollArea#messageScroll {{ background: transparent; border: none; }}
QWidget#messageHost {{ background: transparent; }}

QFrame#userBubble {{
    background: {BUBBLE_USER}; border: none; border-radius: 14px;
}}
QLabel#userText {{ color: {BUBBLE_USER_TEXT}; font-size: 14px; }}

QFrame#assistantBubble {{
    background: {BUBBLE_ASSISTANT}; border: none; border-radius: 14px;
}}
QLabel#assistantText {{ color: {BUBBLE_ASSISTANT_TEXT}; font-size: 14px; }}

QTextBrowser#assistantMd {{
    background: transparent; border: none; color: {BUBBLE_ASSISTANT_TEXT}; font-size: 14px;
}}

QLabel#toolLine {{ color: {TOOL_LINE}; font-size: 12px; padding: 2px 0; }}

QFrame#toolCardInner, QFrame#toolCardSuccess {{
    background: {BG_2}; border: 1px solid {BORDER}; border-radius: 8px;
}}
QFrame#toolCardRunning {{
    background: {ACCENT_SOFT}; border: 1px solid {ACCENT}; border-radius: 8px;
}}
QFrame#toolCardError {{
    background: #2D1B1B; border: 1px solid #7F1D1D; border-radius: 8px;
}}
QLabel#toolCardName {{ font-size: 13px; font-weight: 600; color: {TEXT_0}; }}
QLabel#toolCardStatus {{ font-size: 12px; color: {TEXT_2}; }}
QPushButton#toolCardToggle {{
    background: transparent; border: none; color: {ACCENT}; font-size: 12px; padding: 0; text-align: left;
}}
QLabel#toolCardArgs, QLabel#toolCardResult {{ font-size: 12px; color: {TEXT_1}; padding: 4px 0; }}

QFrame#reasoningCard {{
    background: {BG_2}; border: 1px solid {BORDER}; border-radius: 8px;
}}
QPushButton#reasoningToggle {{
    background: transparent; border: none; color: {TEXT_2}; font-size: 12px; font-weight: 600; padding: 0; text-align: left;
}}
QPushButton#reasoningToggle:checked {{ color: {ACCENT}; }}
QTextBrowser#reasoningBody {{
    background: transparent; border: none; color: {TEXT_1}; font-size: 12px;
    font-family: "Consolas", "Courier New", monospace;
}}

QWidget#composer {{
    background: {BG_1}; border-top: 1px solid {BORDER};
}}
QTextEdit#input {{
    background: {BG_2}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 9px 14px; font-size: 14px; color: {TEXT_0};
}}
QTextEdit#input:focus {{ border-color: {ACCENT}; }}
QPushButton#send {{
    background: {ACCENT}; border: none; border-radius: 10px; padding: 9px 18px;
    color: #FFFFFF; font-weight: 600;
}}
QPushButton#send:hover {{ background: #4A7DE0; }}

QStatusBar {{
    background: {BG_1}; border-top: 1px solid {BORDER};
    font-size: 12px; color: {TEXT_1};
}}

QDialog {{
    background: {BG_1};
}}
QDialog QLabel {{ color: {TEXT_0}; font-size: 13px; }}
QDialog QLabel#hintLabel {{ color: {TEXT_2}; font-size: 12px; }}

QComboBox#settingCombo, QLineEdit#settingEdit {{
    background: {BG_2}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 10px; color: {TEXT_0};
    selection-background-color: {ACCENT}; selection-color: #FFFFFF;
}}
QComboBox#settingCombo:focus, QLineEdit#settingEdit:focus {{ border-color: {ACCENT}; }}
QComboBox#settingCombo QAbstractItemView {{
    background: {BG_1}; color: {TEXT_0};
    selection-background-color: {ACCENT_SOFT}; selection-color: {ACCENT};
}}

QPushButton#settingPrimary {{
    background: {ACCENT}; border: none; border-radius: 6px; padding: 7px 18px;
    color: #FFFFFF; font-weight: 600;
}}
QPushButton#settingPrimary:hover {{ background: #4A7DE0; }}
QPushButton#settingSecondary {{
    background: transparent; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 7px 18px; color: {TEXT_1};
}}
QPushButton#settingSecondary:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton#settingToggle {{
    background: {BG_2}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 12px; color: {TEXT_1}; font-size: 12px;
}}
QPushButton#settingToggle:checked {{ border-color: {ACCENT}; color: {ACCENT}; }}
"""
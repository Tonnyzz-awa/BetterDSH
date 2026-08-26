from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path

import subprocess

from PyQt6.QtCore import Qt, QObject, QTimer, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QInputDialog, QLabel, QMainWindow, QMessageBox,
    QToolButton, QVBoxLayout, QWidget, QFileDialog, QFrame, QSizePolicy,
)

from harness.launcher import (
    HarnessUnavailable, ensure_deps, probe_prereqs,
    start_runtime, stop_runtime, wait_ready,
)
from harness.rpc import HarnessRpcClient, TransportClosed
from harness.settings import DEFAULT_PROVIDER, load_settings, save_settings
from ui.locale import tr, on_lang_change, set_lang, Lang
from ui.betterdsh_ui import (
    Sidebar, MessagesArea, MessageRow, RichText, ThinkBlock, ToolCallCard,
    SendButton, ComposerInput, Toaster, ReasoningSlider, icon_sparkle,
    icon_attach, icon_export, icon_gear, md_to_html, now_stamp, greeting,
    trim_title, ui_font, set_theme, app_qss, is_dark, BG, FG, FG2, MUTED, META, ACCENT,
    ACCENT_ON, SURFACE, SURFACE_W, BORDER, BORDER_S, HOVER,
    SUCCESS, DANGER,
)
import ui.betterdsh_ui as betterdsh_ui


def _strip_text_blocks(content) -> str:
    """从消息 content（list[dict] 或 str）中提取纯文本。"""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif isinstance(block, str):
            parts.append(block)
    return "".join(parts)


class RuntimeBridge(QObject):
    status = pyqtSignal(str, str)
    notification = pyqtSignal(str, dict)
    log = pyqtSignal(str)
    promptFinished = pyqtSignal(str, bool, str)

    def __init__(self, root: Path, repo: Path, config_path: Path):
        super().__init__()
        self._root = root
        self._repo = repo
        self._config_path = config_path
        self._proc: subprocess.Popen | None = None
        self._rpc: HarnessRpcClient | None = None
        try:
            from harness.shared_backend import session_root as _shared_root
            self._session_root = _shared_root()
        except BaseException:
            self._session_root = root / "data" / "sessions"
        self._stderr_thread: threading.Thread | None = None
        self._stderr_buffer: list[str] = []
        self._want_settings: dict = {}

    def start_async(self, settings: dict):
        self._want_settings = settings
        t = threading.Thread(target=self._start_worker, daemon=True)
        t.start()

    def _start_worker(self):
        try:
            self.status.emit("preparing", "检查依赖")
            for name, ok, msg in probe_prereqs(self._repo):
                self.log.emit(f"[{name}] {'OK' if ok else 'FAIL'}{msg}")
            ensure_deps(self._repo, echo=lambda s: self.log.emit(str(s)))

            self.status.emit("launching", "启动运行时")
            proc, rpc = start_runtime(
                repo=self._repo,
                config_path=self._config_path,
                session_root=self._session_root,
                api_key=self._want_settings.get("api_key"),
                provider=self._want_settings.get("provider"),
            )
            old_cb = rpc._notify_cb

            def notify_cb(method, params):
                if method == "+request":
                    return
                if old_cb is not None:
                    try:
                        old_cb(method, params)
                    except BaseException:
                        pass
                self.notification.emit(method, params if isinstance(params, dict) else {})
            rpc._notify_cb = notify_cb

            self._proc = proc
            self._rpc = rpc
            self._start_stderr_thread()

            self.status.emit("waiting", "等待握手")
            wait_ready(rpc, echo=lambda s: self.log.emit(str(s)),
                       stderr_lines=self._stderr_buffer,
                       provider=self._want_settings.get("provider"),
                       model=self._want_settings.get("model") or None,
                       repo=self._repo,
                       reasoning_effort=self._want_settings.get("reasoning_effort") or None)
            self.status.emit("ready", "运行时就绪")
        except HarnessUnavailable as exc:
            self.status.emit("error", f"启动失败: {exc}")
        except TransportClosed as exc:
            self.status.emit("error", f"运行时通道关闭: {exc}")
        except Exception as exc:
            import traceback
            self.log.emit(traceback.format_exc())
            self.status.emit("error", f"意外错误: {exc}")

    def _start_stderr_thread(self):
        assert self._proc is not None
        self._stderr_buffer = []

        def loop():
            assert self._proc is not None and self._proc.stderr is not None
            for line in self._proc.stderr:
                line = line.rstrip()
                self._stderr_buffer.append(line)
                self.log.emit(line)

        self._stderr_thread = threading.Thread(target=loop, daemon=True)
        self._stderr_thread.start()

    def _safe_request(self, method, params, timeout) -> BaseException | None:
        try:
            self._rpc.request(method, params, timeout=timeout)
            return None
        except BaseException as exc:
            return exc

    def send_prompt(self, session_id: str, text: str, reasoning_effort: str | None = None):
        if self._rpc is None:
            raise HarnessUnavailable("运行时未就绪")
        params = {"sessionId": session_id,
                  "contentBlocks": [{"type": "text", "text": text}]}
        if reasoning_effort:
            params["reasoningEffort"] = reasoning_effort
        threading.Thread(target=self._prompt_worker, args=(params,), daemon=True).start()

    def _prompt_worker(self, params: dict):
        sid = params.get("sessionId", "")
        err = self._safe_request("session/prompt", params, 30)
        self.promptFinished.emit(sid, err is None, "" if err is None else str(err))

    def set_reasoning_effort(self, session_id: str, effort: str):
        if self._rpc is None:
            return
        threading.Thread(target=self._reasoning_effort_worker,
                         args=(session_id, effort), daemon=True).start()

    def _reasoning_effort_worker(self, session_id: str, effort: str):
        params = {"sessionId": session_id, "reasoningEffort": effort}
        for method in ("session/setReasoningEffort", "session/update"):
            if self._safe_request(method, params, 8) is None:
                return

    def stop_async(self):
        proc, rpc = self._proc, self._rpc
        if proc is not None and rpc is not None:
            threading.Thread(target=self._stop_worker, args=(proc, rpc), daemon=True).start()

    def _stop_worker(self, proc, rpc):
        stop_runtime(proc, rpc)
        if self._proc is proc:
            self._proc = None
        self._rpc = None
        self.status.emit("stopped", "运行时已停止")

    @property
    def rpc(self):
        return self._rpc


class MainWindow(QMainWindow):
    def __init__(self, root: Path, repo: Path, config_path: Path):
        super().__init__()
        self._root = root
        self._repo = repo
        self._config_path_val = root / "data" / "runtime.cordis.yml"
        self._bridge = RuntimeBridge(root, repo, config_path)
        self._settings = load_settings(root)

        # 会话数据：sid -> {"title","time","group","msgs":[{role,text,reasoning}]}
        self._sessions: dict[str, dict] = {}
        self._active_id: str | None = None

        # 流式渲染的每会话实时状态
        self._live_row: dict[str, MessageRow] = {}
        self._live_rich: dict[str, RichText] = {}
        self._live_think: dict[str, ThinkBlock] = {}
        self._text_buf: dict[str, str] = {}
        self._reason_buf: dict[str, str] = {}
        self._live_msg_ref: dict[str, dict] = {}
        self._live_tools: dict[str, ToolCallCard] = {}

        from harness.config import ALL_PROVIDERS
        self._provider_name_map = {p["id"]: p["name"] for p in ALL_PROVIDERS}

        self.setWindowTitle("BetterDSH · DeepSeek Harness")
        self.resize(1180, 760)
        set_theme(self._settings.get("theme", "light"))
        self._sync_colors()
        self.setStyleSheet(app_qss())

        self._build_ui()
        self._connect_bridge()

        if not self._settings.get("model"):
            try:
                from harness.catalog import default_model_for_provider
                resolved = default_model_for_provider(
                    repo, self._settings.get("provider", DEFAULT_PROVIDER))
                if resolved:
                    self._settings["model"] = resolved
            except BaseException:
                pass

        self._load_history()
        self._update_slider_levels()
        lang = self._settings.get("lang", "zh")
        try:
            set_lang(Lang(lang))
        except ValueError:
            set_lang(Lang("zh"))
        self._apply_lang()
        self._refresh_header()
        self._render_sidebar()
        on_lang_change(self._on_lang_changed)
        QTimer.singleShot(300, self._auto_start)

    # ---------- 历史持久化 ----------
    def _history_path(self) -> Path:
        return self._root / "data" / "history.json"

    def _config_path(self) -> Path:
        return self._config_path_val

    def _load_history(self):
        """从 webgui 共享后端读取会话列表（~/.dsh/sessions/*.jsonl.zstd）。

        只读 header 行，不解析事件——大量会话时性能可控。
        点击某会话时再按需 read_session 解析事件为消息列表。
        """
        # 先读本地 history.json（pygui 私有历史，向后兼容）
        p = self._history_path()
        if p.exists():
            try:
                rows = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                rows = []
            for row in rows:
                sid = row.get("id")
                if not sid:
                    continue
                msgs = []
                for m in row.get("msgs", []):
                    msgs.append({
                        "role": m.get("role", "assistant"),
                        "text": m.get("text", ""),
                        "reasoning": m.get("reasoning", ""),
                    })
                if not msgs:
                    continue
                self._sessions[sid] = {
                    "title": row.get("title", "新对话"),
                    "time": row.get("time", now_stamp()),
                    "group": row.get("group", "更早"),
                    "msgs": msgs,
                }
        # 再从 webgui 共享后端读取真实会话列表
        try:
            from harness.webgui_reader import WebguiReader
            reader = WebguiReader()
            for s in reader.list_sessions():
                sid = s.get("id")
                if not sid or sid in self._sessions:
                    continue
                created = s.get("createdAt")
                if isinstance(created, (int, float)) and created > 0:
                    from datetime import datetime, timezone
                    dt = datetime.fromtimestamp(created / 1000, tz=timezone.utc).astimezone()
                    time_str = dt.strftime("%m/%d %H:%M")
                else:
                    time_str = now_stamp()
                # 优先用 webgui 会话标题（事件 session/title 折叠所得），回退到 cwd 末段或 agentPreset
                cwd = s.get("cwd") or ""
                title = (s.get("title")
                         or (Path(cwd).name if cwd else (s.get("agentPreset") or "webgui 会话")))
                self._sessions[sid] = {
                    "title": title,
                    "time": time_str,
                    "group": "更早",
                    "msgs": [],
                    "_webgui": True,
                }
        except BaseException:
            pass

    def _save_history(self):
        rows = []
        for sid, data in self._sessions.items():
            # webgui 会话不写回本地 history.json（它们由 ~/.dsh/sessions 管理）
            if data.get("_webgui"):
                continue
            if not data["msgs"]:
                continue
            rows.append({
                "id": sid,
                "title": data["title"],
                "time": data.get("time", ""),
                "group": data.get("group", ""),
                "msgs": [{"role": m["role"], "text": m["text"],
                          "reasoning": m.get("reasoning", "")} for m in data["msgs"]],
            })
        try:
            self._history_path().write_text(
                json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    # ---------- 构建界面 ----------
    def _build_ui(self):
        self._central_w = QWidget()
        self._central_w.setObjectName("root")
        self.setCentralWidget(self._central_w)
        layout = QHBoxLayout(self._central_w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 侧边栏
        self.sidebar = Sidebar()
        self.sidebar.newChatRequested.connect(self._new_chat)
        self.sidebar.convSelected.connect(self._switch_to)
        self.sidebar.renameRequested.connect(self._rename_session)
        self.sidebar.deleteRequested.connect(self._delete_session)
        self.sidebar.settingsRequested.connect(self._open_settings)
        self.sidebar.searchChanged.connect(self._on_search)
        layout.addWidget(self.sidebar, 0)

        self._right_w = QWidget()
        right_layout = QVBoxLayout(self._right_w)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(self._build_header())

        self.messages = MessagesArea()
        self.messages.empty_state().promptClicked.connect(self._on_prompt_card)
        self.messages.empty_state().set_greeting(f"{greeting()}，{tr('empty_greet')}")
        right_layout.addWidget(self.messages, 1)

        right_layout.addWidget(self._build_composer())

        layout.addWidget(self._right_w, 1)

        self.toaster = Toaster(self._central_w)

    def _build_header(self) -> QWidget:
        self._header_w = QWidget()
        self._header_w.setFixedHeight(64)
        h = QHBoxLayout(self._header_w)
        h.setContentsMargins(28, 0, 20, 0)
        h.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        self.chat_title = QLabel(tr("new_chat"))
        self.chat_subtitle = QLabel(tr("not_connected"))
        title_box.addWidget(self.chat_title)
        title_box.addWidget(self.chat_subtitle)
        h.addLayout(title_box)
        h.addStretch(1)

        self.export_btn = QToolButton()
        self.export_btn.setIcon(icon_export())
        self.export_btn.setIconSize(QSize(18, 18))
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setToolTip(tr("export_md"))
        self.export_btn.clicked.connect(self._export_conversation)
        h.addWidget(self.export_btn)

        self.header_gear = QToolButton()
        self.header_gear.setIcon(icon_gear())
        self.header_gear.setIconSize(QSize(18, 18))
        self.header_gear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_gear.setToolTip(tr("settings"))
        self.header_gear.clicked.connect(self._open_settings)
        h.addWidget(self.header_gear)

        return self._header_w

    def _build_composer(self) -> QWidget:
        self._composer_wrap = QWidget()
        outer = QVBoxLayout(self._composer_wrap)
        outer.setContentsMargins(24, 10, 24, 20)
        outer.setSpacing(8)

        self._composer_card = QFrame()
        self._composer_card.setObjectName("composerCard")
        self._composer_card.setStyleSheet(f"background: {SURFACE}; border-radius: 14px;")
        cl = QVBoxLayout(self._composer_card)
        cl.setContentsMargins(16, 12, 12, 12)
        cl.setSpacing(8)

        self.input = ComposerInput()
        self.input.submitRequested.connect(self._on_submit)
        self.input.textChanged.connect(self._on_input_changed)
        cl.addWidget(self.input)

        tools = QHBoxLayout()
        tools.setContentsMargins(0, 0, 0, 0)
        tools.setSpacing(10)

        self.attach_btn = QToolButton()
        self.attach_btn.setIcon(icon_attach())
        self.attach_btn.setIconSize(QSize(18, 18))
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setToolTip(tr("attach_file"))
        self.attach_btn.clicked.connect(self._attach_file)
        tools.addWidget(self.attach_btn)

        # 推理强度滑块（档位从 pi-ai 目录动态读取）
        think_lbl_icon = QLabel()
        think_lbl_icon.setPixmap(icon_sparkle(color=FG2).pixmap(15, 15))
        think_lbl_icon.setStyleSheet("background:transparent; border:none;")
        tools.addWidget(think_lbl_icon)
        self.reasoning_slider = ReasoningSlider(levels=["off", "high"])
        self.reasoning_slider.valueChanged.connect(self._on_reasoning_changed)
        tools.addWidget(self.reasoning_slider)

        tools.addStretch(1)

        self.send_btn = SendButton()
        self.send_btn.clicked.connect(self._on_send_clicked)
        tools.addWidget(self.send_btn)

        cl.addLayout(tools)
        outer.addWidget(self._composer_card)

        self._send_hint = QLabel(tr("enter_hint"))
        self._send_hint.setStyleSheet(f"font-size:11px; color:{META}; background:transparent;")
        self._send_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(self._send_hint)

        return self._composer_wrap

    def _connect_bridge(self):
        self._bridge.status.connect(self._on_bridge_status)
        self._bridge.notification.connect(self._on_notification)
        self._bridge.promptFinished.connect(self._on_prompt_finished)
        self._bridge.log.connect(lambda s: None)

    # ---------- 头部 / 侧边栏刷新 ----------
    def _refresh_header(self):
        provider_name = self._provider_name_map.get(
            self._settings.get("provider"), self._settings.get("provider") or tr("provider"))
        model = self._settings.get("model") or tr("model")
        self._provider_model_tag = f"{provider_name} · {model}"
        if self._active_id and self._active_id in self._sessions:
            self.chat_title.setText(self._sessions[self._active_id]["title"])
        else:
            self.chat_title.setText(tr("new_chat"))

    def _model_tag(self) -> str:
        provider_name = self._provider_name_map.get(
            self._settings.get("provider"), self._settings.get("provider") or "")
        model = self._settings.get("model") or ""
        return model or provider_name

    def _render_sidebar(self, query: str = ""):
        convs = []
        for sid, data in self._sessions.items():
            convs.append({
                "id": sid,
                "title": data["title"],
                "time": data.get("time", ""),
                "group": self._local_group(data.get("group", "")),
            })
        convs.reverse()
        self.sidebar.render(convs, self._active_id or "", query)

    def _new_chat(self) -> str:
        sid = f"gui-{uuid.uuid4().hex[:12]}"
        self._sessions[sid] = {
            "title": "新对话", "time": now_stamp(), "group": "今天", "msgs": []
        }
        self._active_id = sid
        self._save_history()
        self._render_sidebar()
        self._render_conversation(sid)
        self.input.setFocus()
        return sid

    def _switch_to(self, sid: str):
        if sid not in self._sessions:
            return
        data = self._sessions[sid]
        # webgui 会话首次打开时按需读取事件内容
        if data.get("_webgui") and not data["msgs"]:
            self._load_webgui_session(sid)
        self._active_id = sid
        self._render_sidebar(self._current_query())
        self._render_conversation(sid)

    def _load_webgui_session(self, sid: str):
        """从 ~/.dsh/sessions 读取指定会话的事件并解析为消息列表。"""
        try:
            from harness.webgui_reader import WebguiReader
            full = WebguiReader().read_session(sid)
        except BaseException:
            return
        if not full:
            return
        events = full.get("events", [])
        data = self._sessions.setdefault(sid, {"title": "webgui 会话", "time": now_stamp(), "group": "更早", "msgs": []})
        data["msgs"] = []
        for ev in events:
            etype = ev.get("type")
            edata = ev.get("data") or {}
            if etype == "user/message":
                text = _strip_text_blocks(edata.get("message", {}).get("content", ""))
                if text:
                    data["msgs"].append({"role": "user", "text": text, "reasoning": ""})
            elif etype == "assistant/message":
                text = _strip_text_blocks(edata.get("message", {}).get("content", ""))
                if text:
                    data["msgs"].append({"role": "assistant", "text": text, "reasoning": ""})
            elif etype == "assistant/chunk":
                chunk = edata.get("chunk") or {}
                ctype = chunk.get("type")
                if ctype == "reasoning-delta" and data["msgs"]:
                    last = data["msgs"][-1]
                    if last["role"] == "assistant":
                        last["reasoning"] += chunk.get("text", "")
                elif ctype == "text-delta" and data["msgs"]:
                    last = data["msgs"][-1]
                    if last["role"] == "assistant":
                        last["text"] += chunk.get("text", "")
            elif etype == "tool/call":
                cid = edata.get("callId") or ""
                name = edata.get("name", "?")
                args = edata.get("arguments", "")
                if isinstance(args, (dict, list)):
                    try:
                        args = json.dumps(args, ensure_ascii=False, indent=2)
                    except BaseException:
                        args = str(args)
                data["msgs"].append({"role": "tool_call", "name": name,
                                     "args": str(args)[:800], "call_id": cid,
                                     "result": "", "is_error": False})
            elif etype == "tool/result":
                msg = edata.get("message") if isinstance(edata.get("message"), dict) else {}
                cid = (msg.get("callId") or "") if isinstance(msg, dict) else ""
                content = msg.get("content") if isinstance(msg, dict) else None
                snippet = " ".join(_strip_text_blocks(content).split())[:500]
                is_error = bool(msg.get("isError")) if isinstance(msg, dict) else False
                paired = False
                if cid:
                    for m in reversed(data["msgs"]):
                        if m.get("role") == "tool_call" and m.get("call_id") == cid:
                            m["result"] = snippet
                            m["is_error"] = is_error
                            paired = True
                            break
                if not paired:
                    data["msgs"].append({"role": "tool_call", "name": "?",
                                         "args": "", "call_id": cid,
                                         "result": snippet, "is_error": is_error})

    def _rename_session(self, sid: str):
        if sid not in self._sessions:
            return
        cur = self._sessions[sid]["title"]
        new_title, ok = QInputDialog.getText(self, tr("rename_title"), tr("new_name"), text=cur)
        if ok and new_title.strip():
            self._sessions[sid]["title"] = new_title.strip()
            if sid == self._active_id:
                self.chat_title.setText(new_title.strip())
            self._save_history()
            self._render_sidebar(self._current_query())

    def _delete_session(self, sid: str):
        if sid not in self._sessions:
            return
        reply = QMessageBox.question(
            self, tr("confirm_delete_title"), tr("confirm_delete_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._sessions.pop(sid, None)
        self._live_row.pop(sid, None)
        self._live_rich.pop(sid, None)
        self._live_think.pop(sid, None)
        self._text_buf.pop(sid, None)
        self._reason_buf.pop(sid, None)
        self._live_msg_ref.pop(sid, None)
        self._live_tools.clear()
        if self._active_id == sid:
            self._active_id = None
            self.chat_title.setText("新对话")
            self.messages.clear()
            self.messages.show_empty()
        self._save_history()
        self._render_sidebar(self._current_query())

    def _local_group(self, g: str) -> str:
        """把侧边栏分组标签本地化；未知分组原样返回。"""
        return {"今天": tr("group_today"), "更早": tr("group_earlier")}.get(g, g or tr("group_earlier"))

    def _current_query(self) -> str:
        return getattr(self, "_search_query", "")

    def _on_search(self, text: str):
        self._search_query = text
        self._render_sidebar(text)

    def _on_prompt_card(self, prompt: str):
        self.input.setPlainText(prompt)
        self.input.setFocus()

    # ---------- 会话渲染 ----------
    def _render_conversation(self, sid: str):
        self.messages.clear()
        self._live_row.pop(sid, None)
        self._live_rich.pop(sid, None)
        self._live_think.pop(sid, None)
        data = self._sessions.get(sid)
        if not data:
            self.messages.show_empty()
            return
        self.chat_title.setText(data["title"])
        if not data["msgs"]:
            self.messages.show_empty()
            return
        self.messages.show_conv()
        for m in data["msgs"]:
            role = m["role"]
            if role == "user":
                row = MessageRow("u", tr("me"), data.get("time", now_stamp()))
                rt = RichText()
                rt.render_md(m["text"])
                row.add_widget(rt)
                self.messages.add_row(row)
            elif role == "assistant":
                row = MessageRow("a", tr("deepseek_name"), data.get("time", now_stamp()),
                                 model_tag=self._model_tag())
                if m.get("reasoning"):
                    tb = ThinkBlock()
                    tb.set_text(m["reasoning"])
                    tb.set_running(False)
                    tb.set_open(False)
                    row.add_widget(tb)
                rt = RichText()
                rt.render_md(m["text"])
                row.add_widget(rt)
                self.messages.add_row(row)
            elif role == "tool_call":
                row = MessageRow("a", tr("tool_msg"), data.get("time", now_stamp()))
                card = ToolCallCard()
                card.set_name(m.get("name", "?"))
                if m.get("args"):
                    card.set_args(m["args"])
                if m.get("result"):
                    if m.get("is_error"):
                        card.set_error()
                    else:
                        card.set_success()
                    card.set_result(m["result"])
                else:
                    card.set_running()
                card.set_open(False)
                row.add_widget(card)
                self.messages.add_row(row)
            elif role == "tool":
                row = MessageRow("a", tr("tool_msg"), data.get("time", now_stamp()))
                rt = RichText()
                rt.render_md(m["text"])
                row.add_widget(rt)
                self.messages.add_row(row)
        self.messages.scroll_bottom()

    # ---------- 发送 ----------
    def _on_input_changed(self):
        has = bool(self.input.toPlainText().strip())
        self.send_btn.setEnabled(has)

    def _on_send_clicked(self):
        text = self.input.toPlainText().strip()
        if text:
            self.input.clear()
            self._on_submit(text)

    def _on_submit(self, text: str):
        text = text.strip()
        if not text:
            return
        if self._bridge.rpc is None:
            self.toaster.show_text(tr("runtime_not_ready"))
            return
        sid = self._active_id
        if sid is None or sid not in self._sessions:
            sid = self._new_chat()
        self._append_user_message(sid, text)
        try:
            self._bridge.send_prompt(sid, text, reasoning_effort=self._settings.get("reasoning_effort"))
        except Exception as exc:
            self._append_tool_message(sid, f"{tr('send_failed')}：{exc}")
            self.send_btn.set_busy(False)

    def _on_prompt_finished(self, sid: str, ok: bool, error: str):
        if ok:
            return
        self._append_tool_message(sid, f"{tr('send_failed')}：{error}")
        if sid == self._active_id:
            self.send_btn.set_busy(False)

    def _append_user_message(self, sid: str, text: str):
        data = self._sessions[sid]
        data["msgs"].append({"role": "user", "text": text, "reasoning": ""})
        if data["title"] == "新对话":  # 数据哨兵（新会话默认标题），非界面文案
            data["title"] = trim_title(text)
            self.chat_title.setText(data["title"])
        data["time"] = now_stamp()
        self.messages.show_conv()
        row = MessageRow("u", tr("me"), now_stamp())
        rt = RichText()
        rt.render_md(text)
        row.add_widget(rt)
        self.messages.add_row(row)
        self.messages.scroll_bottom()
        self._save_history()
        self._render_sidebar(self._current_query())

    def _append_tool_message(self, sid: str, text: str):
        data = self._sessions.get(sid)
        if data is not None:
            data["msgs"].append({"role": "tool", "text": text, "reasoning": ""})
            self._save_history()
        row = MessageRow("a", "工具", now_stamp())
        rt = RichText()
        rt.render_md(text)
        row.add_widget(rt)
        self.messages.add_row(row)
        self.messages.scroll_bottom()

    # ---------- 通知 / 流式事件 ----------
    def _on_notification(self, method: str, params: dict):
        if method == "session.event":
            self._on_session_event(params)
        elif method == "session.status":
            status = params.get("status", "?")
            self.chat_subtitle.setText(tr("session_status").format(status=status))

    def _ensure_live_row(self, sid: str) -> MessageRow:
        """获取或创建当前 turn 的助手 MessageRow。"""
        row = self._live_row.get(sid)
        if row is not None:
            return row
        row = MessageRow("a", tr("deepseek_name"), now_stamp(), model_tag=self._model_tag())
        self._live_row[sid] = row
        data = self._sessions.setdefault(
            sid, {"title": "新对话", "time": now_stamp(), "group": "今天", "msgs": []})
        msg_ref = {"role": "assistant", "text": "", "reasoning": ""}
        data["msgs"].append(msg_ref)
        self._live_msg_ref[sid] = msg_ref
        self._text_buf[sid] = ""
        self._reason_buf[sid] = ""
        if sid == self._active_id:
            self.messages.show_conv()
            self.messages.add_row(row)
        return row

    def _ensure_think(self, sid: str) -> ThinkBlock:
        tb = self._live_think.get(sid)
        if tb is not None:
            return tb
        row = self._ensure_live_row(sid)
        tb = ThinkBlock()
        tb.set_running(True)
        row.add_widget(tb)
        self._live_think[sid] = tb
        return tb

    def _ensure_rich(self, sid: str) -> RichText:
        rt = self._live_rich.get(sid)
        if rt is not None:
            return rt
        row = self._ensure_live_row(sid)
        rt = RichText()
        row.add_widget(rt)
        self._live_rich[sid] = rt
        return rt

    def _on_session_event(self, params: dict):
        sid = params.get("sessionId", "")
        event = params.get("event") or {}
        etype = event.get("type")
        data = event.get("data") or {}

        if etype == "turn/start":
            self._live_row.pop(sid, None)
            self._live_rich.pop(sid, None)
            self._live_think.pop(sid, None)
            self._live_tools.clear()
            if sid == self._active_id:
                self.chat_subtitle.setText(tr("assistant_thinking"))
                self.send_btn.set_busy(True)
                self.send_btn.setEnabled(False)

        elif etype == "user/message":
            return

        elif etype == "assistant/message":
            msg = data.get("message") if isinstance(data.get("message"), dict) else None
            content = (msg or {}).get("content") or []
            text = _strip_text_blocks(content)
            if text:
                rt = self._ensure_rich(sid)
                self._text_buf[sid] = text
                rt.render_md(text)
                ref = self._live_msg_ref.get(sid)
                if ref is not None:
                    ref["text"] = text

        elif etype == "assistant/chunk":
            chunk = data.get("chunk") if isinstance(data.get("chunk"), dict) else {}
            ctype = chunk.get("type")
            if ctype == "reasoning-delta":
                piece = chunk.get("text", "")
                if piece:
                    tb = self._ensure_think(sid)
                    buf = self._reason_buf.get(sid, "") + piece
                    self._reason_buf[sid] = buf
                    tb.set_text(buf)
                    ref = self._live_msg_ref.get(sid)
                    if ref is not None:
                        ref["reasoning"] = buf
            elif ctype == "text-delta":
                piece = chunk.get("text", "")
                if piece:
                    tb = self._live_think.get(sid)
                    if tb is not None and tb.is_running():
                        tb.set_running(False)
                        tb.set_open(False)
                    rt = self._ensure_rich(sid)
                    buf = self._text_buf.get(sid, "") + piece
                    self._text_buf[sid] = buf
                    rt.render_md(buf)
                    ref = self._live_msg_ref.get(sid)
                    if ref is not None:
                        ref["text"] = buf
            elif ctype == "finish":
                tb = self._live_think.get(sid)
                if tb is not None and tb.is_running():
                    tb.set_running(False)
                    tb.set_open(False)

        elif etype == "tool/call":
            cid = data.get("callId") or ""
            name = data.get("name", "?")
            args = data.get("arguments", "")
            if isinstance(args, (dict, list)):
                try:
                    args = json.dumps(args, ensure_ascii=False, indent=2)
                except BaseException:
                    args = str(args)
            row = self._ensure_live_row(sid)
            card = ToolCallCard()
            card.set_name(name)
            if args:
                card.set_args(str(args)[:800])
            card.call_id = cid
            card.set_running()
            row.add_widget(card)
            if cid:
                self._live_tools[cid] = card
            sdata = self._sessions.get(sid)
            if sdata is not None:
                sdata["msgs"].append({"role": "tool_call", "name": name,
                                      "args": str(args)[:800], "call_id": cid,
                                      "result": "", "is_error": False})

        elif etype == "tool/result":
            msg = data.get("message") if isinstance(data.get("message"), dict) else {}
            cid = (msg.get("callId") or "") if isinstance(msg, dict) else ""
            content = msg.get("content") if isinstance(msg, dict) else None
            snippet = " ".join(_strip_text_blocks(content).split())[:500]
            is_error = bool(msg.get("isError")) if isinstance(msg, dict) else False
            card = self._live_tools.pop(cid, None) if cid else None
            if card is None:
                row = self._ensure_live_row(sid)
                card = ToolCallCard()
                card.set_name("?")
                card.call_id = cid
                card.set_running()
                row.add_widget(card)
            if is_error:
                card.set_error()
            else:
                card.set_success()
            if snippet:
                card.set_result(snippet)
            sdata = self._sessions.get(sid)
            if sdata is not None and cid:
                for m in reversed(sdata["msgs"]):
                    if m.get("role") == "tool_call" and m.get("call_id") == cid:
                        m["result"] = snippet
                        m["is_error"] = is_error
                        break

        elif etype == "turn/end":
            self._live_row.pop(sid, None)
            self._live_rich.pop(sid, None)
            self._live_think.pop(sid, None)
            self._live_msg_ref.pop(sid, None)
            self._live_tools.clear()
            self._save_history()
            if sid == self._active_id:
                self.chat_subtitle.setText(tr("completed"))
                self.send_btn.set_busy(False)
                self._on_input_changed()

        if sid == self._active_id:
            self.messages.scroll_bottom()

    # ---------- 运行时生命周期 ----------
    def _auto_start(self):
        if self._bridge.rpc is not None:
            return
        if not self._settings.get("api_key"):
            provider = self._settings.get("provider", "deepseek-official")
            self.chat_subtitle.setText(tr("no_api_key_hint").format(provider=provider))
        self._start_runtime()

    def _start_runtime(self):
        if self._bridge.rpc is not None:
            return
        self.sidebar.set_status(MUTED, tr("connecting"))
        self.chat_subtitle.setText(tr("starting_runtime"))
        self._bridge.start_async(self._settings)

    def _restart_runtime(self):
        if self._bridge.rpc is not None:
            self._bridge.stop_async()
        QTimer.singleShot(200, self._start_runtime)

    def _on_bridge_status(self, stage: str, desc: str):
        provider_name = self._provider_name_map.get(self._settings.get("provider"), "")
        model = self._settings.get("model", "")
        local_desc = {
            "preparing": tr("checking_deps"),
            "launching": tr("starting_runtime"),
            "waiting": tr("waiting_handshake"),
        }.get(stage, desc)
        if stage == "ready":
            self.sidebar.set_status(SUCCESS, tr("connected"))
            self.chat_subtitle.setText(tr("runtime_ready").format(provider=provider_name, model=model))
            self._on_input_changed()
            self.input.setFocus()
        elif stage == "error":
            self.sidebar.set_status(DANGER, tr("error"))
            self.chat_subtitle.setText(local_desc)
        elif stage == "stopped":
            self.sidebar.set_status(MUTED, tr("stopped"))
            self.chat_subtitle.setText(tr("stopped"))
        elif stage in ("preparing", "launching", "waiting"):
            self.sidebar.set_status(META, local_desc)
            self.chat_subtitle.setText(local_desc + "…")
        else:
            self.sidebar.set_status(META, local_desc)

    # ---------- 主题 ----------
    def _sync_colors(self) -> None:
        # set_theme 重绑定了 betterdsh_ui 的模块级颜色常量；本模块用 from-import
        # 绑定的是 import 时刻的快照，需手动同步，否则内联样式标签 / 状态点在切
        # 主题后仍是旧色（深色模式“失效”的根因）。
        global BG, FG, FG2, MUTED, META, ACCENT, ACCENT_ON, SURFACE, SURFACE_W
        global BORDER, BORDER_S, HOVER, SUCCESS, DANGER
        BG = betterdsh_ui.BG
        FG = betterdsh_ui.FG
        FG2 = betterdsh_ui.FG2
        MUTED = betterdsh_ui.MUTED
        META = betterdsh_ui.META
        ACCENT = betterdsh_ui.ACCENT
        ACCENT_ON = betterdsh_ui.ACCENT_ON
        SURFACE = betterdsh_ui.SURFACE
        SURFACE_W = betterdsh_ui.SURFACE_W
        BORDER = betterdsh_ui.BORDER
        BORDER_S = betterdsh_ui.BORDER_S
        HOVER = betterdsh_ui.HOVER
        SUCCESS = betterdsh_ui.SUCCESS
        DANGER = betterdsh_ui.DANGER

    def _apply_theme(self) -> None:
        """主题变更后重建中央控件并刷新全局 QSS（控件在 __init__ 固化了配色）。"""
        set_theme(self._settings.get("theme", "light"))
        self._sync_colors()
        qss = app_qss()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)
        self.setStyleSheet(qss)
        old = self.centralWidget()
        self._build_ui()
        self._live_row.clear()
        self._live_rich.clear()
        self._live_think.clear()
        self._text_buf.clear()
        self._reason_buf.clear()
        self._live_msg_ref.clear()
        self._live_tools.clear()
        self._render_sidebar()
        self._refresh_header()
        self._update_slider_levels()
        self._apply_lang()
        if self._active_id:
            self._switch_to(self._active_id)
        if old is not None:
            old.deleteLater()

    # ---------- 设置 ----------
    def _open_settings(self):
        from harness.config import load_extra_entries, write_config
        from ui.settings_dialog import SettingsDialog

        def runtime_list_models(pid: str) -> list[str]:
            rpc = self._bridge.rpc
            if rpc is None:
                return []
            try:
                result = rpc.list_models([pid], timeout=8)
            except BaseException:
                return []
            for p in (result or {}).get("providers", []):
                if p.get("id") == pid:
                    return [m.get("id") for m in p.get("models", []) if m.get("id")]
            return []

        dlg = SettingsDialog(self._root, repo=self._repo,
                             list_models_cb=runtime_list_models, parent=self)
        if dlg.exec() != SettingsDialog.DialogCode.Accepted:
            return
        self._settings = dlg.current_settings()
        if (self._settings.get("theme", "light") == "dark") != is_dark():
            self._apply_theme()
        provider = self._settings.get("provider", "deepseek-official")
        entries = load_extra_entries(self._root)
        if provider == "custom" and self._settings.get("base_url"):
            write_config(self._config_path(), provider_id=provider,
                         base_url=self._settings["base_url"],
                         custom_models=self._settings.get("custom_models") or [],
                         extra_entries=entries)
        else:
            write_config(self._config_path(), provider_id=provider,
                         extra_entries=entries)
        self._update_slider_levels()
        self._refresh_header()
        self.toaster.show_text(tr("settings_saved"))
        self._restart_runtime()

    # ---------- 推理强度滑块 ----------
    def _on_reasoning_changed(self, idx: int):
        levels = self.reasoning_slider.levels()
        if idx < 0 or idx >= len(levels):
            return
        effort = levels[idx]
        self._settings["reasoning_effort"] = effort
        try:
            save_settings(self._root, self._settings)
        except BaseException:
            pass
        # 尝试实时下发（stdio 运行时可能不支持，静默降级）
        if self._bridge.rpc is not None and self._active_id:
            try:
                self._bridge.set_reasoning_effort(self._active_id, effort)
            except BaseException:
                pass
        # 设置已保存，下一次 prompt 必定带上此档位，即刻生效
        self.toaster.show_text(tr("reasoning_applied").format(effort=effort))

    # ---------- 附件（真实：读取文本文件插入输入框） ----------
    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("attach_file"), "",
            "文本文件 (*.txt *.md *.py *.js *.ts *.json *.yaml *.yml *.csv *.log *.html *.css);;所有文件 (*.*)")
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self.toaster.show_text(tr("read_file_failed").format(err=exc))
            return
        if len(content) > 20000:
            content = content[:20000] + "\n…（内容过长已截断）"
        name = Path(path).name
        cur = self.input.toPlainText()
        block = f"\n\n--- 文件：{name} ---\n{content}\n--- 文件结束 ---\n"
        self.input.setPlainText(cur + block)
        self.input.setFocus()
        self.toaster.show_text(tr("file_attached").format(name=name))

    # ---------- 导出 ----------
    def _export_conversation(self):
        sid = self._active_id
        if not sid or sid not in self._sessions or not self._sessions[sid]["msgs"]:
            self.toaster.show_text(tr("no_export"))
            return
        data = self._sessions[sid]
        default_name = f"{trim_title(data['title'])}.md".replace("…", "")
        path, _ = QFileDialog.getSaveFileName(
            self, tr("export_title"), default_name, "Markdown 文件 (*.md);;所有文件 (*.*)")
        if not path:
            return
        lines = [f"# {data['title']}\n"]
        for m in data["msgs"]:
            role = m["role"]
            if role == "user":
                lines.append(f"\n## {tr('me')}\n\n{m['text']}\n")
            elif role == "assistant":
                if m.get("reasoning"):
                    lines.append(f"\n## {tr('deepseek_name')}（思考过程）\n\n> {m['reasoning']}\n")
                lines.append(f"\n## {tr('deepseek_name')}\n\n{m['text']}\n")
            elif role == "tool_call":
                tag = f" — {tr('tool_failed')}" if m.get("is_error") else ""
                lines.append(f"\n### {tr('tool_msg')}：{m.get('name', '?')}{tag}\n")
                if m.get("args"):
                    lines.append(f"\n**{tr('tool_args')}**\n\n```\n{m['args']}\n```\n")
                if m.get("result"):
                    lines.append(f"\n**{tr('tool_output')}**\n\n{m['result']}\n")
            elif role == "tool":
                lines.append(f"\n## {tr('tool_msg')}\n\n{m['text']}\n")
        try:
            Path(path).write_text("".join(lines), encoding="utf-8")
        except OSError as exc:
            self.toaster.show_text(tr("export_failed").format(err=exc))
            return
        self.toaster.show_text(tr("exported_to").format(name=Path(path).name))

    # ---------- 语言 ----------
    def _on_lang_changed(self, lang):
        try:
            self._apply_lang()
        except BaseException:
            pass

    def _apply_lang(self):
        self.sidebar._new_btn.setText(f"  {tr('new_chat')}")
        self.sidebar._search.setPlaceholderText(tr("search"))
        self.sidebar._foot_title.setText(tr("brand"))
        self.sidebar._gear.setToolTip(tr("settings"))
        self.input.setPlaceholderText(tr("input_placeholder"))
        self.export_btn.setToolTip(tr("export_md"))
        self.header_gear.setToolTip(tr("settings"))
        self.attach_btn.setToolTip(tr("attach_file"))
        self._send_hint.setText(tr("enter_hint"))
        self.messages.empty_state().apply_lang()
        self._refresh_header()

    def _update_slider_levels(self):
        try:
            from harness.catalog import reasoning_levels
            provider = self._settings.get("provider", "deepseek-official")
            model = self._settings.get("model", "")
            repo = self._repo
            levels = reasoning_levels(repo, provider, model) or ["high"]
        except BaseException:
            levels = ["high"]
        # 始终在最前面加入 off 档位，让用户可以关闭深度思考
        if "off" not in levels:
            levels = ["off"] + levels
        self.reasoning_slider.blockSignals(True)
        self.reasoning_slider.setLevels(levels)
        effort = self._settings.get("reasoning_effort", "high")
        levels_list = self.reasoning_slider.levels()
        if effort in levels_list:
            self.reasoning_slider.setValue(levels_list.index(effort))
        else:
            self.reasoning_slider.setValue(max(0, len(levels_list) - 1))
        self.reasoning_slider.blockSignals(False)

    def closeEvent(self, event):
        try:
            self._save_history()
        except BaseException:
            pass
        self._bridge.stop_async()
        super().closeEvent(event)









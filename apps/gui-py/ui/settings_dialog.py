"""设置对话框: 供应商 / 模型 / API key / 自定义端点。

模型列表不再写死：
- 若运行时已连接，优先调用 `models/list` RPC 拿注册路由的动态模型目录；
- 否则读取已安装 pi-ai 的 providers 数据（与运行时同源）；
- 两者都拿不到时，允许手动输入任意模型 id。
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from harness import config as hc
from harness import settings as hs
from ui.locale import tr, set_lang, Lang, lang_name


class SettingsDialog(QDialog):
    def __init__(self, root: Path, *, repo: Path | None = None,
                 list_models_cb=None, parent=None):
        """list_models_cb: 可选，签名 (provider) -> list[str]。运行时已连接时由主窗口注入。"""
        super().__init__(parent)
        self._root = root
        self._repo = repo
        self._list_models_cb = list_models_cb
        self._settings = hs.load_settings(root)
        self.setWindowTitle(tr("settings_title"))
        self.setModal(True)
        self.setMinimumWidth(460)
        self._build_ui()
        self._load_values()

    # ---- UI ----

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 18)
        outer.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.provider_box = QComboBox()
        self.provider_box.setObjectName("settingCombo")
        for p in hc.ALL_PROVIDERS:
            self.provider_box.addItem(p["name"], p["id"])
        form.addRow(tr("provider_label"), self.provider_box)

        self.model_box = QComboBox()
        self.model_box.setObjectName("settingCombo")
        self.model_box.setEditable(True)
        form.addRow(tr("model"), self.model_box)

        # ---- 思考强度（从 pi-ai 目录动态拉取档位） ----
        self.reasoning_box = QComboBox()
        self.reasoning_box.setObjectName("settingCombo")
        form.addRow(tr("reasoning_label"), self.reasoning_box)

        # ---- harness 模式（agent preset，动态读取磁盘真实预设） ----
        self.preset_box = QComboBox()
        self.preset_box.setObjectName("settingCombo")
        self._preset_meta: dict[str, dict] = {}
        self._reload_presets()
        self.preset_box.currentIndexChanged.connect(self._refresh_preset_hint)
        form.addRow(tr("harness_mode"), self.preset_box)

        self.preset_hint = QLabel()
        self.preset_hint.setObjectName("hintLabel")
        self.preset_hint.setWordWrap(True)
        form.addRow("", self.preset_hint)

        # ---- 工作区 ----
        self.workspace_row = QWidget()
        ws_h = QHBoxLayout(self.workspace_row)
        ws_h.setContentsMargins(0, 0, 0, 0)
        ws_h.setSpacing(8)
        self.workspace_box = QComboBox()
        self.workspace_box.setObjectName("settingCombo")
        ws_h.addWidget(self.workspace_box, 1)
        self.add_ws_btn = QPushButton(tr("add_workspace"))
        self.add_ws_btn.setObjectName("settingSecondary")
        self.add_ws_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_ws_btn.clicked.connect(self._add_workspace)
        ws_h.addWidget(self.add_ws_btn)
        form.addRow(tr("workspace"), self.workspace_row)
        self._reload_workspaces()

        self.key_edit = QLineEdit()
        self.key_edit.setObjectName("settingEdit")
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText(tr("paste_key_hint"))
        self.toggle_key_btn = QPushButton(tr("show"))
        self.toggle_key_btn.setObjectName("settingToggle")
        self.toggle_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_key_btn.setCheckable(True)
        self.toggle_key_btn.toggled.connect(
            lambda on: self.key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password)
        )
        key_row = QWidget()
        key_h = QHBoxLayout(key_row)
        key_h.setContentsMargins(0, 0, 0, 0)
        key_h.setSpacing(8)
        key_h.addWidget(self.key_edit, 1)
        key_h.addWidget(self.toggle_key_btn)
        form.addRow(tr("api_key"), key_row)

        self.env_label = QLabel()
        self.env_label.setObjectName("hintLabel")
        self.env_label.setWordWrap(True)
        form.addRow("", self.env_label)

        self.base_url_row = QWidget()
        base_h = QHBoxLayout(self.base_url_row)
        base_h.setContentsMargins(0, 0, 0, 0)
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setObjectName("settingEdit")
        self.base_url_edit.setPlaceholderText("https://api.example.com/v1")
        base_h.addWidget(self.base_url_edit, 1)
        form.addRow(tr("base_url_label"), self.base_url_row)

        # ---- 语言选择 ----
        self.lang_box = QComboBox()
        self.lang_box.setObjectName("settingCombo")
        for lang in Lang:
            self.lang_box.addItem(lang_name(lang), lang.value)
        form.addRow(f"{tr('language')} / Language", self.lang_box)

        outer.addLayout(form)

        tip = QLabel(tr("settings_tip"))
        tip.setObjectName("hintLabel")
        tip.setWordWrap(True)
        outer.addWidget(tip)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.cancel_btn = QPushButton(tr("cancel"))
        self.cancel_btn.setObjectName("settingSecondary")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton(tr("save_restart"))
        self.save_btn.setObjectName("settingPrimary")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._on_save)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        outer.addLayout(btns)

        self.provider_box.currentIndexChanged.connect(self._refresh_models)
        self.provider_box.currentIndexChanged.connect(self._refresh_custom_visibility)
        self.model_box.currentTextChanged.connect(self._refresh_reasoning)

    # ---- 值加载 / 动态模型 ----

    def _current_provider_id(self) -> str:
        return self.provider_box.currentData()

    def _fetch_models(self, pid: str) -> list[str]:
        """按优先级拿模型列表：运行时 RPC > 已装 pi-ai 目录 > 空。"""
        if self._list_models_cb is not None:
            try:
                live = self._list_models_cb(pid)
                if live:
                    return live
            except BaseException:
                pass
        if self._repo is not None:
            try:
                from harness.catalog import provider_models
                disk = provider_models(self._repo, pid)
                if disk:
                    return disk
            except BaseException:
                pass
        return []

    def _refresh_models(self):
        pid = self._current_provider_id()
        options = self._fetch_models(pid)
        saved = self._settings.get("model")
        if saved and saved not in options:
            options.append(saved)  # 保留已有选择，避免切供应商把模型改没
        self.model_box.clear()
        self.model_box.addItems(options)
        current = saved or (options[0] if options else "")
        if current:
            self.model_box.setCurrentText(current)
        self._refresh_reasoning()

    def _refresh_reasoning(self):
        """用 pi-ai 目录的官方档位填充思考强度下拉。"""
        pid = self._current_provider_id()
        model_id = self.model_box.currentText().strip()
        levels: list[str] = []
        if self._repo is not None and model_id:
            try:
                from harness.catalog import reasoning_levels
                levels = reasoning_levels(self._repo, pid, model_id)
            except BaseException:
                levels = []
        saved = self._settings.get("reasoning_effort")
        current = saved if saved in levels else (levels[-1] if levels else "high")
        self.reasoning_box.clear()
        if levels:
            for lv in levels:
                self.reasoning_box.addItem(lv, lv)
            self.reasoning_box.setCurrentText(current)
        else:
            self.reasoning_box.addItem("high", "high")
            self.reasoning_box.setCurrentIndex(0)
        self.reasoning_box.setEnabled(bool(levels))

    def _refresh_custom_visibility(self):
        is_custom = self._current_provider_id() == "custom"
        self.base_url_row.setVisible(is_custom)
        if is_custom:
            env = "CUSTOM_API_KEY"
        else:
            env = hs.env_name_for_provider(self._current_provider_id()) or "DEEPSEEK_API_KEY"
        self.env_label.setText(tr("key_injected_hint").format(env=env))

    def _reload_presets(self):
        """动态读取磁盘上的真实 agent preset，填充下拉（不硬编码）。"""
        from harness.presets import list_preset_options
        self.preset_box.blockSignals(True)
        self.preset_box.clear()
        self._preset_meta = {}
        try:
            opts = list_preset_options()
        except BaseException:
            opts = []
        for p in opts:
            self.preset_box.addItem(p["name"], p["id"])
            self._preset_meta[p["id"]] = p
        self.preset_box.blockSignals(False)
        return opts

    def _refresh_preset_hint(self):
        """更新 harness 模式下拉的描述提示（读真实 preset 的 description）。"""
        pid = self.preset_box.currentData()
        meta = self._preset_meta.get(pid or "")
        if meta and meta.get("description"):
            self.preset_hint.setText(meta["description"])
        else:
            self.preset_hint.setText("")

    def _reload_workspaces(self):
        """动态读取 webgui 的 workspace 注册表，填充工作区下拉。"""
        from harness.shared_backend import list_workspaces
        self.workspace_box.blockSignals(True)
        self.workspace_box.clear()
        self._workspaces = []
        try:
            self._workspaces = list_workspaces()
        except BaseException:
            self._workspaces = []
        for ws in self._workspaces:
            title = ws.get("title") or ws.get("workspaceId", "")
            path = ws.get("path", "")
            self.workspace_box.addItem(f"{title}  ·  {path}", ws.get("workspaceId"))
        self.workspace_box.blockSignals(False)

    def _add_workspace(self):
        """选择并登记一个目录作为工作区。"""
        from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
        from harness.shared_backend import create_workspace
        path, _ = QFileDialog.getExistingDirectory(self, tr("workspace"), "")
        if not path:
            return
        created = create_workspace(path)
        if created is None:
            QMessageBox.information(self, tr("workspace"), tr("workspace_invalid"))
            return
        # 用 QInputDialog 提示标题（可选，默认取目录名）
        title, ok = QInputDialog.getText(self, tr("workspace"), tr("workspace_title"), text=created.get("title", ""))
        if ok and title.strip() and title.strip() != created.get("title", ""):
            created["title"] = title.strip()
            self._update_ws_title(created.get("workspaceId"), title.strip())
        self._reload_workspaces()
        self.workspace_box.setCurrentIndex(self.workspace_box.findData(created.get("workspaceId")))

    def _update_ws_title(self, wid, title):
        """就地更新 workspace 注册表中某个工作区的标题。"""
        from harness.shared_backend import workspace_path
        import json as _json
        wp = workspace_path()
        try:
            data = _json.loads(wp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        try:
            data["tables"]["workspaces"][wid]["title"] = title
            wp.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except (KeyError, OSError):
            pass

    def _load_values(self):
        pid = self._settings.get("provider", hs.DEFAULT_PROVIDER)
        idx = self.provider_box.findData(pid)
        self.provider_box.setCurrentIndex(idx if idx >= 0 else 0)
        self._refresh_models()
        self.key_edit.setText(self._settings.get("api_key", ""))
        self.base_url_edit.setText(self._settings.get("base_url", ""))
        self._refresh_custom_visibility()
        # 语言
        saved_lang = self._settings.get("lang", "zh")
        li = self.lang_box.findData(saved_lang)
        self.lang_box.setCurrentIndex(li if li >= 0 else 0)
        # 思考强度
        saved_re = self._settings.get("reasoning_effort", "high")
        re_idx = self.reasoning_box.findData(saved_re)
        self.reasoning_box.setCurrentIndex(re_idx if re_idx >= 0 else max(0, self.reasoning_box.count() - 1))
        # harness 模式（agent preset）
        saved_preset = self._settings.get("agent_preset", "")
        p_idx = self.preset_box.findData(saved_preset)
        self.preset_box.setCurrentIndex(p_idx if p_idx >= 0 else 0)
        self._refresh_preset_hint()
        # 工作区
        saved_ws = self._settings.get("workspace", "")
        w_idx = self.workspace_box.findData(saved_ws)
        self.workspace_box.setCurrentIndex(w_idx if w_idx >= 0 else 0)

    # ---- 保存 ----

    def _on_save(self):
        model_text = self.model_box.currentText().strip()
        if not model_text:
            # 动态解析：优先当前下拉第一个，其次 catalog 默认
            model_text = (self.model_box.itemText(0)
                          or self._dynamic_default_model())
        custom_models = [self.model_box.currentText()] if self.model_box.currentText() else []
        sel_lang = self.lang_box.currentData() or "zh"
        set_lang(Lang(sel_lang))
        new_settings = {
            "provider": self._current_provider_id(),
            "api_key": self.key_edit.text().strip(),
            "model": model_text,
            "base_url": self.base_url_edit.text().strip(),
            "custom_models": custom_models,
            "lang": sel_lang,
            "theme": "light",
            "reasoning_effort": self.reasoning_box.currentData() or "high",
            "agent_preset": self.preset_box.currentData() or "",
            "workspace": self.workspace_box.currentData() or "",
        }
        hs.save_settings(self._root, new_settings)
        self._settings = new_settings
        self.accept()

    def _dynamic_default_model(self) -> str:
        if self._repo is None:
            return ""
        try:
            from harness.catalog import default_model_for_provider
            return default_model_for_provider(self._repo, self._current_provider_id())
        except BaseException:
            return ""

    def current_settings(self) -> dict:
        return self._settings
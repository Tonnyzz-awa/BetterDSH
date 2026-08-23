"""GUI 设置的持久化，与 webgui 共用同一后端。

读优先 webgui 共享源，写同时落到本地 data/settings.json 与 webgui 的
~/.dsh/{settings.yaml,.credentials.yaml}，保证两端的 provider / API key /
model / reasoning 配置一致。

存明文 key 有风险, 但这是本机工具; 我们对两个约束保持诚实:
- 读取时校验 JSON 结构与字段名, 损坏时静默回到默认, 不炸启动

字段:
    provider:      供应商 id (config.ALL_PROVIDERS 内)
    api_key:       API key (明文, 仅本机)
    model:         模型 id (可手填)
    base_url:      自定义 OpenAI 兼容端点 (仅 custom 供应商使用)
    custom_models: 自定义端点附加模型列表 (可空)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .shared_backend import (
    load_settings_merged,
    save_settings_shared,
)

DEFAULT_PROVIDER = "deepseek-official"
DEFAULT_MODEL = "deepseek-v4-flash"

_STORE_NAME = "settings.json"
_KEYS = ("provider", "api_key", "model", "base_url", "custom_models", "lang", "theme", "reasoning_effort", "agent_preset", "workspace")


def _store_path(root: Path) -> Path:
    return root / "data" / _STORE_NAME


def load_settings(root: Path) -> dict:
    """读设置; 文件缺失/损坏/字段非法时返回默认值。

    合并 webgui 共享后端（provider/model/reasoning_effort/api_key），
    共享源优先于本地，保证 pygui 打开就看到 webgui 的配置。
    """
    path = _store_path(root)
    defaults = {
        "provider": DEFAULT_PROVIDER,
        "api_key": "",
        "model": DEFAULT_MODEL,
        "base_url": "",
        "custom_models": [],
        "lang": "zh",
        "theme": "light",
        "reasoning_effort": "high",
        "agent_preset": "",
        "workspace": "",
    }
    out = dict(defaults)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = {}
        if isinstance(raw, dict):
            for key in _KEYS:
                if key not in defaults:
                    continue
                if not isinstance(raw.get(key), type(defaults[key]) if defaults[key] is not None else str):
                    continue
                if key == "custom_models":
                    value = raw[key]
                    if all(isinstance(m, str) for m in value):
                        out[key] = value
                elif key == "model" and raw[key] == "":
                    out[key] = DEFAULT_MODEL
                else:
                    out[key] = raw[key]
    # 合并 webgui 共享后端（共享源优先）
    return load_settings_merged(out)


def save_settings(root: Path, settings: dict) -> None:
    """写回设置; 尽力而为, 失败静默（配置丢失不等于崩溃）。

    同时写本地 data/settings.json 与 webgui 的 settings.yaml/.credentials.yaml。
    lang/theme 仅在本地；provider/key/model/base_url/reasoning_effort 两端同步。
    """
    filtered = {key: settings.get(key) for key in _KEYS if key in settings}
    path = _store_path(root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(filtered, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        if os.name != "nt":  # POSIX 上收紧权限, 保护明文 key
            try:
                path.chmod(0o600)
            except OSError:
                pass
    except OSError:
        pass
    # 同步到 webgui 共享后端
    try:
        save_settings_shared(filtered)
    except BaseException:
        pass


def env_name_for_provider(provider: str) -> str | None:
    """供应商 id -> 其 API key 环境变量名。"""
    from .config import provider_env_id
    return provider_env_id(provider)
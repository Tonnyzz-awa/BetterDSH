"""与 webgui 共用同一后端的读写层。

pygui 与 webgui 共享同一套运行时后端。webgui 把用户数据放在 DSH_HOME
（默认 ~/.dsh，或 $DSH_HOME）下的 settings.yaml / .credentials.yaml /
sessions，pygui 直接读写同一文件，即为“共用一个后端”。

本模块只负责磁盘读写，不限定 UI。读取/写入约定：
  - settings.yaml      → agent-default-model 节的 provider/model/reasoningEffort
  - .credentials.yaml  → API Key（如 DEEPSEEK_API_KEY）
  - sessions           → 会话日志目录（与 runtime 的 DSH_SESSION_ROOT 一致）

PyYAML 不可用时读写不会崩：读不到就跳过共享源，写不进就保持本地。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_HAS_YAML = False
_yaml = None
try:
    import yaml as _yaml  # type: ignore[import-untyped]
    _HAS_YAML = True
except ImportError:
    pass


# 类定义必须在 PyYAML 存在时才做，否则 import 期就会 NameError 崩整个 harness。
if _HAS_YAML:
    class _StringScalarLoader(_yaml.SafeLoader):
        """YAML 1.1 会把 off/on/yes/no 解析成布尔；这个 Loader 只保留字符串
        解析器，避免 reasoningEffort=off 变成 False。"""

    _StringScalarLoader.yaml_implicit_resolvers = {
        key: [(tag, regexp) for tag, regexp in rules if tag == "tag:yaml.org,2002:str"]
        for key, rules in _StringScalarLoader.yaml_implicit_resolvers.items()
    }
else:
    _StringScalarLoader = None


def _load_yaml(text: str) -> Any:
    """用纯字符串 Loader 解析 YAML（不识别 off/on/yes/no 为布尔）。"""
    if _StringScalarLoader is None:
        raise TypeError("PyYAML 不可用")
    return _yaml.load(text, Loader=_StringScalarLoader)


DSH_HOME_DIR = ".dsh"
DSH_HOME_ENV = "DSH_HOME"
SETTINGS_FILE = "settings.yaml"
CREDENTIALS_FILE = ".credentials.yaml"
SESSIONS_DIR = "sessions"

# pygui 设置字段 → agent-default-model 节字段名
_AGENT_KEYS = {
    "provider": "provider",
    "model": "model",
    "reasoning_effort": "reasoningEffort",
}

# pygui 设置字段 → agent-presets 节字段名（harness 模式）
_AGENT_PRESET_KEY = "agent_preset"
_AGENT_PRESET_YAML_KEY = "default"

# pygui 设置字段 → credentials 文件 key
_CRED_KEY = "api_key"


def resolve_dsh_home() -> Path:
    """同 webgui 的 resolveDshHome 逻辑。"""
    env = os.environ.get(DSH_HOME_ENV)
    if env and env.strip():
        return Path(env.strip()).expanduser().resolve()
    return (Path.home() / DSH_HOME_DIR).expanduser().resolve()


def settings_path() -> Path:
    return resolve_dsh_home() / SETTINGS_FILE


def credentials_path() -> Path:
    return resolve_dsh_home() / CREDENTIALS_FILE


def session_root() -> Path:
    return resolve_dsh_home() / SESSIONS_DIR


# ---------------------------------------------------------------------------
# 读
# ---------------------------------------------------------------------------
def read_shared_settings() -> dict[str, Any]:
    """读取 webgui 的共享配置（provider/model/reasoning_effort 等）。

    返回 pygui 设置字段名的子集（缺省字段不出现）。
    """
    out: dict[str, Any] = {}
    path = settings_path()
    if not _HAS_YAML or not path.is_file():
        return out
    try:
        data = _load_yaml(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return out
    agent = data.get("agent-default-model") or {}
    if isinstance(agent, dict):
        for py_key, yaml_key in _AGENT_KEYS.items():
            if yaml_key in agent:
                # YAML 1.1 会把 off/on/yes/no 解析成布尔，强制字符串避免类型漂移
                out[py_key] = str(agent[yaml_key])
    # agent-presets.default → harness 模式（standard/code/minimal/cordis）
    preset_sec = data.get("agent-presets") or {}
    if isinstance(preset_sec, dict) and preset_sec.get(_AGENT_PRESET_YAML_KEY):
        out[_AGENT_PRESET_KEY] = str(preset_sec[_AGENT_PRESET_YAML_KEY])
    # 从供应商适配器节提取 base_url / apiKeyEnv（与 reader 一致）
    for ns in ("llm-deepseek", "llm-pi-ai"):
        section = data.get(ns) or {}
        if isinstance(section, dict):
            if "baseURL" in section and "base_url" not in out:
                out["base_url"] = section["baseURL"]
            if "apiKeyEnv" in section:
                out["_api_key_env"] = section["apiKeyEnv"]
    return out


def read_shared_credentials() -> dict[str, str]:
    """读取 webgui 的共享凭据（API Key 映射）。"""
    out: dict[str, str] = {}
    path = credentials_path()
    if not _HAS_YAML or not path.is_file():
        return out
    try:
        data = _load_yaml(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return out
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                out[k] = v
    return out


def load_settings_merged(local: dict[str, Any]) -> dict[str, Any]:
    """把本地设置与 webgui 共享后端合并。

    优先级：webgui 共享源 > 本地。这样 pygui 打开就会看到 webgui
    已配置好的 provider/model/reasoning_effort 与 API Key。
    """
    merged = dict(local)
    shared = read_shared_settings()
    if shared.get("provider"):
        merged["provider"] = shared["provider"]
    if shared.get("model"):
        merged["model"] = shared["model"]
    if shared.get("reasoning_effort") is not None:
        merged["reasoning_effort"] = shared["reasoning_effort"]
    if shared.get(_AGENT_PRESET_KEY):
        merged[_AGENT_PRESET_KEY] = shared[_AGENT_PRESET_KEY]
    if shared.get("base_url"):
        merged["base_url"] = shared["base_url"]
    creds = read_shared_credentials()
    env = shared.get("_api_key_env") or _default_env_for(merged.get("provider"))
    if env and creds.get(env):
        merged["api_key"] = creds[env]
    return merged


def _default_env_for(provider: str | None) -> str | None:
    try:
        from .config import provider_env_id
        return provider_env_id(provider)
    except Exception:
        return "DEEPSEEK_API_KEY"


# ---------------------------------------------------------------------------
# 写
# ---------------------------------------------------------------------------
def write_shared_settings(settings: dict[str, Any]) -> None:
    """把 provider/model/reasoning_effort 写入 webgui 的 settings.yaml。

    保留 webgui 已有节（ui-*、agent-presets、llm-* 等），只更新
    agent-default-model。PyYAML 缺失时静默跳过。
    """
    if not _HAS_YAML:
        return
    path = settings_path()
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            parsed = _yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            pass
    agent = dict(data.get("agent-default-model") or {})
    changed = False
    for py_key, yaml_key in _AGENT_KEYS.items():
        if py_key in settings and settings[py_key] is not None:
            agent[yaml_key] = settings[py_key]
            changed = True
    if changed:
        data["agent-default-model"] = agent
    # agent_preset → agent-presets.default（harness 模式）
    if settings.get(_AGENT_PRESET_KEY):
        preset_sec = dict(data.get("agent-presets") or {})
        preset_sec[_AGENT_PRESET_YAML_KEY] = settings[_AGENT_PRESET_KEY]
        data["agent-presets"] = preset_sec
    # 默认（无 preset）改 provider/model 也要落盘，否则重载被共享配置覆盖（静默回退）。
    if changed or settings.get(_AGENT_PRESET_KEY):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                _yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            if os.name != "nt":
                try:
                    path.chmod(0o600)
                except OSError:
                    pass
        except OSError:
            pass


def write_shared_credentials(settings: dict[str, Any]) -> None:
    """把 API Key 写入 webgui 的 .credentials.yaml。

    只更新该 provider 对应的环境变量键，保留其他键。
    """
    if not _HAS_YAML:
        return
    api_key = settings.get("api_key")
    if not api_key:
        return
    env = _default_env_for(settings.get("provider")) or "DEEPSEEK_API_KEY"
    path = credentials_path()
    creds: dict[str, Any] = {}
    if path.is_file():
        try:
            parsed = _yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                creds = parsed
        except Exception:
            pass
    creds[env] = api_key
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _yaml.safe_dump(creds, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        if os.name != "nt":
            try:
                path.chmod(0o600)
            except OSError:
                pass
    except OSError:
        pass


def save_settings_shared(settings: dict[str, Any]) -> None:
    """把 API 相关设置写回 webgui 共享后端（配置 + 凭据）。"""
    write_shared_settings(settings)
    write_shared_credentials(settings)


# ---------------------------------------------------------------------------
# 工作区
# ---------------------------------------------------------------------------
def storages_root() -> Path:
    return resolve_dsh_home() / "storages"


def workspace_path() -> Path:
    return storages_root() / "workspace.json"


def list_workspaces() -> list[dict[str, Any]]:
    """读取 webgui 的 workspace 注册表，返回按 updatedAt 降序的工作区列表。

    返回 [{workspaceId, path, title, sessionIds, createdAt, updatedAt}, ...]
    """
    wp = workspace_path()
    if not wp.is_file():
        return []
    try:
        raw = json.loads(wp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    tables = raw.get("tables") or {}
    workspaces = (tables.get("workspaces") or {})
    if not isinstance(workspaces, dict):
        return []
    out: list[dict[str, Any]] = []
    for wid, ws in workspaces.items():
        if not isinstance(ws, dict):
            continue
        entry = {"workspaceId": wid}
        for k in ("path", "title", "sessionIds", "createdAt", "updatedAt"):
            if k in ws:
                entry[k] = ws[k]
        out.append(entry)
    out.sort(key=lambda w: w.get("updatedAt", ""), reverse=True)
    return out


def create_workspace(path: str, title: str = "") -> dict[str, Any] | None:
    """在 webgui 的 workspace 注册表中登记一个工作区。

    路径须为已存在目录（同 webgui 的 workspace.create：fs.realpath 规范化、
    拒绝不存在/非目录、每个 canonical path 至多一条记录）。返回新建的工作区，
    已存在则返回现有记录。
    """
    p = Path(path).expanduser()
    if not p.is_dir():
        return None
    canonical = str(p.resolve())
    ws_list = list_workspaces()
    for ws in ws_list:
        if ws.get("path") == canonical or ws.get("path") == path:
            return ws
    import uuid
    wid = str(uuid.uuid4())
    now = _utc_now_iso()
    wp = workspace_path()
    data: dict[str, Any] = {}
    if wp.is_file():
        try:
            data = json.loads(wp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    tables = data.setdefault("tables", {})
    workspaces = tables.setdefault("workspaces", {})
    workspaces[wid] = {
        "path": canonical,
        "title": title or p.name,
        "sessionIds": [],
        "createdAt": now,
        "updatedAt": now,
    }
    data.setdefault("global", {})["workspaceIds"] = list(workspaces.keys())
    try:
        wp.parent.mkdir(parents=True, exist_ok=True)
        wp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return None
    return workspaces[wid]


def _utc_now_iso() -> str:
    """当前 UTC 时间 ISO8601（替代 datetime.utcnow().isoformat()）。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
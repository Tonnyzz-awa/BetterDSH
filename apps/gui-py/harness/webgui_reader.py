"""WebGUI 数据磁盘读取器。

pygui 与 webgui 共享同一套运行时后端，但传输层不同（stdio vs HTTP）。
通过共享磁盘读取 webgui 持久化的数据，是耦合最低的对接方式。

读取目标（默认 DSH_HOME = ~/.dsh 或 $DSH_HOME）：
  - settings.yaml      → API 配置（provider/model/reasoning_effort）
  - .credentials.yaml  → API Key
  - sessions/          → 会话历史（JSONL.zstd 格式）
  - storages/          → 工作区注册表（workspace.json）

用法:
    reader = WebguiReader()
    config = reader.read_api_config()       # {provider, model, reasoning_effort}
    creds = reader.read_credentials()       # {"DEEPSEEK_API_KEY": "sk-...", ...}
    sessions = reader.list_sessions()       # [{id, createdAt, cwd, agentPreset, ...}]
    events = reader.read_session(sid)       # {header: {...}, events: [...]}
    workspaces = reader.list_workspaces()   # [{workspaceId, path, title, sessionIds, ...}]
"""

from __future__ import annotations

import json
import os
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# 依赖可选项
# ---------------------------------------------------------------------------
_HAS_YAML = False
try:
    import yaml  # type: ignore[import-untyped]
    _HAS_YAML = True
except ImportError:
    pass
# 与 shared_backend 共用同一个“纯字符串” Loader，避免 off/on 被 YAML 解析成布尔
try:
    from .shared_backend import _load_yaml as _load_yaml  # noqa: F401
except ImportError:
    def _yaml_safe_load(text):
        import yaml as _y
        return _y.safe_load(text)
else:
    def _yaml_safe_load(text):
        return _load_yaml(text)

_HAS_ZSTD = False
try:
    import zstandard as _zstd  # type: ignore[import-untyped]
    _HAS_ZSTD = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DSH_HOME_DIR = ".dsh"
DSH_HOME_ENV = "DSH_HOME"
SETTINGS_FILE = "settings.yaml"
CREDENTIALS_FILE = ".credentials.yaml"
SESSIONS_DIR = "sessions"
STORAGES_DIR = "storages"
WORKSPACE_FILE = "workspace.json"
NO_CWD = "_no-cwd"


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------
class WebguiReaderError(RuntimeError):
    """读取 webgui 数据时出错。"""


class MissingDependencyError(WebguiReaderError):
    """缺少依赖包。"""


# ---------------------------------------------------------------------------
# 路径解析
# ---------------------------------------------------------------------------
def resolve_dsh_home() -> Path:
    """解析 DSH_HOME 路径（同 webgui 的 resolveDshHome 逻辑）。"""
    env = os.environ.get(DSH_HOME_ENV)
    if env and env.strip():
        base = env.strip()
    else:
        base = Path.home() / DSH_HOME_DIR
    return Path(base).expanduser().resolve()


def _encode_segment(raw: str) -> str:
    """会话 ID 的 filesystem-safe 编码（同 format.ts encodeSegment）。"""
    if not raw:
        raise ValueError("empty segment")
    if raw == ".":
        return "~002E"
    if raw == "..":
        return "~002E~002E"
    out = []
    for ch in raw:
        code = ord(ch)
        if ch != "~" and ch.isascii() and (ch.isalnum() or ch in "._-"):
            out.append(ch)
        else:
            out.append(f"~{code:04X}")
    return "".join(out)


def _project_key(cwd: str) -> str:
    """项目目录 key（同 format.ts projectKey）。"""
    readable = ""
    sep_run = False
    for ch in cwd:
        code = ord(ch)
        if ch in ("/", "\\", ":"):
            if not sep_run:
                readable += "-"
            sep_run = True
        elif ch != "~" and ch.isascii() and (ch.isalnum() or ch in "._-"):
            readable += ch
            sep_run = False
        else:
            readable += f"~{code:04X}"
            sep_run = False
    slug = readable.lstrip("-") or "root"
    return f"--{slug[:251]}--"


def _session_log_path(session_root: Path, cwd: str | None, session_id: str) -> Path:
    """构建会话日志路径（同 format.ts logPath）。"""
    project = _project_key(cwd) if cwd else NO_CWD
    return session_root / project / _encode_segment(session_id) / "session.jsonl.zstd"


# ---------------------------------------------------------------------------
# 读取器
# ---------------------------------------------------------------------------
class WebguiReader:
    """从 webgui 的 DSH_HOME 磁盘目录读取持久化数据。"""

    def __init__(self, dsh_home: str | Path | None = None):
        self._home = Path(dsh_home).expanduser().resolve() if dsh_home else resolve_dsh_home()
        self._settings_path = self._home / SETTINGS_FILE
        self._creds_path = self._home / CREDENTIALS_FILE
        self._sessions_root = self._home / SESSIONS_DIR
        self._storages_root = self._home / STORAGES_DIR
        self._workspace_path = self._storages_root / WORKSPACE_FILE

    # -- 属性 ---------------------------------------------------------------

    @property
    def home(self) -> Path:
        return self._home

    # -- API 配置 -----------------------------------------------------------

    def read_api_config(self) -> dict[str, Any]:
        """读取 settings.yaml → API 配置。

        返回:
            {provider, model, reasoning_effort, base_url, api_key_env}
            缺失字段不出现。
        """
        if not self._settings_path.is_file():
            return {}
        if not _HAS_YAML:
            raise MissingDependencyError(
                "需要 PyYAML 来解析 settings.yaml。运行: pip install pyyaml")

        raw = self._settings_path.read_text(encoding="utf-8")
        try:
            data = _yaml_safe_load(raw) or {}
        except _yaml.YAMLError as exc:
            raise WebguiReaderError(
                f"settings.yaml 解析失败: {exc}") from exc

        config: dict[str, Any] = {}

        # agent-default-model 节
        adm = data.get("agent-default-model") or {}
        if isinstance(adm, dict):
            for k in ("provider", "model", "reasoningEffort"):
                if k in adm:
                    config[k] = adm[k]

        # 从 llm-deepseek / llm-pi-ai 节补充 base_url 等
        for ns in ("llm-deepseek", "llm-pi-ai"):
            section = data.get(ns) or {}
            if isinstance(section, dict):
                if "baseURL" in section:
                    config["base_url"] = section["baseURL"]
                if "apiKeyEnv" in section:
                    config["api_key_env"] = section["apiKeyEnv"]

        return config

    # -- 凭据 ---------------------------------------------------------------

    def read_credentials(self) -> dict[str, str]:
        """读取 .credentials.yaml → API Key 映射。

        返回:
            {"DEEPSEEK_API_KEY": "sk-...", "OPENAI_API_KEY": "sk-...", ...}
        """
        if not self._creds_path.is_file():
            return {}
        if not _HAS_YAML:
            raise MissingDependencyError(
                "需要 PyYAML 来解析 .credentials.yaml。运行: pip install pyyaml")

        raw = self._creds_path.read_text(encoding="utf-8")
        try:
            data = _yaml_safe_load(raw) or {}
        except _yaml.YAMLError as exc:
            raise WebguiReaderError(
                f".credentials.yaml 解析失败: {exc}") from exc

        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}

    # -- 会话历史 -----------------------------------------------------------

    def list_sessions(self) -> list[dict[str, Any]]:
        """列举所有会话（只读 header，不解析事件）。

        遍历 sessions/ 目录下每个 session.jsonl.zstd 文件，
        读取第一行（JSON header） → 返回会话元信息列表。

        返回:
            [{id, createdAt, cwd, delegationDepth, agentPreset, projectKey, ...}, ...]
        """
        if not self._sessions_root.is_dir():
            return []
        if not _HAS_ZSTD:
            raise MissingDependencyError(
                "需要 zstandard 来解压会话日志。运行: pip install zstandard")

        sessions: list[dict[str, Any]] = []
        dctx = _zstd.ZstdDecompressor()

        for zstd_path in self._sessions_root.rglob("session.jsonl.zstd"):
            if not zstd_path.is_file():
                continue
            try:
                header = self._read_header_line(zstd_path, dctx)
                if header:
                    sessions.append(header)
            except Exception:
                continue  # 跳过损坏的会话

        # 按 createdAt 降序
        sessions.sort(key=lambda s: s.get("createdAt", 0), reverse=True)
        return sessions

    def _read_header_line(self, zstd_path: Path, dctx: _zstd.ZstdDecompressor) -> dict[str, Any] | None:
        """从 zstd 压缩文件中读取第一行（session header）并解析。"""
        with open(zstd_path, "rb") as f:
            # 跳过帧头读取第一行
            reader = dctx.stream_reader(f)
            line = b""
            while True:
                c = reader.read(1)
                if not c or c == b"\n":
                    break
                line += c
            if not line:
                return None
            parsed = json.loads(line.decode("utf-8"))
            if not isinstance(parsed, dict) or parsed.get("type") != "session":
                return None
            # 添加 project key 信息
            parsed["projectKey"] = zstd_path.parent.parent.name
            return parsed

    def read_session(self, session_id: str) -> dict[str, Any] | None:
        """读取指定 ID 的完整会话内容。

        搜索所有 session.jsonl.zstd 文件，匹配 header 中的 id 字段。

        返回:
            {header: {...}, events: [{...}, ...]}
            或 None（未找到）。
        """
        if not self._sessions_root.is_dir():
            return None
        if not _HAS_ZSTD:
            raise MissingDependencyError(
                "需要 zstandard 来解压会话日志。运行: pip install zstandard")

        dctx = _zstd.ZstdDecompressor()

        for zstd_path in self._sessions_root.rglob("session.jsonl.zstd"):
            if not zstd_path.is_file():
                continue
            try:
                result = self._read_session_file(zstd_path, dctx, session_id)
                if result is not None:
                    return result
            except Exception:
                continue
        return None

    def read_session_by_path(self, zstd_path: str | Path) -> dict[str, Any] | None:
        """直接读取指定路径的会话文件。

        返回:
            {header: {...}, events: [{...}, ...]}
            或 None（文件不存在或损坏）。
        """
        p = Path(zstd_path)
        if not p.is_file():
            return None
        if not _HAS_ZSTD:
            raise MissingDependencyError(
                "需要 zstandard 来解压会话日志。运行: pip install zstandard")

        dctx = _zstd.ZstdDecompressor()
        try:
            return self._read_session_file(p, dctx, match_id=None)
        except Exception:
            return None

    def _read_session_file(
        self, zstd_path: Path, dctx: _zstd.ZstdDecompressor, match_id: str | None
    ) -> dict[str, Any] | None:
        """读取一个会话文件，如匹配则返回头+事件。"""
        with open(zstd_path, "rb") as f:
            # webgui 的 zstd 帧头可能不含 content size，用 stream_reader 逐块解压
            reader = dctx.stream_reader(f)
            raw = reader.read()
            data = raw

        text = data.decode("utf-8")
        lines = text.splitlines()
        if not lines:
            return None

        # 解析 header
        header = json.loads(lines[0])
        if not isinstance(header, dict) or header.get("type") != "session":
            return None
        if match_id is not None and header.get("id") != match_id:
            return None

        # 解析事件行
        events: list[dict[str, Any]] = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                if isinstance(ev, dict):
                    events.append(ev)
            except json.JSONDecodeError:
                continue

        return {"header": header, "events": events}

    # -- 工作区 -------------------------------------------------------------

    def list_workspaces(self) -> list[dict[str, Any]]:
        """读取 workspace.json → 工作区列表。

        返回:
            [{workspaceId, path, title, sessionIds, createdAt, updatedAt}, ...]
        """
        if not self._workspace_path.is_file():
            return []
        try:
            raw = json.loads(self._workspace_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise WebguiReaderError(
                f"workspace.json 解析失败: {exc}") from exc

        tables = raw.get("tables") or {}
        workspaces = (tables.get("workspaces") or {})
        result: list[dict[str, Any]] = []
        for wid, ws in workspaces.items():
            entry = {"workspaceId": wid}
            if isinstance(ws, dict):
                for k in ("path", "title", "sessionIds", "createdAt", "updatedAt"):
                    if k in ws:
                        entry[k] = ws[k]
            result.append(entry)
        return result

    # -- 便捷入口：读取 webgui 的完整配置 ---------------------------------

    def read_all(self) -> dict[str, Any]:
        """一次性读取所有 webgui 数据。

        返回:
            {config, credentials, sessions, workspaces}
        """
        config = self.read_api_config()
        creds = self.read_credentials()
        sessions = self.list_sessions()
        workspaces = self.list_workspaces()
        return {
            "config": config,
            "credentials": creds,
            "sessions": sessions,
            "workspaces": workspaces,
        }


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------
def quick_read() -> dict[str, Any]:
    """快速读取所有 webgui 数据（单行入口）。"""
    return WebguiReader().read_all()


def read_api_config() -> dict[str, Any]:
    """快速读取 API 配置。"""
    return WebguiReader().read_api_config()


def read_credentials() -> dict[str, str]:
    """快速读取凭据。"""
    return WebguiReader().read_credentials()


def list_sessions() -> list[dict[str, Any]]:
    """快速列举会话。"""
    return WebguiReader().list_sessions()


def read_session(session_id: str) -> dict[str, Any] | None:
    """快速读取指定会话。"""
    return WebguiReader().read_session(session_id)


def list_workspaces() -> list[dict[str, Any]]:
    """快速列举工作区。"""
    return WebguiReader().list_workspaces()


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pprint

    print("=" * 60)
    print("WebguiReader 自测")
    print(f"DSH_HOME: {WebguiReader().home}")
    print("=" * 60)

    reader = WebguiReader()

    print("\n--- API 配置 ---")
    pprint.pprint(reader.read_api_config())

    print("\n--- 凭据 ---")
    creds = reader.read_credentials()
    # 脱敏显示
    safe = {k: v[:10] + "…" if len(v) > 10 else v for k, v in creds.items()}
    pprint.pprint(safe)

    print("\n--- 会话列表 ---")
    sessions = reader.list_sessions()
    for s in sessions[:5]:
        created = datetime.fromtimestamp(s["createdAt"] / 1000, tz=timezone.utc)
        print(f"  {s['id']}  {created.isoformat()}  cwd={s.get('cwd','?')}  "
              f"preset={s.get('agentPreset','?')}")

    print(f"\n  共 {len(sessions)} 个会话")

    if sessions:
        print(f"\n--- 读取最新会话: {sessions[0]['id']} ---")
        full = reader.read_session(sessions[0]["id"])
        if full:
            header = full["header"]
            events = full["events"]
            types = [e.get("type", "?") for e in events]
            print(f"  事件数: {len(events)}")
            print(f"  事件类型: {types[:8]}{'...' if len(types) > 8 else ''}")

    print("\n--- 工作区 ---")
    pprint.pprint(reader.list_workspaces())

    print("\n✓ 自测完成")
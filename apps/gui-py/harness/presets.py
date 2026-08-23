"""动态读取 agent preset（harness 模式）。

与 webgui 的 dsh-agent-presets discovery 一致：一个 preset 是
`<dshHome>/.agent-presets/`（及随附根目录）下的一个目录，目录名即 preset id，
旁附可选的 `preset.yml` 携带显示元数据（name/description/order）。

每次调用都重新扫描磁盘，因此用户/Agent 新创建的 preset 无需重启即可见。

本模块只负责发现，不限定 UI；设置对话框据此填充"Harness 模式"下拉。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .shared_backend import resolve_dsh_home

# 目录名须匹配才视为一个 preset 槽位（同 PRESET_ID）
_PRESET_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# 组成文件：目录内必须有它才算 preset（同 COMPOSITION_FILE）
COMPOSITION_FILE = "agent.cordis.yml"
# 可选显示元数据（同 METADATA_FILE）
METADATA_FILE = "preset.yml"
# 个人自有 preset 目录（同 USER_PRESET_DIR）
USER_PRESET_DIR = ".agent-presets"


class Preset:
    """一个 agent preset 的发现结果。"""

    def __init__(
        self,
        *,
        id: str,
        name: str,
        description: str = "",
        order: int | None = None,
        path: Path,
        trust: str = "user",
    ):
        self.id = id
        self.name = name
        self.description = description
        self.order = order
        self.path = path
        self.trust = trust

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "trust": self.trust,
        }
        if self.description:
            d["description"] = self.description
        if self.order is not None:
            d["order"] = self.order
        return d

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Preset {self.id!r} name={self.name!r}>"


def _read_metadata(directory: Path) -> tuple[str, str, int | None]:
    """读一个 preset 目录的 preset.yml，返回 (name, description, order)。

    缺失/损坏/形状错误都回退到 id / 空 / None，与 webgui 一致：显示文本
    缺失不能让一个能挂载的 preset 变成不可用。
    """
    mf = directory / METADATA_FILE
    if not mf.is_file():
        return directory.name, "", None
    try:
        text = mf.read_text(encoding="utf-8")
        data = _load_yaml(text) or {}
    except BaseException:
        return directory.name, "", None
    if not isinstance(data, dict):
        return directory.name, "", None

    def _str(v: Any) -> str:
        return v.strip() if isinstance(v, str) and v.strip() else ""

    name = _str(data.get("name")) or directory.name
    desc = _str(data.get("description"))
    order = data.get("order")
    order = int(order) if isinstance(order, (int, float)) and not isinstance(order, bool) else None
    return name, desc, order


def _load_yaml(text: str) -> Any:
    """用纯字符串 Loader 解析 YAML（避免 off/on/yes/no 变成布尔）。"""
    from .shared_backend import _load_yaml as _shared_load
    return _shared_load(text)


def user_preset_root() -> Path:
    """个人自有 preset 根目录（默认 ~/.dsh/.agent-presets）。"""
    return resolve_dsh_home() / USER_PRESET_DIR


def _scan_dir(root: Path, trust: str) -> list[Preset]:
    """扫描一个根目录，返回其下所有合法 preset 目录。"""
    found: list[Preset] = []
    if not root.is_dir():
        return found
    try:
        children = list(root.iterdir())
    except OSError:
        return found
    for child in children:
        if not child.is_dir():
            continue
        if not _PRESET_ID.match(child.name):
            continue
        # 目录内须有组成文件才算 preset（_preset 模板目录会被跳过）
        if not (child / COMPOSITION_FILE).is_file():
            continue
        name, desc, order = _read_metadata(child)
        found.append(Preset(
            id=child.name, name=name, description=desc, order=order,
            path=child, trust=trust,
        ))
    # 先按 order 排（缺失视为正无穷），再按 id
    found.sort(key=lambda p: (p.order if p.order is not None else float("inf"), p.id))
    return found


def list_presets() -> list[Preset]:
    """动态列举当前可用的 agent preset（harness 模式）。

    读取个人自有根目录（~/.dsh/.agent-presets/），返回按 order+id 排序的列表。
    每次调用重扫磁盘，实时反映新增的 preset。
    """
    return _scan_dir(user_preset_root(), "user")


def list_preset_options() -> list[dict[str, Any]]:
    """设置下拉用的简化形式：已按序排列的 {id, name, description}。"""
    return [p.as_dict() for p in list_presets()]


if __name__ == "__main__":  # pragma: no cover - debug 自测
    import pprint
    opts = list_preset_options()
    print(f"发现 {len(opts)} 个 preset：")
    pprint.pprint(opts)
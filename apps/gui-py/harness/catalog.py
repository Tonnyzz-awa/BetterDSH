"""从已安装的 pi-ai 目录动态读取供应商及模型列表。

模型清单不写死在代码里：只要 deepseek-harness 仓库更新了 pi-ai 或
其中的 providers 数据，GUI 的模型下拉就会自动跟着变。

数据来源：node_modules 里 @earendil-works/pi-ai 的
dist/providers/data/*.json。每个文件顶层是协议名（如
openai-completions），每个模型的 `provider` 字段才是路由 id。
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path


def pi_data_dir(repo: Path) -> Path | None:
    """定位 pi-ai 的 providers/data 目录；找不到返回 None。"""
    candidates = []
    pattern = repo / "node_modules" / ".pnpm" / "@earendil-works+pi-ai@*" / "node_modules" / "@earendil-works" / "pi-ai" / "dist" / "providers" / "data"
    matches = glob.glob(os.fspath(pattern))
    candidates.extend(Path(m) for m in matches)
    # pnpm 也可能没有 .pnpm 目录（hoisted 布局）
    candidates.append(repo / "node_modules" / "@earendil-works" / "pi-ai" / "dist" / "providers" / "data")
    for cand in candidates:
        if cand.is_dir():
            return cand
    return None


def _load_provider_index(data_dir: Path) -> dict[str, list[dict]]:
    """把 data/*.json 聚合成 {provider_id: [{id, name}]}（保持文件顺序）。"""
    index: dict[str, list[dict]] = {}
    for f in sorted(data_dir.glob("*.json")):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(raw, dict):
            continue
        for protocol, models in raw.items():
            if not isinstance(models, dict):
                continue
            for mid, model in models.items():
                if not isinstance(model, dict):
                    continue
                provider = model.get("provider")
                if not isinstance(provider, str):
                    continue
                name = model.get("name")
                tlm = model.get("thinkingLevelMap", {})
                levels = [k for k, v in tlm.items() if v is not None] if isinstance(tlm, dict) else []
                names = index.setdefault(provider, [])
                entry = {"id": mid, "name": name if isinstance(name, str) and name else mid}
                if levels:
                    entry["thinkingLevels"] = levels
                names.append(entry)
    _merge_override(index)
    return index


def _merge_override(index: dict[str, list[dict]]) -> None:
    """把本地 data/models.override.json 的模型并入目录，保证重装依赖后仍在。

    override 文件格式：{provider_id: [{id, name, thinkingLevels}]}。
    只补入目录里没有的 id，已有 id 不覆盖，避免重复。
    """
    p = Path(__file__).resolve().parent.parent / "data" / "models.override.json"
    if not p.is_file():
        return
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if not isinstance(raw, dict):
        return
    for provider, models in raw.items():
        if not isinstance(models, list):
            continue
        existing = {m["id"] for m in index.get(provider, []) if isinstance(m, dict) and m.get("id")}
        bucket = index.setdefault(provider, [])
        for m in models:
            if not isinstance(m, dict) or not m.get("id") or m["id"] in existing:
                continue
            entry = {"id": m["id"], "name": m.get("name") or m["id"]}
            if isinstance(m.get("thinkingLevels"), list) and m["thinkingLevels"]:
                entry["thinkingLevels"] = m["thinkingLevels"]
            bucket.append(entry)
            existing.add(m["id"])


def list_available_providers(repo: Path) -> dict[str, list[dict]]:
    """返回 pi-ai 内置目录中所有 provider -> 模型列表；目录缺失时为空。"""
    d = pi_data_dir(repo)
    return _load_provider_index(d) if d is not None else {}


def provider_models(repo: Path, provider_id: str) -> list[str]:
    """单个 provider 的模型 id 列表（可空）。"""
    return [m["id"] for m in list_available_providers(repo).get(provider_id, [])]


def default_model_for_provider(repo: Path, provider_id: str) -> str:
    """给出该 provider 的动态默认模型。"""
    pid = "deepseek" if provider_id == "deepseek-official" else provider_id
    models = provider_models(repo, pid)
    return models[0] if models else ""


def reasoning_levels(repo: Path, provider_id: str, model_id: str) -> list[str]:
    """从 pi-ai 目录获取该 provider/model 的思考强度档位（官方值）。"""
    pid = "deepseek" if provider_id == "deepseek-official" else provider_id
    index = list_available_providers(repo)
    for m in index.get(pid, []):
        if m["id"] == model_id:
            return m.get("thinkingLevels", [])
    return []
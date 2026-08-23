"""生成 dsh-gui 的 cordis.yml 组合文件。

基于所选供应商渲染配置：
- deepseek-official（默认）：只挂官方适配器（llm-deepseek），不挂 pi-ai
- pi-ai 供应商（openai, anthropic 等）：挂官方 + 该供应商路由（省略 models，
  运行时自动使用 pi-ai 内置目录，模型列表由此动态获得、不写死在代码里）
- custom：挂官方 + 自定义 OpenAI 兼容端点路由（模型由用户填写）
"""

from __future__ import annotations

import sys
from pathlib import Path

PYTHON_SHELL_PKG = "@deepseek-ai/dsh-pwsh-local" if sys.platform == "win32" else "@deepseek-ai/dsh-bash-local"
PYTHON_SHELL_ID = "pwsh" if sys.platform == "win32" else "bash"

# 供应商清单（下拉框来源）。模型列表由 catalog.py 从已安装 pi-ai 目录动态读取。
DEEPSEEK_OFFICIAL = {
    "id": "deepseek-official",
    "name": "DeepSeek 官方",
    "env": "DEEPSEEK_API_KEY",
}

PI_PROVIDERS = [
    {"id": "openai",     "name": "OpenAI",         "env": "OPENAI_API_KEY"},
    {"id": "anthropic",  "name": "Anthropic",      "env": "ANTHROPIC_API_KEY"},
    {"id": "deepseek",   "name": "DeepSeek（pi-ai）", "env": "DEEPSEEK_API_KEY"},
    {"id": "google",     "name": "Google Gemini",  "env": "GOOGLE_API_KEY"},
    {"id": "groq",       "name": "Groq",           "env": "GROQ_API_KEY"},
    {"id": "mistral",    "name": "Mistral",        "env": "MISTRAL_API_KEY"},
    {"id": "xai",        "name": "xAI (Grok)",     "env": "XAI_API_KEY"},
    {"id": "openrouter", "name": "OpenRouter",     "env": "OPENROUTER_API_KEY"},
]

CUSTOM_PROVIDER = {
    "id": "custom",
    "name": "自定义 (OpenAI 兼容)",
    "env": "CUSTOM_API_KEY",
}

ALL_PROVIDERS = [DEEPSEEK_OFFICIAL, *PI_PROVIDERS, CUSTOM_PROVIDER]

# 供应商 id -> 环境变量名
PROVIDER_ENV: dict[str, str] = {p["id"]: p["env"] for p in ALL_PROVIDERS}


def render_config(
    *,
    provider_id: str = "deepseek-official",
    base_url: str | None = None,
    custom_models: list[str] | None = None,
    extra_entries: list[str] | None = None,
) -> str:
    """渲染运行时组合文件。

    provider_id 决定挂载哪些适配器：
    - deepseek-official: 仅官方 llm-deepseek
    - pi-ai 供应商: 官方 + 该供应商路由（省略 models -> 运行时用内置目录）
    - custom: 官方 + 自定义端点路由（模型列表由用户填写）

    `extra_entries` 是要追加的原版 Cordis 插件条目（每个元素一段 YAML，例如
    "- id: my-plugin\n  name: '@scope/pkg'\n  config:\n    key: value"）。
    这使 GUI 驱动的运行时可挂载仓库内的任意原版插件，与官方 dsh --profile
    使用的独立 cordis 文件互不冲突。
    """
    lines = [
        "# dsh-gui runtime (由 config.py 生成，请勿手改)",
        "",
        "# --- dsh-gui 固定条目 ---",
        "- id: sdk-jsonrpc-server",
        "  name: '@deepseek-ai/dsh-sdk-jsonrpc-server'",
        "",
        "- id: agent-core",
        "  name: '@deepseek-ai/dsh-agent-spine-demo'",
        "  config:",
        "    workspaceContext:",
        "      maxBytes: 65536",
        "",
        "- id: llm-deepseek",
        "  name: '@deepseek-ai/dsh-llm-deepseek'",
        "",
    ]

    route = _pi_route_for(provider_id, base_url, custom_models)
    if route is not None:
        lines.append(route)
        lines.append("")

    lines.extend([
        "- id: sessions",
        "  name: '@deepseek-ai/dsh-session-persistence-jsonl'",
        "  config:",
        "    root: !!js process.env.DSH_SESSION_ROOT ?? './data/sessions'",
        "",
        "- id: session-checkpoints",
        "  name: '@deepseek-ai/dsh-session-checkpoint-policy'",
        "",
        "- id: subprocess",
        "  name: '@deepseek-ai/dsh-subprocess-local'",
        "",
        f"- id: {PYTHON_SHELL_ID}",
        f"  name: '{PYTHON_SHELL_PKG}'",
        "  config:",
        "    cwd: !!js process.env.DSH_CWD ?? process.cwd()",
        "",
        "- id: fs-local",
        "  name: '@deepseek-ai/dsh-fs-local'",
        "  config:",
        "    cwd: !!js process.env.DSH_CWD ?? process.cwd()",
        "",
    ])

    # --- 原版插件追加区（可空） ---
    if extra_entries:
        lines.append("# --- 用户追加的原版插件 ---")
        for entry in extra_entries:
            if entry and not entry.isspace():
                lines.append(entry.rstrip())
                lines.append("")

    return "\n".join(lines)


def _yaml_model(model: str) -> str:
    return f"          - id: {model}"


def _pi_route_for(
    provider_id: str, base_url: str | None, custom_models: list[str] | None
) -> str | None:
    """生成 llm-pi-ai 的 providers 段；官方适配器不需要。"""
    if provider_id == "deepseek-official":
        return None

    env = PROVIDER_ENV.get(provider_id, "CUSTOM_API_KEY")

    if provider_id == "custom" and base_url:
        models = custom_models or ["custom-model"]
        route = (
            "- id: llm-pi-ai\n"
            "  name: '@deepseek-ai/dsh-llm-pi-ai'\n"
            "  config:\n"
            "    providers:\n"
            "      custom:\n"
            f"        apiKeyEnv: {env}\n"
            "        api: openai-completions\n"
            f"        baseURL: {base_url}\n"
            "        models:"
        )
        for m in models:
            route += f"\n{_yaml_model(m)}"
        return route

    # pi-ai 目录路由：省略 models -> 运行时使用安装好的 pi-ai 内置模型目录
    return (
        "- id: llm-pi-ai\n"
        "  name: '@deepseek-ai/dsh-llm-pi-ai'\n"
        "  config:\n"
        "    providers:\n"
        f"      {provider_id}:\n"
        f"        apiKeyEnv: {env}"
    )


def write_config(path, *, provider_id: str = "deepseek-official",
                 base_url: str | None = None,
                 custom_models: list[str] | None = None,
                 extra_entries: list[str] | None = None) -> str:
    """按设置渲染组合文件并写盘。"""
    text = render_config(provider_id=provider_id, base_url=base_url,
                         custom_models=custom_models, extra_entries=extra_entries)
    path.write_text(text, encoding="utf-8")
    return text


def load_extra_entries(gui_root) -> list[str]:
    """读取 dsh-gui 目录下 `data/plugins.entries.yml` 里的追加插件文本。

    该文件不是标准 cordis 文件格式（避免兼容性问题），而是**一段文本**：
    以 `- id:` 开头的 entry 行，可直接透传给 render_config 的 extra_entries。
    缺失或空文件返回 []。
    """
    p = Path(gui_root) / "data" / "plugins.entries.yml"
    try:
        content = p.read_text(encoding="utf-8")
    except OSError:
        return []
    return [line.rstrip() for line in content.splitlines() if line.strip()]


def provider_env_id(provider_id: str) -> str | None:
    return PROVIDER_ENV.get(provider_id)
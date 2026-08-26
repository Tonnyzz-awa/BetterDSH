"""dsh-gui 启动器: 定位仓库、准备依赖、启动/停止 harness 运行时。

运行时启动方式（源码模式）:
    node --import tsx/esm <repo>/packages/examples/jsonrpc-demo/src/bin.ts <config>

源码模式依赖仓库已 `corepack pnpm install`（node_modules 存在）。
本模块提供 `probe_prereqs()` 检查 + `start_runtime()` 拉起 + `stop_runtime()` 关闭。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .config import render_config
from .rpc import HarnessRpcClient
from .settings import env_name_for_provider

# 官方 rxO 用法: 配置文件路径挂环境变量或 argv。 我们走 argv。
DEMO_ENTRY = "packages/examples/jsonrpc-demo/src/bin.ts"
# 会话根与 webgui 共用：默认放到 DSH_HOME/sessions，与 settings.yaml 同根。
from .shared_backend import session_root as _shared_session_root  # noqa: E402

SESSION_ROOT = "data/sessions"  # 兜底（未走 shared_backend 时的旧值）

# 端口无关; 仅本次子进程的 stdio
# 融合后本模块位于 <repo>/apps/gui-py/harness/launcher.py，仓库根为向上三级。
DEFAULT_REPO = Path(__file__).resolve().parents[3]


def resolve_repo(explicit: str | None = None) -> Path:
    """解析仓库根：显式参数 > 环境变量 DSH_REPO > 融合后的自身上级目录。"""
    if explicit:
        return Path(explicit).resolve()
    env = os.environ.get("DSH_REPO")
    if env:
        return Path(env).resolve()
    return DEFAULT_REPO

# 唤醒超时: 首次 boot 需要几十秒（编译+加载）
LAUNCH_TIMEOUT_S = 120


class HarnessUnavailable(RuntimeError):
    """前置条件不满足: 缺少 node / repo / 依赖。"""


def _find_repo(explicit: str | None) -> Path:
    """解析仓库路径: 显式参数 > 环境变量 DSH_REPO > 融合后的上级仓库根。"""
    return resolve_repo(explicit)


def _node_cmd() -> list[str]:
    """返回可用的 node 启动向量。优先本机 node，其次 corepack。"""
    node = shutil.which("node")
    if node:
        return [node]
    corepack = shutil.which("corepack")
    if corepack:
        return [corepack, "node"]
    raise HarnessUnavailable("未找到 node；请安装 Node.js ≥ 22.19")


def probe_prereqs(repo: Path) -> list[dict]:
    """探测运行前置条件，返回 [(name, ok, message)]。探测不应抛异常。"""
    checks = []
    try:
        node_bin = _node_cmd()
        checks.append(("node", True, " ".join(node_bin)))
    except HarnessUnavailable as exc:
        checks.append(("node", False, str(exc)))
    checks.append(("repo", repo.is_dir(), str(repo)))
    if repo.is_dir():
        has_module = (repo / "node_modules").is_dir()
        checks.append(("deps", has_module, "node_modules" if has_module else "缺失，需 corepack pnpm install"))
        demo = repo / DEMO_ENTRY
        checks.append(("demo-entry", demo.is_file(), str(demo) if demo.is_file() else "缺失"))
    return checks


def ensure_deps(repo: Path, *, echo=print, timeout=None) -> None:
    """在仓库根安装依赖（若 node_modules 缺失）。

    跨平台：优先 pnpm，其次 corepack 托管，再次 npx。Windows 上 pnpm/corepack
    多为 .cmd 包装，必须经 cmd.exe 解析（shell=True），直接当可执行会 OSError。
    """
    nm = repo / "node_modules"
    if nm.is_dir():
        echo("依赖已就绪")
        return
    echo("未安装依赖，开始安装 …")
    candidates = ["pnpm install", "corepack pnpm install", "npx -y pnpm install"]
    last_err: BaseException | None = None
    for cmd in candidates:
        try:
            subprocess.run(
                cmd,
                cwd=repo,
                shell=True,
                timeout=timeout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            return
        except subprocess.CalledProcessError as exc:
            last_err = exc
            echo(f"{cmd} 失败（exit {exc.returncode}），尝试备选方案 …")
        except OSError as exc:
            last_err = exc
            echo(f"无法执行 {cmd}：{exc}")
    raise HarnessUnavailable(f"依赖安装失败：{last_err}")


def _resolve_tsx_import(repo: Path) -> str:
    """解析 node --import 用的 tsx loader。

    pnpm 默认不把 devDependency（tsx）提升到仓库根 node_modules，
    裸 specifier `tsx/esm` 会报 ERR_MODULE_NOT_FOUND 而秒退。
    优先用裸 specifier（根 node_modules 存在时），否则在 .pnpm 中找到
    tsx 并按其 exports["./esm"] 解析到真实文件绝对路径。
    """
    if (repo / "node_modules" / "tsx" / "package.json").is_file():
        return "tsx/esm"
    pnpm_dir = repo / "node_modules" / ".pnpm"
    if pnpm_dir.is_dir():
        for cand in sorted(pnpm_dir.glob("tsx@*/node_modules/tsx"), reverse=True):
            pkg = cand / "package.json"
            if not pkg.is_file():
                continue
            try:
                exports = json.loads(pkg.read_text(encoding="utf-8")).get("exports", {})
            except (json.JSONDecodeError, OSError):
                continue
            target = exports.get("./esm")
            if isinstance(target, dict):
                target = target.get("import") or target.get("default") \
                    or next(iter(target.values()), None)
            if not target or not isinstance(target, str):
                continue
            loader = (cand / target).resolve()
            if loader.is_file():
                return loader.as_uri()  # Windows 上 --import 需要 file:// URL
    raise HarnessUnavailable(
        "未找到 tsx 加载器。请在仓库根执行 corepack pnpm install 后再启动运行时。")


def start_runtime(
    *,
    repo: Path,
    config_path: Path,
    session_root: Path,
    api_key: str | None = None,
    provider: str | None = None,
) -> tuple[subprocess.Popen, HarnessRpcClient]:
    """在 `repo` 中启动 JSON-RPC 运行时子进程，返回 (proc, rpc)。

    `api_key` 属于当前所选供应商: 仅注入该供应商对应的环境变量名,
    避免把 key 塞错位置。`provider` 用于 `wait_ready` 握手时告知
    运行时该路由已注册（deepseek-official 会自动降级挂适配器）。
    """
    env = os.environ.copy()
    env.setdefault("DSH_SESSION_ROOT", str(session_root))
    env_name = env_name_for_provider(provider) if provider else None
    env_name = env_name or "DEEPSEEK_API_KEY"  # 兜底: 未知 provider 退回官方
    if api_key:
        env[env_name] = api_key
    else:
        env.pop(env_name, None)  # 避免继承来的垃圾 key

    entry = repo / DEMO_ENTRY
    cmd = [*_node_cmd(), "--import", _resolve_tsx_import(repo),
           str(entry), str(config_path)]
    popen_kwargs = dict(
        cwd=str(repo),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    if os.name == "nt":
        # 必须开新进程组: 否则 node 子进程留在 Python 父进程组,
        # dsh 运行时 boot 在加载 cordis 插件树时死锁(仅后台/无控制台启动会触发),
        # 实测 CREATE_NEW_CONSOLE 会崩(STATUS_CONTROL_C_EXIT)且弹窗。
        # 同时 CREATE_NO_WINDOW 抑制弹窗。两者组合: 既避开死锁又无可见窗口。
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    proc = subprocess.Popen(cmd, **popen_kwargs)
    rpc = HarnessRpcClient(
        read=proc.stdout,
        write=proc.stdin,
        notify_cb=None,
    ).start()
    return proc, rpc


def wait_ready(rpc: HarnessRpcClient, *, timeout: float = LAUNCH_TIMEOUT_S,
               echo=print, stderr_lines=None,
               provider: str | None = None, model: str | None = None,
               repo: Path | None = None,
               reasoning_effort: str | None = None) -> dict:
    """等待运行时可用: 发 initialize 握手, 成功即就绪; 返回握手结果。

    `provider`/`model` 决定 runtime 为该会话路由的模型:
    - deepseek-official 未注册适配器时 runtime 自动挂官方适配器
    - 其他 provider 必须已由 llm-pi-ai 路由声明 (config.py 已渲染)
    模型为空时，从已装 pi-ai 目录动态解析该 provider 的默认模型（不写死），
    `repo` 指定读取模型目录用的仓库根（默认融合后的仓库根）。
    `reasoning_effort` 可选思考强度等级（如 'off', 'low', 'medium', 'high', 'max'）。
    失败时把 stderr 尾部放进异常消息, 便于定位。
    """
    deadline = time.monotonic() + timeout
    last_exc = None
    target_provider = provider or "deepseek-official"
    target_model = model
    if not target_model:
        try:
            from .catalog import default_model_for_provider
            target_model = default_model_for_provider(repo or DEFAULT_REPO, target_provider)
        except BaseException:
            target_model = ""
    while time.monotonic() < deadline:
        try:
            result = rpc.request(
                "initialize",
                {"cwd": str(Path.cwd()),
                 "provider": target_provider,
                 "model": target_model or target_provider,
                 **({"reasoningEffort": reasoning_effort} if reasoning_effort else {})},
                timeout=5,
            )
            echo(f"运行时就绪: {result}")
            return result or {}
        except TimeoutError as exc:
            last_exc = exc
            echo("等待运行时…")
        except Exception as exc:  # 服务器返回错误通常表示未完全启动
            last_exc = exc
            echo(f"握手失败: {exc}")
            time.sleep(0.5)
    tail = ""
    if stderr_lines:
        tail = "\n".join(stderr_lines[-30:])
    raise HarnessUnavailable(
        f"等待运行时就绪超时（{timeout}s）。最后错误: {last_exc}"
        + (f"\n--- 运行时 stderr 尾部 ---\n{tail}" if tail else "")
    )


def provider_hint(provider: str | None) -> str:
    """给 UI 状态条用的一句话说明。"""
    if provider == "deepseek-official":
        return "DeepSeek 官方"
    return provider or "DeepSeek 官方"


def stop_runtime(proc: subprocess.Popen, rpc: HarnessRpcClient, *, timeout: float = 10) -> None:
    """优雅关闭: 先发 shutdown，再终止进程。"""
    try:
        rpc.request("shutdown", None, timeout=5)
    except Exception:
        pass
    try:
        rpc.close()
    except Exception:
        pass
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
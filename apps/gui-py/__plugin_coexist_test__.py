"""端到端验证: GUI 运行时 + 追加原版插件共存（开发自检，非交付）。

把 dsh-gui 的配置渲染出来，再用 extra_entries 追加原版 tool-fs / tool-todo，
启动运行时确认整棵树能加载（不冲突）。无 API key 时只验证启动+握手，不对话。
"""
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from harness.config import load_extra_entries, write_config
from harness.launcher import DEFAULT_REPO, start_runtime, wait_ready, stop_runtime


def main() -> int:
    # 1) GUI 原生的配置 + 追加原版插件条目
    config = ROOT / "data" / "runtime-plugin-test.cordis.yml"
    entries = [
        "- id: tool-fs",
        "  name: '@deepseek-ai/dsh-tool-fs'",
        "",
        "- id: tool-todo",
        "  name: '@deepseek-ai/dsh-tool-todo'",
        "  config:",
        "    allowParallelInProgress: true",
        "",
    ]
    write_config(config, provider_id="deepseek-official", extra_entries=entries)

    # 快速验证生成内容
    text = config.read_text(encoding="utf-8")
    assert "tool-fs" in text and "@deepseek-ai/dsh-tool-fs" in text
    assert "tool-todo" in text and "allowParallelInProgress" in text
    print("[config] 追加原版插件条目 OK")

    # 2) 启动并确认加载（若 plugins 冲突会在 stderr 崩掉）
    sessions = ROOT / "data" / "sessions"
    proc, rpc = start_runtime(repo=DEFAULT_REPO, config_path=config,
                             session_root=sessions, api_key=None)
    stderr_lines: list[str] = []

    def drain():
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_lines.append(line.rstrip())

    threading.Thread(target=drain, daemon=True).start()
    try:
        try:
            wait_ready(rpc, timeout=40, echo=lambda s: print(f"[boot] {s}"),
                       stderr_lines=stderr_lines, provider="deepseek-official",
                       repo=DEFAULT_REPO)
        except Exception:
            print("---- stderr 尾部 ----")
            for ln in stderr_lines[-60:]:
                print("  |", ln)
            raise
        print("[boot] GUI 运行时 + 原版插件共存加载 OK")
        bad = [ln for ln in stderr_lines if "failed to" in ln.lower() or "cannot find" in ln.lower()]
        if bad:
            print("[warn] stderr 有关键报错:")
            for ln in bad[:10]:
                print("  |", ln)
        return 1 if bad else 0
    finally:
        stop_runtime(proc, rpc)
        try:
            config.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
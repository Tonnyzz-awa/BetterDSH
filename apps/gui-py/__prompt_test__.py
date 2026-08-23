"""验证 session/prompt -> 事件流通知（开发自检，非交付）。

无 API key 时模型请求会 401 失败, 但应能看到 turn/start、user/message、
tool/call(或错误) 等事件通知——这正是前端渲染的核心通路。
"""
import random
import string
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from harness.launcher import DEFAULT_REPO, start_runtime, stop_runtime, wait_ready


def main() -> int:
    config = ROOT / "data" / "runtime.cordis.yml"
    sessions = ROOT / "data" / "sessions"
    proc, rpc = start_runtime(repo=DEFAULT_REPO, config_path=config,
                             session_root=sessions, api_key=None)

    events = []
    stderr_lines: list[str] = []

    def drain():
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_lines.append(line.rstrip())

    threading.Thread(target=drain, daemon=True).start()

    def notify(method, params):
        if method == "session.event":
            ev = params.get("event") or {}
            events.append((ev.get("type"), ev.get("data") or {}))

    old = rpc._notify_cb

    def notify_cb(m, p):
        if old is not None:
            try:
                old(m, p)
            except BaseException:
                pass
        notify(m, p)

    rpc._notify_cb = notify_cb

    seen_turn_end = False
    try:
        # 首次 boot 需激活整棵插件树, 循环重试 initialize
        wait_ready(rpc, timeout=90, echo=lambda s: print(f"[boot] {s}"),
                   stderr_lines=stderr_lines)
        sid = "boot-test-" + "".join(random.choices(string.ascii_lowercase, k=6))
        print(f"[prompt] session={sid}")
        print(rpc.request("session/prompt",
              {"sessionId": sid, "contentBlocks": [{"type": "text", "text": "hi"}]}, timeout=5))

        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if any(t == "turn/end" for t, _ in events):
                seen_turn_end = True
                break
            time.sleep(0.3)
        print(f"[events] 收到 {len(events)} 条事件; turn/end: {seen_turn_end}")
        seen = sorted({t for t, _ in events})
        print(f"[types] {seen}")
        for t, d in events[:10]:
            print("   -", t, str(d)[:120])
    finally:
        stop_runtime(proc, rpc)

    if not seen_turn_end:
        print("[stderr 尾部]")
        for ln in stderr_lines[-20:]:
            print("  |", ln)
    return 0 if seen_turn_end else 1


if __name__ == "__main__":
    raise SystemExit(main())
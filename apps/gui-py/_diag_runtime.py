"""诊断运行时：复刻 launcher 启动，活体打印 stdout/stderr，并在数秒后发送 initialize，
观察运行时是否回应、回应什么、或卡在哪里。"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(r"D:\Deepseek\dsh-source-code")
CFG = REPO / "apps/gui-py/data/runtime.cordis.yml"
SESSION_ROOT = REPO / "apps/gui-py/data/sessions"
DEMO_ENTRY = REPO / "packages/examples/jsonrpc-demo/src/bin.ts"


def resolve_tsx(repo: Path) -> str:
    if (repo / "node_modules" / "tsx" / "package.json").is_file():
        return "tsx/esm"
    raise SystemExit("tsx not found at node_modules/tsx")


def main():
    env = os.environ.copy()
    env.setdefault("DSH_SESSION_ROOT", str(SESSION_ROOT))
    env["DSH_CWD"] = str(REPO)

    cmd = [r"C:\Program Files\nodejs\node.EXE", "--import", resolve_tsx(REPO),
           str(DEMO_ENTRY), str(CFG)]
    print("CMD:", " ".join(cmd), flush=True)

    proc = subprocess.Popen(
        cmd, cwd=str(REPO), env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    print("pid:", proc.pid, flush=True)

    def pump(stream, label):
        try:
            for line in stream:
                print(f"[{label}] {line.rstrip()}", flush=True)
        except Exception as exc:
            print(f"[{label} pump error] {exc}", flush=True)

    threading.Thread(target=pump, args=(proc.stdout, "OUT"), daemon=True).start()
    threading.Thread(target=pump, args=(proc.stderr, "ERR"), daemon=True).start()

    # 等运行时起来
    time.sleep(5)
    print("=== sending initialize ===", flush=True)
    req = {
        "jsonrpc": "2.0",
        "id": "diag-1",
        "method": "initialize",
        "params": {
            "cwd": str(REPO),
            "provider": "deepseek-official",
            "model": "deepseek-official",
        },
    }
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    print("initialize sent; waiting 12s for response...", flush=True)

    # 主线程空转，pump 线程会打印任何响应
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            print(f"!!! runtime exited with code {proc.returncode}", flush=True)
            break
        time.sleep(0.5)

    print("=== done waiting; terminating ===", flush=True)
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


if __name__ == "__main__":
    main()

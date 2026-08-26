"""临时冒烟测试：复刻 main_window 的启动流程，验证运行时能否 boot 并回应 initialize。"""
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, r"D:\Deepseek\dsh-source-code\apps\gui-py")

from harness.launcher import (
    resolve_repo, probe_prereqs, ensure_deps, start_runtime, wait_ready,
    HarnessUnavailable,
)
from harness.config import write_config
from harness.shared_backend import session_root

repo = resolve_repo(None)
print("repo:", repo)
cfg = Path(r"D:\Deepseek\dsh-source-code\apps\gui-py\data\runtime.cordis.yml")
cfg.parent.mkdir(parents=True, exist_ok=True)
write_config(cfg, provider_id="deepseek-official")
print("config written:", cfg)

sr = session_root()
provider = "deepseek-official"
api_key = None

for name, ok, msg in probe_prereqs(repo):
    print(f"[probe:{name}] {'OK' if ok else 'FAIL'} {msg}")

ensure_deps(repo)
print("deps ensured")

proc, rpc = start_runtime(repo=repo, config_path=cfg, session_root=sr,
                          api_key=api_key, provider=provider)
print("runtime pid:", proc.pid)

stderr_buf = []

def stderr_loop():
    for line in proc.stderr:
        line = line.rstrip()
        stderr_buf.append(line)
        print("[stderr]", line, flush=True)

t = threading.Thread(target=stderr_loop, daemon=True)
t.start()

try:
    res = wait_ready(rpc, provider=provider, repo=repo, stderr_lines=stderr_buf)
    print("=== RUNTIME READY ===", res)
except HarnessUnavailable as exc:
    print("=== STARTUP FAILED ===", exc)
    print("--- stderr tail ---")
    print("\n".join(stderr_buf[-40:]))
except Exception as exc:
    print("=== UNEXPECTED ===", repr(exc))
    print("\n".join(stderr_buf[-40:]))
finally:
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

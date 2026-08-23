# -*- coding: utf-8 -*-
"""一键启动 pygui（Python 桌面端）。

它会依次完成：
  1. 检查 Node.js
  2. 安装仓库依赖（corepack pnpm install，仅首次）
  3. 构建 host 端 lib（pnpm build:lib:host，仅 lib 缺失时）
  4. 安装 Python 依赖（pip install -r apps/gui-py/requirements.txt）
  5. 启动 apps/gui-py/run_gui.py

用法：
    python 启动pygui.py
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

GUI = ROOT / "apps" / "gui-py"
REQS = GUI / "requirements.txt"
RUN_GUI = GUI / "run_gui.py"
# host 端构建产物标记：存在即认为 lib 已构建
LIB_MARKER = ROOT / "packages" / "boot" / "app-boot" / "lib" / "index.js"


def has_node() -> str | None:
    """返回可用 node 向量（node 或 corepack node），无则 None。"""
    for cmd in (["node"], ["corepack", "node"]):
        try:
            subprocess.run(cmd + ["--version"], capture_output=True, check=True, shell=True)
            return cmd[0] if len(cmd) == 1 else cmd
        except Exception:
            continue
    return None


def run(cmd: str, *, check: bool = True) -> int:
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd, shell=True, check=False)
    if check and r.returncode != 0:
        raise SystemExit(f"命令失败（退出码 {r.returncode}）：{cmd}")
    return r.returncode


def main() -> int:
    node = has_node()
    if not node:
        print("未检测到 Node.js（需要 ≥ 22.19）。请先安装：https://nodejs.org/")
        input("按回车退出...")
        return 1

    # 1) 仓库依赖
    if not (ROOT / "node_modules").is_dir():
        print("首次运行：安装仓库依赖（corepack pnpm install），耗时较长，请耐心等待...")
        run("corepack pnpm install")
    else:
        print("依赖已就绪（node_modules 存在）")

    # 2) host 端 lib 构建（运行时通过 tsx 加载 workspace 包的 lib/）
    if not LIB_MARKER.is_file():
        print("host 端 lib 未构建，开始构建（pnpm build:lib:host）...")
        run("corepack pnpm build:lib:host")
    else:
        print("host 端 lib 已构建")

    # 3) Python 依赖
    if REQS.is_file():
        print("安装 Python 依赖（pip install -r apps/gui-py/requirements.txt）...")
        run(f"{sys.executable} -m pip install -r \"{REQS}\"", check=False)
    else:
        print(f"未找到 requirements.txt：{REQS}")

    # 4) 启动 pygui
    print("\n启动 pygui ...")
    return run(f"\"{sys.executable}\" \"{RUN_GUI}\"", check=False)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消")
    except SystemExit:
        raise
    finally:
        if not sys.flags.interactive:
            input("\n按回车退出...")

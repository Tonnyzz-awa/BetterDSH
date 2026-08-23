# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def has_node():
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True, shell=True)
        return True
    except Exception:
        return False

def run(cmd, wait=True):
    print(">>> " + cmd)
    subprocess.run(cmd, shell=True, check=False)
    time.sleep(0.3)


def main():
    if not has_node():
        print("未检测到 Node.js，请先安装 Node.js 18+")
        input("按回车退出...")
        sys.exit(1)

    if not os.path.isdir(os.path.join(ROOT, "node_modules")):
        print("首次运行，正在安装依赖（pnpm install），请耐心等待...")
        run("npx pnpm install")
    else:
        print("依赖已存在，跳过安装")

    dist = os.path.join(ROOT, "apps", "web", "dist", "index.html")
    if not os.path.isfile(dist):
        print("前端未构建，正在构建...")
        run("npx pnpm run build")
    else:
        print("前端已构建，跳过")

    print("正在启动 dsh web，浏览器打开 http://127.0.0.1:3080")
    run("npx pnpm dsh web")
    print("服务已退出")
    input("按回车退出...")


if __name__ == "__main__":
    main()
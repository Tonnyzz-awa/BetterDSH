"""dsh-gui 入口: 按设置渲染运行时配置、启动 PyQt6 前端。

用法:
    pip install -r requirements.txt
    python run_gui.py

环境变量:
    DSH_REPO              仓库路径 (缺省自动探测融合位置的上三级目录)
    供应商/密钥通过界面设置保存到 data/settings.json, 也可用环境变量注入。
"""

from __future__ import annotations

import sys
from pathlib import Path

from harness.config import write_config
from harness.launcher import _find_repo
from harness.settings import load_settings


def main() -> int:
    root = Path(__file__).resolve().parent
    repo = _find_repo(None)

    sessions_dir = root / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    settings = load_settings(root)
    config_path = root / "data" / "runtime.cordis.yml"
    provider = settings.get("provider", "deepseek-official")
    if provider == "custom" and settings.get("base_url"):
        write_config(config_path, provider_id=provider,
                     base_url=settings["base_url"],
                     custom_models=settings.get("custom_models") or [])
    else:
        write_config(config_path, provider_id=provider)

    if not repo.is_dir():
        print(f"[dsh-gui] 未找到仓库: {repo}")
        print(f"[dsh-gui] 设置 DSH_REPO 指向 deeppseek-harness 目录")
        return 2

    # 延迟导入 Qt: CLI-only 用法（如 --help）不需安装 PyQt6
    from PyQt6.QtWidgets import QApplication
    from ui.betterdsh_ui import set_theme, app_qss
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    set_theme(settings.get("theme", "light"))
    app.setStyleSheet(app_qss())
    window = MainWindow(root=root, repo=repo, config_path=config_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
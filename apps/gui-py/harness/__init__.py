"""接入 DeepSeek Harness 运行时的 Python 侧。
- rpc:      stdio NEWLINE-JSON-RPC 客户端（进程通信层）
- launcher: 定位仓库、生成配置、启动/关闭运行时子进程
- config:   生成 cordis.yml 组合文件
"""
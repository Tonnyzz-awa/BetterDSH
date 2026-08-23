# dsh-gui — DeepSeek Harness 桌面前端（PyQt6）

一个极简的桌面聊天壳，直接驱动仓库里的 `dsh-sdk-jsonrpc-server`（JSON-RPC over stdio），
不经过浏览器。左侧是历史对话栏（可折叠），中间偏右是对话区。

本目录已融合进 deepseek-harness 仓库（`apps/gui-py/`），运行时依赖与官方
`dsh --profile` 共用同一份 node_modules；两者各自使用独立的配置与进程，互不冲突。

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│ PyQt6 前端 (run_gui.py / ui/)                                  │
│   左侧历史栏(可折叠)  中间对话气泡 + 底部输入框                 │
└───────────────▲─────────────────────────────────────────────┘
                │ NEWLINE-JSON-RPC (stdin/stdout)
┌───────────────┴──────────────┐
│ harness 运行时子进程            │
│   node --import tsx/esm        │
│   packages/examples/jsonrpc-demo/src/bin.ts <config>        │
└──────────────────────────────┘
```

- **JSON-RPC 协议**（`dsh-sdk-protocol`）：请求有 `id`；通知（`session.event`、
  `session.status`、`subagent.*`）无 `id`，携带事件。
- **前端不直接 import harness 代码**：以进程边界隔离，任何可以按此协议说话的
  运行时都能替换。
- **会话模型**：`session/prompt` 每次把用户消息排进该 `sessionId` 的
  agent，模型按自身 turn 处理。UI 侧每个"对话"对应一个 `sessionId`。

## 二、安装与运行

前置要求:

- Python 3.10+；`pip install -r requirements.txt`
- Node.js ≥ 22.19（推荐 24；项目引擎范围 `^22.19.0 || >=24.0.0`）
- 仓库已完成 `corepack pnpm install`（本应用启动时若发现 node_modules 缺失
  会自动尝试安装）

运行:

```powershell
cd D:\Deepseek\deepseek-harness-master\apps\gui-py
pip install -r requirements.txt
$env:DEEPSEEK_API_KEY = "sk-..."   # 可选; 不设也能启动界面
python run_gui.py
```

- 仓库根自动探测（本文件位置向上三级），也可用 `$env:DSH_REPO` 覆盖。
- 首次启动会在 `data/` 生成 `runtime.cordis.yml`（Windows 上自动选用
  pwsh-shell；其他平台用 bash）。
- 点「启动运行时」，状态变为「运行时就绪」后即可对话。

## 三、插件支持（与原版 harness 的关系）

harness 的插件是 **Cordis 体系（TypeScript / npm 包）**，dsh-gui 本身是 Python
写的**客户端外壳**：它不执行插件，而是把插件挂载清单写进运行时配置
`data/runtime.cordis.yml`，交给 `dsh-sdk-jsonrpc-server` 在子进程中加载。
因此：

- **原版插件全部可用**：任何 `packages/` 里已安装的 Cordis 插件，只要在运行时
  配置里声明条目即可被加载。
- **挂载方式**：编辑 `data/plugins.entries.yml`，写入追加的 entry 文本
  （块级 YAML，从 `- id:` 开始）。保存设置重启后生效。
  ```yaml
  # data/plugins.entries.yml（示例：追加一个原版工具插件，仿照其 cordis.yml 写法）
  - id: my-tool
    name: '@deepseek-ai/dsh-tool-cordis'
    config:
      cwd: !!js process.cwd()
  ```
- **与官方 `dsh --profile` 不冲突**：GUI 运行时用自己生成的独立
  `data/runtime.cordis.yml`、独立的 `DSH_SESSION_ROOT` 会话目录、独立的
  settings（明文 key 存 `data/settings.json`），官方 profile 的 `cordis.yml` /
  `.env` / 会话日志完全不受影响。两者可以同时跑不同 profile。

## 四、目录结构

```
gui-py/
  harness/
    launcher.py   仓库定位、依赖探测、启动/停止运行时、握手就绪
    rpc.py        新行 JSON-RPC 客户端（线程安全，含 models/list）
    config.py     生成 cordis.yml（平台 shell / 供应商路由 / 追加插件）
    catalog.py    从已装 pi-ai 目录动态读取模型列表（不写死）
    settings.py   data/settings.json 读写
  ui/
    theme.py      QSS 极简主题（想换配色只改这一处）
    widgets.py    气泡（助手 Markdown 渲染）/ 工具行 / 输入框
    main_window.py 主窗口 + 运行时桥接
  run_gui.py      入口
  requirements.txt
  data/           运行期数据（会话、设置、生成配置；不进 git）
```

## 五、协议注释（给以后加功能的人）

- 启动：`launcher.start_runtime()` 返回 `(proc, rpc)`；`wait_ready()` 使用
  `initialize` 方法握手（provider/model/context）。
- 模型：`rpc.list_models(["openai"])` 走新增的 `models/list` 只读方法，
  返回已注册路由的模型目录；离线兜底读 pi-ai 的 providers 数据。
- 发消息：`rpc.request("session/prompt", {sessionId, contentBlocks})`，
  返回 `{messageId}` 只是「排入收件箱」凭证，并不代表回答完成。
- 看回答：订阅 `session.event` 通知，事件类型见 `SessionEventMap`——
  `assistant/message`（整条）、`assistant/chunk`（流式增量）、
  `tool/call`、`tool/result`、`turn/start|end`。
- 优雅退出：`rpc.request("shutdown")` 后 dispose 根上下文再 exit 0；EOF 与
  信号也会触发同一路径。

## 六、已知边界

- `initialize` 需要 provider/model；默认走 `deepseek-official`（仓库 installs
  `dsh-llm-deepseek`，从环境读 `DEEPSEEK_API_KEY`）。
- JSON-RPC 层没有 per-prompt 级取消接口（协议层暂无），发送后等待 turn 结束。
- 会话日志文件目前留在 `data/sessions/`（JSONL），GUI 尚未做跨重启恢复。
"""与 DeepSeek Harness JSON-RPC 运行时对话的最小 stdio 客户端。

协议约定（见 dsh-sdk-protocol）：
- 每个 JSON-RPC 消息是一行紧凑 JSON，通过 stdout 输出、stdin 读入。
- 客户端 -> 服务器：请求（带 id 与 method）或通知（带 method、无 id）。
- 服务器 -> 客户端：同一通道返回响应（带相同 id），并推送通知（无 id）。

本客户端用两个线程：
- reader 线程读 stdout 行，把响应交给对应请求的队列，通知则交给回调。
- writer 线程从队列取帧写 stdin；写阻塞不会卡住某个请求自身的超时，
  因此子进程停滞（不再读 stdin）时请求仍能按 timeout 返回，不会无限挂。
- stderr 由调用方负责排空（本模块不接管），用于诊断日志。
"""

from __future__ import annotations

import json
import queue
import threading
import uuid


class JsonRpcError(Exception):
    """JSON-RPC 层错误：服务器返回的 error 对象。"""

    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code = code
        self.data = data


class TransportClosed(RuntimeError):
    """stdout 已关闭（运行时退出或崩了）。"""


def _frame(method: str, params=None, msg_id=None) -> dict:
    """构造一帧 JSON-RPC 消息。"""
    frame = {"jsonrpc": "2.0", "method": method}
    if msg_id is not None:
        frame["id"] = msg_id
    if params is not None:
        frame["params"] = params
    return frame


class HarnessRpcClient:
    """一个子进程上的纯文本 JSON-RPC 客户端。

    只依赖 subprocess 的新行分隔 stdin/stdout 流，因此可以在任意
    运行时二进制或源码启动的命令之上复用。
    """

    def __init__(self, *, read, write, notify_cb=None):
        """
        read:  可迭代的文本行（通常：runtime.stdout）
        write: 带 flush 的文本写端（通常：runtime.stdin）
        notify_cb: 收到通知（无 id 消息）时回调，签名 (method, params)
        """
        self._read_iter = read
        self._write = write
        self._notify_cb = notify_cb
        self._pending_lock = threading.Lock()
        self._pending: dict[str, queue.Queue] = {}
        self._closed = False
        self._error: BaseException | None = None
        # 写请求帧的队列：writer 线程消费，避免阻塞请求自身的超时等待。
        self._write_q: "queue.Queue[tuple[str, str] | None]" = queue.Queue()
        self._reader = threading.Thread(
            target=self._read_loop,
            name="harness-rpc-reader",
            daemon=True,
        )
        self._writer = threading.Thread(
            target=self._write_loop,
            name="harness-rpc-writer",
            daemon=True,
        )

    def start(self):
        self._reader.start()
        self._writer.start()
        return self

    # ----- 对外 API -----

    def request(self, method, params=None, *, timeout=None):
        """发送一个请求，等待匹配 id 的响应，返回 result。

        超时或传输关闭会抛异常；服务器的 error 对象抛 JsonRpcError。
        """
        if self._closed:
            raise TransportClosed("运行时通道已关闭")
        request_id = str(uuid.uuid4())
        # 用容量为 1 的队列隔离每个请求的等待者
        waiter: queue.Queue = queue.Queue(maxsize=1)
        with self._pending_lock:
            if self._closed:
                raise TransportClosed("运行时通道已关闭")
            self._pending[request_id] = waiter
        frame = _frame(method, params, msg_id=request_id)
        data = json.dumps(frame, ensure_ascii=False, separators=(",", ":"))
        # 入队即返回；真正的写由 writer 线程完成，故写阻塞不会拖住本请求的超时。
        self._write_q.put((request_id, data))
        try:
            payload = waiter.get(timeout=timeout)
        except queue.Empty:
            # 请求超时：立即忘记它，避免后续迟到响应堆积无主队列
            with self._pending_lock:
                self._pending.pop(request_id, None)
            raise TimeoutError(f"请求 {method} 超时（{timeout}s）")
        if isinstance(payload, BaseException):
            raise payload
        if "error" in payload:
            err = payload["error"]
            raise JsonRpcError(err.get("code"), err.get("message", method), err.get("data"))
        return payload.get("result")

    def list_models(self, providers=None, *, timeout=10):
        """查询注册路由的模型目录（只读）。

        providers: 可选的路由过滤列表；省略返回全部注册路由。
        返回 {providers: [{id, name, models: [{id, name}]}]}。
        """
        params = {"providers": providers} if providers else {}
        return self.request("models/list", params, timeout=timeout) or {}

    def wait_closed(self, timeout=None):
        """等待 reader / writer 线程结束（子进程死后 stdout 关闭）。"""
        self._reader.join(timeout=timeout)
        self._writer.join(timeout=timeout)

    def close(self):
        """停止接受新请求；已注册的通知回调仍会收到剩余收尾消息。"""
        self._closed = True
        # 让阻塞中的所有等待者立刻失败
        with self._pending_lock:
            for waiter in list(self._pending.values()):
                waiter.put(TransportClosed("运行时通道已关闭"))
        # 唤醒 writer 线程退出
        self._write_q.put(None)

    # ----- 内部 -----

    def _write_loop(self):
        """从队列取帧写 stdin；写异常只失败对应请求，不影响其它请求。"""
        while True:
            item = self._write_q.get()
            if item is None:
                return
            request_id, data = item
            if self._closed:
                continue
            try:
                self._write.write(data + "\n")
                self._write.flush()
            except BaseException as exc:  # 写失败：清掉等待者再抛
                with self._pending_lock:
                    waiter = self._pending.pop(request_id, None)
                if waiter is not None:
                    waiter.put(TransportClosed(f"写入运行时失败: {exc}"))

    def _read_loop(self):
        try:
            for line in self._read_iter:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    # stdout 只承载 JSON-RPC，垃圾行属于异常：忽略但保留诊断
                    continue
                if not isinstance(msg, dict):
                    continue
                msg_id = msg.get("id")
                if isinstance(msg_id, (str, int)) and "method" not in msg:
                    # 是响应（携带 id 且没有 method）
                    with self._pending_lock:
                        waiter = self._pending.pop(str(msg_id), None)
                    if waiter is None:
                        continue
                    if "error" in msg:
                        waiter.put(JsonRpcError(
                            (msg["error"].get("code") if isinstance(msg["error"], dict) else None),
                            (msg["error"].get("message") if isinstance(msg["error"], dict) else msg["error"]),
                            (msg["error"].get("data") if isinstance(msg["error"], dict) else None),
                        ))
                    else:
                        waiter.put(msg)
                elif isinstance(msg_id, (str, int)):
                    # 服务器主动请求——本实现不支持被驱动，回一个 error 即止
                    if self._notify_cb is not None:
                        try:
                            self._notify_cb("+request", {**msg, "_id": msg_id})
                        except BaseException:
                            pass
                else:
                    # 通知
                    method = msg.get("method")
                    if isinstance(method, str) and self._notify_cb is not None:
                        try:
                            self._notify_cb(method, msg.get("params"))
                        except BaseException:
                            pass
        except BaseException as exc:
            self._error = exc
        finally:
            with self._pending_lock:
                for waiter in list(self._pending.values()):
                    waiter.put(TransportClosed("运行时 stdout 已关闭"))

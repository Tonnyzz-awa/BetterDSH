"""冒烟测试：用内存中的"伪运行时"验证 rpc 客户端。

启动时: 客户端在后台线程写请求, 伪运行时把匹配 id 的响应回推。
验证点:
  1) request() 正确取回 result
  2) 错误响应抛 JsonRpcError
  3) 无 id 的通知被送给 notify_cb
  4) close/transport closed 行为

运行: python harness/__smoke_rpc__.py
（纯标准库，无依赖）
"""
from __future__ import annotations

import json
import queue
import threading
import time

from harness.rpc import HarnessRpcClient, JsonRpcError


class FakeRuntime:
    """双向的假子进程: read 是可迭代, write/flush 是写入端。"""

    def __init__(self):
        self._sent = queue.Queue()   # 客户端 -> 伪运行时
        self._recv = queue.Queue()   # 伪运行时 -> 客户端
        self._closed = False

    # ---- 客户端视角 ----
    def read(self):
        def gen():
            while True:
                try:
                    data = self._recv.get(timeout=5)
                except queue.Empty:
                    continue
                if data is None:
                    return
                yield data
        return gen()

    def write(self, data: str):
        self._sent.put(data)

    def flush(self):
        pass

    # ---- 伪运行时视角 ----
    def add_out(self, line: str):
        """伪运行时向客户端推一条消息。"""
        self._recv.put(line + "\n")

    def close_out(self):
        self._recv.put(None)

    def recv_for(self, method: str):
        """取出伪运行时收到的第一条方法消息。"""
        for _ in range(100):
            try:
                data = self._sent.get(timeout=5)
            except queue.Empty:
                return None
            msg = json.loads(data)
            if msg.get("method") == method:
                return msg
        return None


def main() -> int:
    rt = FakeRuntime()
    got_notifications = []

    client = HarnessRpcClient(
        read=rt.read(),
        write=rt,
        notify_cb=lambda m, p: got_notifications.append((m, p)),
    ).start()

    # 1) 正常响应
    def responder():
        msg = rt.recv_for("initialize")
        assert msg is not None, "未收到 initialize 请求"
        rt.add_out(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": {"ok": 1}}))
    threading.Thread(target=responder, daemon=True).start()
    result = client.request("initialize", {"cwd": "."}, timeout=10)
    assert result == {"ok": 1}, result
    print("1) request/response OK")

    # 2) 错误响应
    def error_responder():
        msg = rt.recv_for("session/prompt")
        assert msg is not None
        rt.add_out(json.dumps({"jsonrpc": "2.0", "id": msg["id"],
                               "error": {"code": -1, "message": "boom"}}))
    threading.Thread(target=error_responder, daemon=True).start()
    try:
        client.request("session/prompt", {"sessionId": "a", "contentBlocks": []}, timeout=10)
        raise SystemExit("错误响应没有抛 JsonRpcError")
    except JsonRpcError as exc:
        assert exc.code == -1 and "boom" in str(exc), exc
        print("2) error -> JsonRpcError OK")

    # 3) 通知转发
    rt.add_out(json.dumps({"jsonrpc": "2.0", "method": "session.event",
                           "params": {"sessionId": "s", "event": {"type": "turn/start", "data": {}}}}))
    for _ in range(100):
        if got_notifications:
            break
        time.sleep(0.02)
    assert got_notifications and got_notifications[0][0] == "session.event", got_notifications
    print("3) notification OK")

    # 4) transport closed 后 request 抛 TransportClosed
    client.close()
    try:
        client.request("shutdown", None, timeout=2)
        raise SystemExit("closed client 仍能 request")
    except Exception as exc:
        assert "通道" in str(exc) or "写入" in str(exc), exc
        print("4) close -> TransportClosed OK")

    print("smoke rpc OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
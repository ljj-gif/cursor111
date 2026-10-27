"""agent.py - Agent 循环：调用 DeepSeek，模型决定用哪个工具，执行后继续对话。

只用 Python 标准库（urllib），不需要 pip install 任何东西。
"""
import json
import os
import urllib.request

from tools import run_tool, tools_schema

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
MAX_ROUNDS = 8  # 一轮对话里最多连续用 8 次工具，防止死循环


def _load_key() -> str:
    """从项目根目录的 .env 读取 key，绝不打印出来。"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if key and key != "你的key填这里":
                        return key
    return ""


SYSTEM_PROMPT = """你是一个运行在桌面应用"迷你 Cursor"里的编程助手。
你可以使用 4 个工具：read（读文件）、write（写文件）、edit（改文件）、bash（执行命令）。
所有文件操作都限制在用户的工作区目录内，工作区里现有的文件可以用 bash 的 ls 查看。
收到编程任务时：先看清楚文件现状（必要时 read 或 ls），再动手写/改，最后可以用 bash 运行验证。
回答用简体中文，简洁一点。"""


class Agent:
    def __init__(self, on_event=None):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.on_event = on_event or (lambda text, kind: None)  # 用于向 UI 汇报

    def chat(self, user_text: str) -> str:
        """处理一条用户消息，返回助手最终回复。可能内部多次调用工具。"""
        key = _load_key()
        if not key:
            return "还没有配置 API key。请把 key 填到项目目录下的 .env 文件里（DEEPSEEK_API_KEY=...），然后重新启动程序。"

        self.messages.append({"role": "user", "content": user_text})

        for _ in range(MAX_ROUNDS):
            reply = self._call_api(key)
            choice = reply["choices"][0]
            message = choice["message"]

            # 模型要用工具
            if message.get("tool_calls"):
                self.messages.append(message)
                for call in message["tool_calls"]:
                    name = call["function"]["name"]
                    args = json.loads(call["function"].get("arguments") or "{}")
                    self.on_event(f"🔧 使用工具 {name} {args}", "tool")
                    result = run_tool(name, args)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": result[:4000],
                        }
                    )
                continue  # 带着工具结果再问模型

            # 模型给出最终回答
            content = message.get("content") or ""
            self.messages.append({"role": "assistant", "content": content})
            return content

        return "(连续多轮使用工具，本轮先停下来了。你可以继续追问。)"

    def _call_api(self, key: str) -> dict:
        """调用 DeepSeek 的 chat/completions 接口（OpenAI 兼容格式）。"""
        body = json.dumps(
            {
                "model": MODEL,
                "messages": self.messages,
                "tools": tools_schema(),
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def reset(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

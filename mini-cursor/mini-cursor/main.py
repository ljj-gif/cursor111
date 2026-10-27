"""main.py - 迷你 Cursor：tkinter 桌面窗口界面

双击运行（或 python main.py）即可打开窗口。
"""
import threading
import tkinter as tk
from tkinter import scrolledtext

# Windows 高分屏（125%/150% 缩放）下声明 DPI 感知，
# 否则系统会把窗口放大，导致底部输入区被顶到屏幕外面看不见。
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from agent import Agent


class MiniCursorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("迷你 Cursor")

        # 按屏幕实际 DPI 计算缩放，保证字体清晰、窗口不超出屏幕
        scale = max(1.0, self.root.winfo_fpixels("1i") / 96.0)
        try:
            self.root.tk.call("tk", "scaling", 1.34 * scale)
        except tk.TclError:
            pass

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w = min(int(820 * scale), max(560, sw - 100))
        h = min(int(620 * scale), max(420, sh - 140))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 30)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(560, 420)

        self.agent = Agent(on_event=self.log_event)

        # 用 grid 布局：第 0 行（聊天区）自动伸展占满剩余空间，
        # 第 1 行（输入区）保持自身高度，永远不会被聊天区挤没。
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # 聊天记录区
        self.chat_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED, height=8,
            font=("Microsoft YaHei UI", 11), padx=10, pady=8,
        )
        self.chat_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # 底部输入区
        bottom = tk.Frame(self.root)
        bottom.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom.grid_columnconfigure(0, weight=1)

        self.input_box = tk.Text(
            bottom, height=3, undo=True, font=("Microsoft YaHei UI", 11),
            relief=tk.SOLID, borderwidth=1,
        )
        self.input_box.grid(row=0, column=0, sticky="nsew")
        self.input_box.bind("<Return>", self._on_enter)

        self.send_btn = tk.Button(
            bottom, text="发送", width=8, command=self.on_send,
            font=("Microsoft YaHei UI", 11),
        )
        self.send_btn.grid(row=0, column=1, sticky="ns", padx=(8, 0))

        self.input_box.focus_set()

        self._append("助手", "你好！我是迷你 Cursor。告诉我你想写或改什么程序，我可以直接读写你工作区里的文件并运行它们。", "assistant")

    # ---------- UI 辅助 ----------

    def _append(self, who: str, text: str, kind: str = "user"):
        self.chat_box.configure(state=tk.NORMAL)
        tag = kind
        self.chat_box.insert(tk.END, f"{who}：", tag)
        self.chat_box.insert(tk.END, text + "\n\n", f"{tag}_text")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state=tk.DISABLED)

        # 颜色标签
        colors = {
            "user": "#1a73e8", "user_text": "#222222",
            "assistant": "#0b8043", "assistant_text": "#222222",
            "tool": "#b26a00", "tool_text": "#8a6d3b",
        }
        if tag not in self.chat_box.tag_names():
            self.chat_box.tag_configure(tag, foreground=colors.get(tag, "#222222"), font=("Microsoft YaHei UI", 11, "bold"))
            self.chat_box.tag_configure(f"{tag}_text", foreground=colors.get(f"{tag}_text", "#222222"))

    def log_event(self, text: str, kind: str):
        self.root.after(0, self._append, "", text, kind)

    def _on_enter(self, event):
        # Shift+Enter 换行，Enter 直接发送
        if not (event.state & 0x0001):
            self.on_send()
            return "break"
        return None

    # ---------- 发送逻辑 ----------

    def on_send(self):
        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            return
        if text.startswith("/new"):
            self.agent.reset()
            self._append("助手", "已开始新对话。", "assistant")
            self.input_box.delete("1.0", tk.END)
            return

        self.input_box.delete("1.0", tk.END)
        self._append("我", text, "user")
        self.send_btn.configure(state=tk.DISABLED, text="思考中…")

        # 网络请求放到后台线程，避免界面卡死
        thread = threading.Thread(target=self._worker, args=(text,), daemon=True)
        thread.start()

    def _worker(self, text: str):
        try:
            reply = self.agent.chat(text)
        except Exception as e:  # noqa: BLE001
            reply = f"出错了：{e}"
        self.root.after(0, self._finish, reply)

    def _finish(self, reply: str):
        self._append("助手", reply, "assistant")
        self.send_btn.configure(state=tk.NORMAL, text="发送")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MiniCursorApp().run()

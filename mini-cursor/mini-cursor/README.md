# 迷你 Cursor

课程作业：用「桌面应用 + 大模型 + MCP 工具调用」的思想，实现一个能读写文件、执行命令的编程助手。

## 功能

- tkinter 桌面窗口（双击即可运行，不是网页）
- 接入 DeepSeek 大模型（OpenAI 兼容的 chat/completions 接口）
- 4 个工具（MCP 风格的 function calling）：
  | 工具 | 作用 |
  |------|------|
  | read | 读取工作区内文件 |
  | write | 写入/新建文件 |
  | edit | 精确替换文件中的一段文本 |
  | bash | 在工作区执行 shell 命令（如运行 Python） |
- 所有文件操作限制在 `workspace/` 目录内，模型无法越界访问其他文件
- Agent 循环：模型可以连续多次调用工具，直到给出最终回答

## 运行步骤

1. 只用标准库，**不需要 pip install 任何依赖**（Python 3.10+）
2. 复制 `.env.example` 为 `.env`，填入你自己的 DeepSeek API key：
   ```
   DEEPSEEK_API_KEY=sk-xxxx
   ```
3. 双击 `main.py` 或命令行运行：
   ```
   python main.py
   ```
4. 在输入框里试着说：「把 workspace 里的 hello.py 改成打印九九乘法表，然后运行它验证」

## 文件结构

```
mini-cursor/
├── main.py        # tkinter 界面 + 消息收发
├── agent.py       # Agent 循环：调模型 -> 执行工具 -> 再调模型
├── tools.py       # 4 个工具的实现和 schema 定义
├── .env.example   # key 模板（真正的 .env 已被 .gitignore 排除）
└── workspace/     # 模型能操作的沙箱目录
```

## 演示建议（5 分钟）

1. 输入「工作区里有什么文件？」→ 演示 bash/ls
2. 输入「读一下 hello.py」→ 演示 read
3. 输入「新建一个 fizzbuzz.py：1 到 100，3 的倍数打 Fizz…，写完运行验证」→ 演示 write + bash
4. 输入「把 fizzbuzz 的循环改成 1 到 20」→ 演示 edit

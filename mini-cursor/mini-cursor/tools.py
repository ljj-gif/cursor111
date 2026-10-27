"""tools.py - 四个工具：read / write / edit / bash

所有文件操作都限制在 WORKSPACE 目录内，防止模型乱翻你电脑上别的文件。
"""
import os
import subprocess

# 工作区根目录：所有文件操作只能在这里面进行
WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
os.makedirs(WORKSPACE, exist_ok=True)


def _safe_path(path: str) -> str:
    """把相对路径转成工作区内的绝对路径，并拒绝越界访问。"""
    if not os.path.isabs(path):
        path = os.path.join(WORKSPACE, path)
    real = os.path.realpath(path)
    root = os.path.realpath(WORKSPACE)
    if not real.startswith(root):
        raise ValueError(f"路径越界：{path}（只允许操作工作区内的文件）")
    return real


def tool_read(path: str) -> str:
    """读取文件内容。"""
    real = _safe_path(path)
    if not os.path.exists(real):
        return f"错误：文件不存在 {path}"
    with open(real, "r", encoding="utf-8") as f:
        content = f.read()
    if len(content) > 8000:
        content = content[:8000] + "\n...(内容过长，已截断)"
    return content


def tool_write(path: str, content: str) -> str:
    """把内容写入文件（覆盖）。"""
    real = _safe_path(path)
    os.makedirs(os.path.dirname(real) or WORKSPACE, exist_ok=True)
    with open(real, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入 {path}（{len(content)} 字符）"


def tool_edit(path: str, old_text: str, new_text: str) -> str:
    """把文件中的一段旧文本替换为新文本。"""
    real = _safe_path(path)
    if not os.path.exists(real):
        return f"错误：文件不存在 {path}"
    with open(real, "r", encoding="utf-8") as f:
        content = f.read()
    if old_text not in content:
        return f"错误：在 {path} 中没有找到要替换的文本"
    content = content.replace(old_text, new_text, 1)
    with open(real, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已编辑 {path}"


def tool_bash(command: str) -> str:
    """在工作区目录里执行一条 shell 命令，返回输出。"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout or "") + (result.stderr or "")
        if not output.strip():
            output = "(命令执行成功，没有输出)"
        return output.strip()[:4000]
    except subprocess.TimeoutExpired:
        return "错误：命令超时（30 秒）"


# 工具清单：名字 -> (函数, 说明, 参数 schema)
TOOLS = {
    "read": {
        "func": tool_read,
        "description": "读取工作区内指定文件的内容",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "文件路径，相对工作区"}},
            "required": ["path"],
        },
    },
    "write": {
        "func": tool_write,
        "description": "把内容写入工作区内的文件（会覆盖原内容）",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的完整内容"},
            },
            "required": ["path", "content"],
        },
    },
    "edit": {
        "func": tool_edit,
        "description": "把文件中的一段旧文本替换为新文本，用于精确修改",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "old_text": {"type": "string", "description": "要被替换的旧文本"},
                "new_text": {"type": "string", "description": "替换后的新文本"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    "bash": {
        "func": tool_bash,
        "description": "在工作区目录执行一条 shell 命令并返回输出，用于运行代码、列目录等",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "要执行的命令"}},
            "required": ["command"],
        },
    },
}


# 转成 DeepSeek/OpenAI 的 tools 参数格式
def tools_schema():
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            },
        }
        for name, meta in TOOLS.items()
    ]


def run_tool(name: str, args: dict) -> str:
    """按名字执行工具，任何异常都转成字符串返回给模型。"""
    try:
        return str(TOOLS[name]["func"](**args))
    except Exception as e:  # noqa: BLE001
        return f"工具执行出错：{e}"

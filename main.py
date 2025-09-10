# --- 导入必要的库 ---
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import json
import uuid
from typing import List, Dict, Any, Optional

# 用于加载 .env 文件中的环境变量
from dotenv import load_dotenv

# 从我们自己的模块中导入 "零件"
from src.models import init_model, get_available_models
from src.tools.tavily import get_tavily_tool
from src.agent.react import create_agent_graph
from langgraph.prebuilt import ToolNode

# --- 1. 初始化 ---

# 在程序启动时，加载 .env 文件
# 这会让 os.getenv() 能够读取到 .env 中定义的变量
load_dotenv()

# 初始化 FastAPI 应用实例
app = FastAPI()

# 初始化我们所有需要用到的工具
tools = [get_tavily_tool()]
# 创建一个独立的 ToolNode。这很重要，因为它允许我们在 /continue 接口中手动执行工具
tool_node = ToolNode(tools)

# 创建一个简单的内存字典来存储每个会話的状态。
# key 是 thread_id (会话ID)，value 是消息历史。
# 注意：在生产环境中，你应该使用像 Redis 这样的数据库来代替，否则服务重启后所有对话历史都会丢失。
conversation_states: Dict[str, Dict] = {}


# --- 2. 定义数据模型 (Pydantic Models) ---
# 这些模型定义了 API 接口期望接收的数据格式，FastAPI 会自动进行数据校验。

class ChatMessage(BaseModel):
    """/chat 接口的请求体模型"""
    text: str
    provider: str = "ollama"
    model: str = "qwen3:1.7b"
    # thread_id 是可选的，可以为字符串或 None
    thread_id: Optional[str] = None


class ContinueRequest(BaseModel):
    """/continue 接口的请求体模型"""
    thread_id: str
    # tool_choice 是一个列表，因为 LLM 可能一次请求调用多个工具
    tool_choice: List[Dict[str, Any]]


# --- 3. 加载前端 HTML ---

try:
    # 启动时，尝试读取 src 目录下的 index.html 文件内容
    with open("src/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
except FileNotFoundError:
    # 如果文件不存在，提供一个备用的 HTML 内容，以防服务器因找不到文件而崩溃
    html_content = "<html><body><h1>错误: src/index.html 未找到</h1></body></html>"


# --- 4. 定义 FastAPI 路由 (API Endpoints) ---

@app.get("/")
def read_root():
    """根路由，访问时返回前端的 HTML 页面。"""
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/models")
def get_models():
    """返回所有可用的模型，供前端动态加载下拉框选项。"""
    return get_available_models()


@app.post("/chat")
async def chat_stream(chat_message: ChatMessage):
    """
    处理聊天请求的主接口，支持流式响应和工具调用中断。
    """
    # 确定或创建一个新的会话ID
    thread_id = chat_message.thread_id or str(uuid.uuid4())

    # 获取该会话的历史消息
    state = conversation_states.get(thread_id, {"messages": []})
    # 将当前用户的输入添加到消息列表中
    current_input = {"messages": state["messages"] + [("user", chat_message.text)]}

    # 根据前端选择，初始化对应的 LLM 和 Agent Graph
    llm = init_model(chat_message.provider, chat_message.model)
    graph = create_agent_graph(llm, tools)

    async def stream_generator():
        """这个异步生成器是实现流式响应和中断的关键。"""

        # --- 核心中断逻辑 ---
        # 我们手动控制 astream 的迭代器，以完全控制流程

        # 1. 创建异步迭代器实例
        astream = graph.astream(current_input, config={"configurable": {"thread_id": thread_id}})

        # 2. 手动获取图执行的第一个步骤（Chunk）
        try:
            first_chunk = await anext(astream)
        except StopAsyncIteration:
            return  # 如果图没有返回任何内容，则直接结束

        # 3. 检查第一个步骤的输出，判断是否需要调用工具
        if agent_chunk := first_chunk.get("agent"):
            if tool_calls := agent_chunk["messages"][-1].tool_calls:
                # 3a. 如果需要工具：
                print("Tool call detected, interrupting for confirmation.")
                # 保存完整的上下文（包括LLM的工具调用请求），以便 /continue 接口恢复
                conversation_states[thread_id] = {
                    "messages": current_input["messages"] + agent_chunk["messages"]
                }
                # 向前端发送工具确认请求
                yield f"data: {json.dumps({'type': 'tool_request', 'content': [tc['name'] for tc in tool_calls], 'tool_choice': tool_calls, 'thread_id': thread_id})}\n\n"
                # **立刻返回**，终止生成器，防止图继续执行
                return

        # --- 正常流式输出逻辑 ---
        # 4. 如果第一个步骤是普通消息，则先将其内容发送给前端
        full_content = ""
        if agent_chunk := first_chunk.get("agent"):
            if content := agent_chunk["messages"][-1].content:
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                full_content += content

        # 5. 继续处理迭代器中剩余的所有步骤，并将内容流式发送
        async for chunk in astream:
            if agent_chunk := chunk.get("agent"):
                if content := agent_chunk["messages"][-1].content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    full_content += content

        # 6. 如果图正常运行结束（没有工具调用），更新完整的对话历史
        if full_content:
            final_messages = current_input["messages"] + [("assistant", full_content)]
            conversation_states[thread_id] = {"messages": final_messages}

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@app.post("/continue")
async def continue_stream(request: ContinueRequest):
    """
    在用户确认工具调用后，继续执行 Agent Graph 的接口。
    """
    thread_id = request.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    # 1. 从内存中恢复被中断的会话状态
    state = conversation_states.get(thread_id)
    if not state:
        return {"error": "Thread not found"}

    # 2. 手动执行用户已确认的工具
    tool_results = tool_node.invoke(request.tool_choice)

    # 3. **核心修复**：
    # 使用 .extend() 而不是 .append() 来添加工具结果。
    # 因为 tool_node.invoke() 返回的是一个 ToolMessage 列表 [ToolMessage(...)],
    # .extend() 会将列表中的元素逐个添加到 state["messages"] 中，保持列表的扁平结构。
    state["messages"].extend(tool_results)

    # 4. 重新初始化 LLM 和图
    llm = init_model("ollama", "qwen3:1.7b")
    graph = create_agent_graph(llm, tools)

    async def stream_generator():
        """这个生成器负责处理工具执行后的最终回复。"""
        # 5. 再次调用 astream，输入是包含了正确工具结果的完整状态
        async for chunk in graph.astream(state, config=config):
            if agent_chunk := chunk.get("agent"):
                final_message = agent_chunk["messages"][-1]
                if final_message.content:
                    print(f"Final content from agent: {final_message.content}")
                    yield f"data: {json.dumps({'type': 'content', 'content': final_message.content})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# --- 5. 启动服务器 ---

if __name__ == "__main__":
    # 这段代码允许你通过 `python main.py` 直接运行应用
    # host="0.0.0.0" 让服务器可以被局域网内的其他设备访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
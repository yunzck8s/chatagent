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
from langchain_core.messages import ToolMessage

# --- 1. 初始化 ---

load_dotenv()
app = FastAPI()
tools = [get_tavily_tool()]
tool_node = ToolNode(tools)


# We no longer need conversation_states for history.
# LangGraph's checkpointer handles state via thread_id.

# --- 2. 定义数据模型 ---

class ChatMessage(BaseModel):
    text: str
    provider: str = "ollama"
    model: str = "qwen3:8b"
    thread_id: Optional[str] = None


class ContinueRequest(BaseModel):
    thread_id: str
    tool_choice: List[Dict[str, Any]]


# --- 3. 加载前端 HTML ---

try:
    with open("src/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
except FileNotFoundError:
    html_content = "<html><body><h1>错误: src/index.html 未找到</h1></body></html>"


# --- 4. 定义 FastAPI 路由 ---

@app.get("/")
def read_root():
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/models")
def get_models():
    return get_available_models()


@app.post("/chat")
async def chat_stream(chat_message: ChatMessage):
    """
    处理初始聊天请求。
    """
    thread_id = chat_message.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # **核心修复**: 输入只包含当前的用户消息。
    # LangGraph会利用thread_id自动从其内存中加载此会话的历史记录。
    graph_input = {"messages": [("user", chat_message.text)]}

    llm = init_model(chat_message.provider, chat_message.model)
    graph = create_agent_graph(llm, tools)

    async def stream_generator():
        final_ai_message = None

        async for event in graph.astream_events(graph_input, config=config, version="v2"):
            event_type = event["event"]

            if event_type == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if final_ai_message is None:
                    final_ai_message = chunk
                else:
                    final_ai_message += chunk

                if content := chunk.content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

            if event_type == "on_chain_end" and event["name"] == "agent":
                if final_ai_message and final_ai_message.tool_calls:
                    print("Tool call detected, interrupting for confirmation.")
                    tool_calls_data = final_ai_message.tool_calls
                    yield f"data: {json.dumps({'type': 'tool_request', 'content': [tc['name'] for tc in tool_calls_data], 'tool_choice': tool_calls_data, 'thread_id': thread_id})}\n\n"
                    return

    return StreamingResponse(stream_generator(), media_type="text-event-stream")


@app.post("/continue")
async def continue_stream(request: ContinueRequest):
    """
    在用户确认工具调用后，继续执行 Agent Graph 的接口。
    """
    thread_id = request.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    # 手动执行工具，获取工具结果（一个 ToolMessage 列表）
    tool_messages = tool_node.invoke(request.tool_choice)

    # **核心修复**: 输入只包含新的工具消息。
    # LangGraph会利用thread_id自动加载历史并正确合并这个新消息。
    graph_input = {"messages": tool_messages}

    llm = init_model("ollama", "qwen3:8b")
    graph = create_agent_graph(llm, tools)

    async def stream_generator():
        async for event in graph.astream_events(graph_input, config=config, version="v2"):
            event_type = event["event"]

            if event_type == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if content := chunk.content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text-event-stream")


# --- 5. 启动服务器 ---

if __name__ == "__main__":
    # 使用 reload=True 可以在代码变更后自动重启服务，方便开发
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
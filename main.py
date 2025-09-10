import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import json

# --- 从我们自己的模块中导入“零件” ---
from src.models import init_model, get_available_models
from src.tools.tavily import get_tavily_tool
from src.agent.react import create_agent_graph

# --- 1. 初始化所有组件 ---
# 初始化默认 LLM (保持向后兼容)
llm = init_model("ollama", "qwen3:8b")

# 初始化工具列表
tools = [get_tavily_tool()]

# 使用“工厂”函数创建代理
# 我们把 LLM 和工具列表传进去，它就会返回一个编译好的图
graph = create_agent_graph(llm, tools)

# --- 2. 定义 FastAPI 的请求和应用 ---
class ChatMessage(BaseModel):
    text: str
    # Add model selection fields
    provider: str = "ollama"
    model: str = "qwen3:8b"

class ModelRequest(BaseModel):
    provider: str
    model: str

class ToolConfirmation(BaseModel):
    confirmed: bool
    tool_call_id: str

app = FastAPI()

# --- 3. 读取 HTML 文件 ---
try:
    with open("src/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
except FileNotFoundError:
    # 注意：确保 index.html 在 src 文件夹下
    html_content = "<html><body><h1>错误: src/index.html 未找到</h1></body></html>"

# --- 4. 定义 FastAPI 路由 ---
@app.get("/")
def read_root():
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/models")
def get_models():
    """Return available models grouped by provider"""
    return get_available_models()

@app.post("/chat")
async def chat_stream(chat_message: ChatMessage):
    try:
        selected_llm = init_model(chat_message.provider, chat_message.model)
        selected_graph = create_agent_graph(selected_llm, tools)
    except Exception as e:
        selected_llm = init_model("ollama", "qwen3:8b")
        selected_graph = create_agent_graph(selected_llm, tools)
    
    async def stream_generator():
        full_content = ""
        thought_content = ""
        
        async for chunk in selected_graph.astream({"messages": [("user", chat_message.text)]}):
            if agent_output := chunk.get("agent"):
                ai_message = agent_output["messages"][-1]

                # Handle thinking content
                if hasattr(ai_message, 'thought'):
                    new_thought = ai_message.thought[len(thought_content):]
                    if new_thought:
                        thought_content += new_thought
                        yield f"data: {json.dumps({'type': 'thought', 'content': new_thought})}\n\n"
                
                # Handle regular content
                new_content = ai_message.content[len(full_content):]
                if new_content:
                    full_content += new_content
                    yield f"data: {json.dumps({'type': 'content', 'content': new_content})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.post("/confirm_tool")
async def confirm_tool(confirmation: ToolConfirmation):
    # This endpoint would handle tool confirmation in a more complex implementation
    # For now, we'll handle confirmation on the frontend side
    pass

# --- 5. (可选) 允许直接运行此文件 ---
if __name__ == "__main__":
    # 运行时请确保你的工作目录是 chatagent (src 的上一级)
    uvicorn.run(app, host="0.0.0.0", port=8000)
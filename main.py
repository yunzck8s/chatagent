import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import json
import uuid
from typing import Optional, Callable, List, Dict, Any
from langgraph.checkpoint.memory import InMemorySaver
# 用于加载 .env 文件中的环境变量
from dotenv import load_dotenv

# LangGraph 和 LangChain 的核心组件
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessageChunk, ToolMessage

# 从我们自己的模块中导入 "零件"
from src.models import init_model, get_available_models
from src.tools.tavily import get_tavily_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_core.tools import BaseTool, tool as create_tool
# 加载环境变量
load_dotenv()

def book_hotel(hotel_name: str):
   """Book a hotel"""
   return f"Successfully booked a stay at {hotel_name}."

# --- 1. 初始化 ---
app = FastAPI()
# checkpointer 用于在内存中保存每个会话的状态
checkpointer = InMemorySaver()

# Get the tools without custom interrupt wrappers
tools = [
    get_tavily_tool(),  # Tavily tool
    book_hotel,         # book_hotel function
]

# 存储活动的 agent executors
active_agents = {}

# --- 2. 定义数据模型 ---
class ChatRequest(BaseModel):
    text: str
    provider: str = "ollama"
    model: str = "qwen3:8b"
    thread_id: Optional[str] = None

class ToolConfirmation(BaseModel):
    thread_id: str
    approved: bool
    tool_calls: Optional[List[Dict[str, Any]]] = None

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
async def chat_stream(request: ChatRequest):
    """
    使用 create_react_agent 处理聊天请求，并以 messages 模式流式返回结果。
    """
    # 1. 初始化模型和 Agent
    try:
        selected_llm = init_model(request.provider, request.model)
        agent_executor = create_react_agent(
            model=selected_llm,
            tools=tools,
            checkpointer=checkpointer,
            interrupt_before=["tools"]  # 在工具执行前中断
        )
    except Exception as e:
        print(f"模型初始化失败，使用备用模型: {e}")
        fallback_llm = init_model("ollama", "qwen3:8b")
        agent_executor = create_react_agent(
            model=fallback_llm,
            tools=tools,
            checkpointer=checkpointer,
            interrupt_before=["tools"]  # 在工具执行前中断
        )

    # 2. 准备输入和配置
    thread_id = request.thread_id or str(uuid.uuid4())
    # 保存 agent executor 供后续使用
    active_agents[thread_id] = agent_executor
    config = {"configurable": {"thread_id": thread_id}}
    graph_input = {"messages": [("user", request.text)]}

    async def stream_generator():
        # 发送开始处理的状态
        yield f"data: {json.dumps({'type': 'thought', 'content': '开始处理您的请求...', 'thread_id': thread_id})}\n\n"
        
        # 用于跟踪是否已发送工具调用消息
        tool_call_sent = False
        
        # 3. **核心**: 使用 astream 并设置 stream_mode="messages"
        # 这会流式返回一个个消息对象 (AIMessageChunk, ToolMessage 等)
        try:
            async for chunk in agent_executor.astream(graph_input, config=config, stream_mode="messages"):
                # 处理不同类型的chunk
                if isinstance(chunk, tuple) and len(chunk) >= 2:
                    # 如果是元组，通常第一个元素是消息，第二个是元数据
                    message = chunk[0]
                    
                    # a. 检查消息块是否是 AI 的回复 (AIMessageChunk)
                    if isinstance(message, AIMessageChunk):
                        # 如果包含文本内容，则作为 "content" 类型发送
                        if message.content:
                            yield f"data: {json.dumps({'type': 'content', 'content': message.content, 'thread_id': thread_id})}\n\n"

                        # 如果包含工具调用请求，只发送一次
                        if message.tool_calls and not tool_call_sent:
                            tool_call = message.tool_calls[0]
                            tool_name = tool_call['name']
                            tool_args = tool_call['args']
                            yield f"data: {json.dumps({'type': 'tool_request', 'tool_name': tool_name, 'arguments': tool_args, 'thread_id': thread_id})}\n\n"
                            tool_call_sent = True

                    # b. 检查消息块是否是工具的执行结果 (ToolMessage)
                    elif isinstance(message, ToolMessage):
                        # 将工具的返回结果作为 "tool_result" 类型发送
                        yield f"data: {json.dumps({'type': 'tool_result', 'content': str(message.content), 'thread_id': thread_id})}\n\n"
                        
                elif isinstance(chunk, AIMessageChunk):
                    # 如果包含文本内容，则作为 "content" 类型发送
                    if chunk.content:
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk.content, 'thread_id': thread_id})}\n\n"

                    # 如果包含工具调用请求，只发送一次
                    if chunk.tool_calls and not tool_call_sent:
                        tool_call = chunk.tool_calls[0]
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        yield f"data: {json.dumps({'type': 'tool_request', 'tool_name': tool_name, 'arguments': tool_args, 'thread_id': thread_id})}\n\n"
                        tool_call_sent = True

                # b. 检查消息块是否是工具的执行结果 (ToolMessage)
                elif isinstance(chunk, ToolMessage):
                    # 将工具的返回结果作为 "tool_result" 类型发送
                    yield f"data: {json.dumps({'type': 'tool_result', 'content': str(chunk.content), 'thread_id': thread_id})}\n\n"
                    
        except Exception as e:
            print(f"Error during streaming: {e}")  # 调试信息
            yield f"data: {json.dumps({'type': 'thought', 'content': f'处理出错: {str(e)}', 'thread_id': thread_id})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@app.post("/continue_thread")
async def continue_thread(confirmation: ToolConfirmation):
    """
    继续执行被中断的线程
    """
    thread_id = confirmation.thread_id
    config = {"configurable": {"thread_id": thread_id}}
    
    # 检查是否有活动的 agent
    if thread_id not in active_agents:
        return {"status": "error", "message": "未找到对应的 agent"}
    
    agent_executor = active_agents[thread_id]
    
    try:
        # Check if there's an interrupt
        state = agent_executor.get_state(config)
        
        # If there's an interrupt, continue with the appropriate command
        if state.next:
            # Use the correct resume value based on approval
            if confirmation.approved:
                # Resume execution to actually run the tools
                result = agent_executor.invoke(None, config=config)
            else:
                # For rejection, we need to handle it differently
                # We'll send a message back to the LLM to continue without tool execution
                result = agent_executor.invoke(
                    {"messages": [("user", "User rejected the tool execution. Please continue without using the tool and provide a response based on your existing knowledge.")]}, 
                    config=config
                )
        else:
            # If there's no interrupt, just return the current state
            result = {"messages": state.values["messages"]}
        
        # 获取工具执行结果
        tool_result = None
        final_response = None
        
        if result and "messages" in result:
            # Look for the last ToolMessage in the messages
            for message in reversed(result["messages"]):
                if isinstance(message, ToolMessage):
                    tool_result = str(message.content)
                    break
            
            # Get the final AI response
            for message in reversed(result["messages"]):
                if hasattr(message, 'content') and message.content and not isinstance(message, ToolMessage):
                    final_response = str(message.content)
                    break
        
        return {
            "status": "success",
            "message": "工具调用已处理",
            "thread_id": thread_id,
            "result": tool_result,
            "final_response": final_response,
            "approved": confirmation.approved
        }
    except Exception as e:
        print(f"Error in continue_thread: {e}")
        return {"status": "error", "message": f"继续执行失败: {str(e)}"}


# --- 5. 启动服务器 ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
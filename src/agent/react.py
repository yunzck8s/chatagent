# src/agent/react.py

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# --- 1. 定义状态 ---
# 这个状态会在我们整个图中流动
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# --- 2. 定义边 (Edges) 的决策逻辑 ---
# 这个函数决定在调用 LLM 后，下一步是去调用工具还是结束
def route_tools(state: AgentState):
    if messages := state.get("messages", []):
        ai_message = messages[-1]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
    return END


# --- 3. 定义图的“工厂”函数 ---
# 这是我们的核心，它负责组装并创建代理
def create_agent_graph(llm, tools):
    """
    接收一个 LLM 和一个工具列表，返回一个编译好的、可执行的 LangGraph 代理。
    """
    # 将工具绑定到 LLM，让 LLM 知道它有哪些工具可用
    llm_with_tools = llm.bind_tools(tools)

    # 定义代理节点
    def agent_node(state: AgentState):
        result = llm_with_tools.invoke(state["messages"])
        return {"messages": [result]}

    # 定义工具节点
    tool_node = ToolNode(tools)

    # 开始构建图
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    graph_builder.set_entry_point("agent")

    graph_builder.add_conditional_edges(
        "agent",
        route_tools,
        {"tools": "tools", END: END}
    )
    graph_builder.add_edge("tools", "agent")

    # 编译图并返回
    graph = graph_builder.compile()
    return graph
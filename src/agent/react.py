# src/agent/react.py

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
# ** 1. 从 langgraph.graph.message 导入 add_messages **
from langgraph.graph.message import add_messages


# --- 1. 定义状态 ---
class AgentState(TypedDict):
    # ** 2. 使用 add_messages 代替 lambda 函数 **
    # 这是修复 TypeError 的关键。add_messages 是 LangGraph 官方提供的、更强大的消息合并函数。
    messages: Annotated[list[BaseMessage], add_messages]


# --- 2. 定义图的“工厂”函数 ---
def create_agent_graph(llm, tools):
    """
    接收一个 LLM 和一个工具列表，返回一个编译好的、可执行的 LangGraph 代理。
    """
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        # 从状态中总是获取最新的消息列表
        result = llm_with_tools.invoke(state["messages"])
        return {"messages": [result]}

    tool_node = ToolNode(tools)

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)
    graph_builder.set_entry_point("agent")

    # 使用内置的 tools_condition 来决定下一步是调用工具还是结束
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}
    )

    # 工具执行完后，必须回到 agent 节点进行总结
    graph_builder.add_edge("tools", "agent")

    # 编译图
    graph = graph_builder.compile()
    return graph
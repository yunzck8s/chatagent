# src/agent/react.py

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition


# --- 1. 定义状态 ---
# 使用 lambda 来正确合并消息列表
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], lambda x, y: x + y]


# --- 2. 定义图的“工厂”函数 ---
def create_agent_graph(llm, tools):
    """
    接收一个 LLM 和一个工具列表，返回一个编译好的、可执行的 LangGraph 代理。
    这个版本是为流式处理和手动工具确认而设计的。
    """
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        result = llm_with_tools.invoke(state["messages"])
        return {"messages": [result]}

    tool_node = ToolNode(tools)

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)
    graph_builder.set_entry_point("agent")

    # 当 agent 节点运行后，使用 tools_condition 判断下一步
    # 1. 如果需要工具，则转到 "tools" 节点
    # 2. 如果不需要工具，则结束 (END)
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}
    )

    # 工具执行完后，必须回到 agent 节点进行总结
    graph_builder.add_edge("tools", "agent")

    # 我们不在编译时中断，而是在后端的 stream 中通过检查 tool_calls 来“模拟”中断
    graph = graph_builder.compile()
    return graph
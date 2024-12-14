from dotenv import load_dotenv

load_dotenv()

from re import M
from typing_extensions import TypedDict
from typing import Literal, Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, AnyMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition

from my_agent.utils.state import ReservState
from my_agent.utils.nodes import Assistant, user_info
from my_agent.utils.utils import create_tool_node_with_fallback
from my_agent.utils.runnables import assistant_runnable
from my_agent.utils.tools.reservation import (
    safe_tools,
    sensitive_tools,
    sensitive_tool_names,
)


# Define the config
class GraphConfig(TypedDict):
    model_name: Literal["openai"]


def route_tools(state: ReservState):
    next_node = tools_condition(state)
    if next_node == END:
        return END
    ai_message = state["messages"][-1]

    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in sensitive_tool_names:
        return "sensitive_tools"
    return "safe_tools"


def buildGraph():
    builder = StateGraph(ReservState)

    builder.add_node("fetch_user_info", user_info)
    builder.add_node("assistant", Assistant(assistant_runnable))
    builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
    builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))

    builder.add_edge(START, "fetch_user_info")
    builder.add_edge("fetch_user_info", "assistant")

    builder.add_conditional_edges(
        "assistant", route_tools, ["safe_tools", "sensitive_tools", END]
    )
    builder.add_edge("safe_tools", "assistant")
    builder.add_edge("sensitive_tools", "assistant")

    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["sensitive_tools"],
    )
    return graph


import os
import uuid
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from my_agent.utils.utils import _print_event
from supabase import create_client, Client


def get_first_user_info():
    if config["configurable"]["phone_number"] != None:
        config["configurable"]["phone_number"] = input("Plz Enter your phone number: ")


if __name__ == "__main__":
    load_dotenv()

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    graph = buildGraph()
    thread_id = str(uuid.uuid4())

    config = {"configurable": {"phone_number": "", "thread_id": thread_id}}
    get_first_user_info()

    while True:
        question = input("Hello! Enter the question: ")

        if question in ["q"]:
            break
        _printed = set()

        events = graph.stream(
            {"messages": ("user", question)}, config, stream_mode="values"
        )
        for event in events:
            _print_event(event, _printed)

        snapshot = graph.get_state(config)

        while snapshot.next:
            try:
                user_input = input(
                    "다음의 행동에 동의하십니까? 동의하시면 'y'를 입력해주세요."
                    "만약 동의하지 않는다면 다른 답변을 입력해주시기 바랍니다.\n\n"
                )
            except:
                user_input = "y"
            if user_input.strip() == "y":
                result = graph.invoke(
                    None,
                    config,
                )
            else:
                result = graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                                content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                            )
                        ]
                    },
                    config,
                )
            snapshot = graph.get_state(config)

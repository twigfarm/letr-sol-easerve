from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from re import M
from typing_extensions import TypedDict
from typing import Literal, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.graph.message import add_messages, AnyMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition
from my_agent.utils.state import ReservState
from my_agent.utils.nodes import Assistant, route_question_adaptive, rag_assistant
from my_agent.utils.utils import create_tool_node_with_fallback
from my_agent.utils.runnables import assistant_runnable
from my_agent.utils.tools.reservation import (
    safe_tools,
    sensitive_tools,
    sensitive_tool_names,
)
from my_agent.utils.tools.rag import rag_assistant_tool_node
from my_agent.utils.utils import parse_phone_number


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


# 기본적인 연결은 add_edge로, add_conditional_edge 보다는 Command 처리방식이 권장됨
def buildGraph():
    builder = StateGraph(ReservState)

    builder.add_node("first_question_router", route_question_adaptive)
    builder.add_node("reservation_assistant", Assistant(assistant_runnable))
    builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
    builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
    builder.add_node("rag_assistant", rag_assistant)
    builder.add_node("tools", rag_assistant_tool_node)

    builder.add_edge(START, "first_question_router")

    builder.add_conditional_edges(
        "rag_assistant",
        tools_condition,
    )

    builder.add_edge("safe_tools", "reservation_assistant")
    builder.add_edge("sensitive_tools", "reservation_assistant")
    builder.add_edge("tools", "rag_assistant")

    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
    )
    return graph


import uuid
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from my_agent.utils.utils import _print_event
import streamlit as st


def set_user_input(user_input):
    st.session_state.user_input = user_input


if __name__ == "__main__":
    load_dotenv()

    if "graph" not in st.session_state:
        st.session_state.graph = buildGraph()

    if "config" not in st.session_state:
        thread_id = str(uuid.uuid4())

        st.session_state.config = {"configurable": {"phone_number": "", "thread_id": thread_id}}
    print(st.session_state.config)

    st.title("강아지 미용 예약 서비스 챗봇입니다!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 먼저 전화번호를 입력해주세요! ex)01012345678"}]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is up?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        if st.session_state.config["configurable"]["phone_number"] == "":
            phone_number = parse_phone_number(prompt)
            print(phone_number)
            if phone_number == None:
                st.session_state.messages.append({"role": "assistant", "content": "전화번호가 잘못 입력되었습니다 다시 입력해주세요."})
                st.rerun()
            else: 
                st.session_state.config["configurable"]["phone_number"] = prompt
                st.session_state.messages.append({"role": "assistant", "content": "전화번호 입력이 완료되었습니다!"})
                st.rerun()
        _printed = set()

        events = st.session_state.graph.stream(
            {"messages": st.session_state.messages}, st.session_state.config, stream_mode="values"
        )
        for event in events:
            _print_event(event, _printed)
            final_response = event["messages"][-1].content
            st.session_state.event = event

        response = f"{final_response}"
        if final_response == "":
            response = "진행하시겠습니까?"
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    if "user_input" not in st.session_state:
        st.session_state.user_input = None
    if st.session_state.user_input is None:
        st.session_state.snapshot = st.session_state.graph.get_state(
            st.session_state.config
        )

    # print(f"st.session_state.snapshot: {st.session_state.snapshot}")
    is_in_snapshot = False
    while st.session_state.snapshot.next:
        is_in_snapshot = True
        if st.session_state.user_input is None:
            try:
                if st.button("Yes", on_click=set_user_input, args=("y",)):
                    print("Yes")
                if st.button("No", on_click=set_user_input, args=("n",)):
                    print("No")
            except:
                user_input = "y"
        if st.session_state.user_input is not None:
            if st.session_state.user_input.strip() == "y":
                result = st.session_state.graph.invoke(
                    Command(resume={"action": "continue"}),
                    st.session_state.config,
                )
                st.session_state.messages[-1]["content"] = result["messages"][
                    -1
                ].content
                print(f"result: {result}")
            else:
                result = st.session_state.graph.invoke(
                    Command(resume={"action": "terminate"}),

                    st.session_state.config,
                )
                st.session_state.messages[-1]['content'] = result["messages"][-1].content
            st.session_state.user_input = None
            st.session_state.snapshot = st.session_state.graph.get_state(
                st.session_state.config
            )
    if is_in_snapshot:
        is_in_snapshot = False
        st.rerun()

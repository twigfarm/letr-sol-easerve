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
from my_agent.utils.nodes import (
    Assistant,
    route_question_adaptive,
    rag_assistant,
    terminate_irrelevant_chat,
)
from my_agent.utils.utils import create_tool_node_with_fallback
from my_agent.utils.runnables import assistant_runnable
from my_agent.utils.tools.reservation import (
    primary_safe_tools,
    primary_sensitive_tools,
    primary_sensitive_tool_names,
)
from my_agent.utils.tools.rag import rag_safe_tools, rag_sensitive_tools
from my_agent.utils.utils import parse_phone_number
from langchain_core.messages import HumanMessage, AIMessage


# Define the config
class GraphConfig(TypedDict):
    model_name: Literal["openai"]


def route_tools(state: ReservState):
    next_node = tools_condition(state)
    if next_node == END:
        return END
    ai_message = state["messages"][-1]

    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in primary_sensitive_tool_names:
        return "primary_sensitive_tools"
    return "primary_safe_tools"


# 기본적인 연결은 add_edge로, add_conditional_edge 보다는 Command 처리방식이 권장됨
def buildGraph():
    builder = StateGraph(ReservState)

    builder.add_node("first_question_router", route_question_adaptive)
    builder.add_node("reservation_assistant", Assistant(assistant_runnable))
    builder.add_node(
        "primary_safe_tools", create_tool_node_with_fallback(primary_safe_tools)
    )
    builder.add_node(
        "primary_sensitive_tools",
        create_tool_node_with_fallback(primary_sensitive_tools),
    )
    builder.add_node("rag_assistant", rag_assistant)
    builder.add_node("rag_safe_tools", create_tool_node_with_fallback(rag_safe_tools))
    builder.add_node(
        "rag_sensitive_tools", create_tool_node_with_fallback(rag_sensitive_tools)
    )
    builder.add_node("terminate_irrelevant", terminate_irrelevant_chat)

    builder.add_edge(START, "first_question_router")
    builder.add_edge("primary_safe_tools", "reservation_assistant")
    builder.add_edge("primary_sensitive_tools", "reservation_assistant")
    builder.add_edge("rag_safe_tools", "rag_assistant")
    builder.add_edge("rag_sensitive_tools", "rag_assistant")

    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
    )
    return graph


from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from my_agent.utils.utils import _print_event
import streamlit as st
from my_agent.utils.db import init_db, update_phone_number
from my_agent.utils.chat import init_session_state, save_message
from my_agent.utils.ui import (
    sidebar_ui,
    get_selected_session,
    set_selected_session,
    display_messages,
)


def set_user_input(user_input):
    st.session_state.user_input = user_input


if __name__ == "__main__":
    load_dotenv()
    init_db()
    init_session_state()

    if "graph" not in st.session_state:
        st.session_state.graph = buildGraph()

    with st.sidebar:
        selected_session_id = sidebar_ui()
        # 세션 선택 변경 시 메시지 로드
        if (
            selected_session_id is not None
            and selected_session_id != get_selected_session()
        ):
            set_selected_session(selected_session_id)

    current_session_id = get_selected_session()

    if current_session_id is None:
        st.write("채팅방을 선택하거나 새로 만들어 주세요.")
        st.stop()

    st.title("강아지 미용 예약 서비스 챗봇입니다!")

    str = (
        "안녕하세요! \n이리온 댕댕입니다 🐾  \n"
        "더욱 편리하고 개인 맞춤형 예약 서비스를  \n"
        "제공하기 위해 휴대전화 번호를 입력해 주세요.  \n"
        "입력하신 번호는 본인 확인과 이전 상담 기록  \n"
        "확인에 활용되며, 고객님과 반려동물을 위한 최적의 서비스를 준비하는 데 사용됩니다. 😊  \n"
        "ex)01012345678  \n"
    )
    if len(st.session_state.messages) == 0:
        st.session_state.messages.append(AIMessage(content=str))
        save_message(current_session_id, "assistant", str)

    display_messages(st.session_state.messages)

    # React to user input
    if prompt := st.chat_input("What is up?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append(HumanMessage(content=prompt))
        save_message(current_session_id, "user", prompt)
        if st.session_state.config["configurable"]["phone_number"] == "":
            phone_number = parse_phone_number(prompt)
            if phone_number == []:

                st.session_state.messages.append(
                    AIMessage(
                        content="전화번호가 잘못 입력되었습니다 다시 입력해주세요."
                    )
                )
                save_message(
                    current_session_id,
                    "assistant",
                    "전화번호가 잘못 입력되었습니다 다시 입력해주세요.",
                )
                st.rerun()
            else:
                st.session_state.config["configurable"]["phone_number"] = phone_number[
                    0
                ]
                update_phone_number(current_session_id, phone_number[0])
                st.session_state.messages.append(
                    AIMessage(
                        content="전화번호 입력이 완료되었습니다! 예약 상담을 도와드리겠습니다."
                    )
                )
                save_message(
                    current_session_id,
                    "assistant",
                    "전화번호 입력이 완료되었습니다! 예약 상담을 도와드리겠습니다.",
                )
                st.rerun()
        _printed = set()

        events = st.session_state.graph.stream(
            {"messages": st.session_state.messages},
            st.session_state.config,
            stream_mode="values",
        )
        for event in events:
            _print_event(event, _printed)
            final_response = event["messages"][-1].content
            st.session_state.event = event

        response = f"{final_response}"
        if final_response == "":
            response = "진행하시겠습니까?"
        # if (isinstance(st.session_state.event["messages"][-1],HumanMessage)):
        #     response = "죄송해요, 말씀하신 내용을 잘 이해하지 못했어요. 다시 시도하시거나, 구체적인 질문을 입력해 주세요. 예를 들어 '예약 변경' 또는 '가격 확인' 등을 말씀해주시면 더 잘 도와드릴 수 있어요!"
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append(AIMessage(content=response))
        save_message(current_session_id, "assistant", response)

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
                print(st.session_state.messages[-1])
                print(result["messages"][-1])
                # AIMessage를 수정할 수 없는 문제 발생
                if isinstance(st.session_state.messages[-1], AIMessage):
                    st.session_state.messages[-1] = AIMessage(
                        content=result["messages"][-1].content,
                        additional_kwargs=result["messages"][-1].additional_kwargs,
                        response_metadata=result["messages"][-1].response_metadata,
                    )
                else:
                    st.session_state.messages[-1]["content"] = result["messages"][
                        -1
                    ].content
            else:
                result = st.session_state.graph.invoke(
                    Command(resume={"action": "terminate"}),
                    st.session_state.config,
                )
                st.session_state.messages[-1]["content"] = result["messages"][
                    -1
                ].content
            st.session_state.user_input = None
            st.session_state.snapshot = st.session_state.graph.get_state(
                st.session_state.config
            )
    if is_in_snapshot:
        is_in_snapshot = False
        st.rerun()

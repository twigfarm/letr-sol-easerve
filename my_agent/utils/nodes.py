from typing import Literal
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from my_agent.utils.state import ReservState
from my_agent.utils.tools.user import fetch_user_info
from my_agent.utils.runnables import router_runnable
from my_agent.utils.tools.reservation import primary_sensitive_tool_names
from my_agent.utils.tools.rag import rag_sensitive_tool_names
from .tools.rag import rag_runnable
from langgraph.types import interrupt, Command
from langgraph.prebuilt import tools_condition
from langgraph.graph import END
from langchain_core.messages import ToolMessage


def user_info(state: ReservState):
    return {"user_info": fetch_user_info.invoke({})}


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: ReservState, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state, config=config)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                # 설명 필요
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break

        # Command로 node 이동
        next_node = tools_condition({"messages": [result]})
        if next_node == END:
            print(f"terminate, {result.content}")
            # END로 갈 때 messages 업데이트 하는 방법 찾기
            return Command(goto=END, update={"messages": result})

        first_tool_call = result.tool_calls[0]
        if first_tool_call["name"] in primary_sensitive_tool_names:
            print("sensitive")
            human_chk = interrupt({})
            chk_action = human_chk["action"]
            if chk_action == "continue":
                return Command(
                    goto="primary_sensitive_tools", update={"messages": [result]}
                )
            else:
                return Command(
                    goto="reservation_assistant",
                    update={
                        "messages": [
                            result,
                            ToolMessage(
                                tool_call_id=result.tool_calls[0]["id"],
                                content=f"API call denied by user. Reasoning: 'user abort tool'. Continue assisting, accounting for the user's input.",
                            ),
                        ]
                    },
                )
        else:
            print("safe")
            return Command(goto="primary_safe_tools", update={"messages": [result]})


def rag_assistant(state: ReservState):
    result = rag_runnable.invoke(state["messages"])
    next_node = tools_condition({"messages": [result]})
    if next_node == END:
        # END로 갈 때 messages 업데이트 하는 방법 찾기
        return Command(goto=END, update={"messages": result})
    first_tool_call = result.tool_calls[0]
    if first_tool_call["name"] in rag_sensitive_tool_names:
        print("sensitive")
        human_chk = interrupt({})
        chk_action = human_chk["action"]
        if chk_action == "continue":
            return Command(goto="rag_sensitive_tools", update={"messages": [result]})
        else:
            return Command(
                goto="rag_assistant",
                update={
                    "messages": [
                        result,
                        ToolMessage(
                            tool_call_id=result.tool_calls[0]["id"],
                            content=f"API call denied by user. Reasoning: 'user abort tool'. Continue assisting, accounting for the user's input.",
                        ),
                    ]
                },
            )
    else:
        return Command(goto="rag_safe_tools", update={"messages": [result]})


def route_question_adaptive(state: ReservState):

    latest_message = state["messages"]
    try:
        result = router_runnable.invoke({"messages": latest_message})

        datasource = result.tool

        if datasource == "reservation_assistant":
            return Command(goto="reservation_assistant")
        elif datasource == "rag_assistant":
            return Command(goto="rag_assistant")
        else:
            return Command(goto=END)
    except Exception as e:
        return Command(goto=END)

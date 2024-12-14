from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from my_agent.utils.state import ReservState
from my_agent.utils.tools.user import fetch_user_info


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
        return {"messages": result}

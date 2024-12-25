from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from my_agent.utils.state import ReservState
from langgraph.types import Command


def _get_model(model_name: str):
    if model_name == "openai":
        model = ChatOpenAI(model="gpt-4o-mini")
    else:
        raise ValueError(f"Unsupported model type: {model_name}")
    return model

# Define the logic to call the model
def get_messages_with_summary(state: ReservState):
    summary = state.get("summary", "")
    if summary:
        system_message = f"Summary of conversation earlier: {summary}"
        messages = [SystemMessage(content=system_message)] + state["messages"]
    else:
        messages = state["messages"]
    return {"messages": messages, 'summary': summary}

def summarize_conversation(state: ReservState):
    summary = state.get("summary", "")
    if summary:
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = _get_model("openai").invoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}

def should_summarize(state: ReservState):
    messages = state["messages"]
    print(f"len of messages: {len(messages)}")
    if len(messages) >= 6:
        return Command(goto="summarize_conversation")
    return Command(goto="first_question_router")

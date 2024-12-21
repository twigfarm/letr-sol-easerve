from typing import TypedDict, Annotated
from langgraph.graph.message import AnyMessage, add_messages
from typing import List


class ReservState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    documents: List[str]

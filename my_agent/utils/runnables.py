from functools import lru_cache
from my_agent.utils.tools.reservation import tools
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from datetime import date, datetime
from langchain.tools import Tool
from my_agent.utils.state import ReservState


@lru_cache(maxsize=4)
def _get_model(model_name: str):
    if model_name == "openai":
        model = ChatOpenAI(model="gpt-4o-mini")
    else:
        raise ValueError(f"Unsupported model type: {model_name}")

    model = model.bind_tools(tools)
    return model


assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Reservation Service. "
            " Use the provided tools to search reservations, add reservation, update reservation and delete reservation"
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If reservations searched still comes up empty, stop searching. It means the reservation does not exist. "
            # "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

assistant_runnable = assistant_prompt | _get_model("openai")

from pydantic import BaseModel, Field
from typing import Literal


class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    tool: Literal["reservation_assistant", "rag_assistant", "terminate"] = Field(
        ...,
        description="Given a user question choose to route it to reservation_assistant or rag_assistant or terminate",
    )


from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

route_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert at routing a user question to a reservation_assistant, rag_assistant and terminate.
            The reservation_assistant is responsible for canceling and changing(updating) reservation.
            The rag_assistant is responsible for finding information and adding new reservation.
            Use the reservation_assistant and rag_assistant about reservation. Otherwise, select terminate.""",
        ),
        ("human", "{messages}"),
    ]
)

model = ChatOpenAI(model="gpt-4o-mini")
structured_model = model.with_structured_output(RouteQuery)

router_runnable = route_prompt | structured_model

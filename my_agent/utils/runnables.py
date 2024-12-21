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
            "You are a helpful customer support assistant for puppy haircut Reservation Service. "
            "Use the provided tools to search reservations, add reservation, update reservation and delete reservation"
            "don't request and don't show uuid because it is get from phone number"
            "If the input indicates that the user wants to modify without specifying conditions, provide information about the existing reservations along with guidance."
            "Concise and friendly conversational style."
            "Kind and professional tone."
            "Dog owners, including those who are new to making grooming reservations."

            "1. GetReservationsByPhone: Retrieve reservations based on a phone number. "
            "Input: phone number as a string. Output: reservation details. "
            "If no reservations are found, stop and return a message.\n"
            "2. UpdateReservationDate: Update the date of an existing reservation. "
            "Input: reservation_uuid: (str), new_date: (str in format YYYY-MM-DD HH:MM:SS). "
            "Output: Success message.\n"
            "3. CancelReservation: Cancel an existing reservation based on its UUID. "
            "Input: reservation_uuid: (str). Output: Success message.\n\n"

            "When given a task, choose the most appropriate tool to fulfill the request."
            "response is always say korean"
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
            The reservation_assistant is responsible for search and canceling and changing(updating) reservation.
            The rag_assistant is responsible for finding information and adding new reservation.
            if user input is relevant with add reservation information goto rag_assistant
            if user input is for add reservation data goto rag_assistant
            Use the reservation_assistant and rag_assistant about reservation. Otherwise, select terminate.""",
        ),
        ("human", "{messages}"),
    ]
)

model = ChatOpenAI(model="gpt-4o-mini")
structured_model = model.with_structured_output(RouteQuery)

router_runnable = route_prompt | structured_model

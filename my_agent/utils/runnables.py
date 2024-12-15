from functools import lru_cache
from my_agent.utils.tools.reservation import tools
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from datetime import date, datetime
from langchain.tools import Tool


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
            " Use the provided tools to search reservations, add reservation, update reservation and delete reservation"
            "if request is not related to reservation, say 'I'm sorry, I can't help with that'."
            "don't request uuid because it is get from phone number"
            "1. GetReservationsByPhone: Retrieve reservations based on a phone number. "
            "Input: phone number as a string. Output: reservation details. "
            "If no reservations are found, stop and return a message.\n"
            "2. UpdateReservationDate: Update the date of an existing reservation. "
            "Input: reservation_uuid: (str), new_date: (str in format YYYY-MM-DD HH:MM:SS). "
            "Output: Success message.\n"
            "3. CancelReservation: Cancel an existing reservation based on its UUID. "
            "Input: reservation_uuid: (str). Output: Success message.\n\n"
            "When given a task, choose the most appropriate tool to fulfill the request."
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

assistant_runnable = assistant_prompt | _get_model("openai")

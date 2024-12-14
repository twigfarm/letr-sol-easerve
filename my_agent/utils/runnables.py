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
            "You are a helpful customer support assistant for Reservation Service. "
            " Use the provided tools to search reservations, add reservation, update reservation and delete reservation"
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

assistant_runnable = assistant_prompt | _get_model("openai")

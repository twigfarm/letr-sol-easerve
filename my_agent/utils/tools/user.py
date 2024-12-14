from langchain_core.runnables import RunnableConfig
from langchain.tools import tool


@tool
def fetch_user_info(config: RunnableConfig) -> list[dict]:
    """Fetch all user info using RunnableConfig"""
    configuration = config.get("configurable", {})
    phone_number = configuration.get("phone_number", None)
    if not phone_number:
        raise ValueError("No phone number configured.")

    return []

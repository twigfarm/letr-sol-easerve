from langchain.tools import Tool
from langchain_core.tools import tool
from my_agent.utils.rpc import (
    get_reservations_by_phone,
    update_reservation_date,
    cancel_reservation,
)
from langchain_core.runnables.config import RunnableConfig

# @tool vs Tool
# Tool은 클래스이며 @tool 데코레이터는 함수를 Tool 객체로 더 쉽게 반환해준다.
# @tool 사용 권장
# 권장사항에 따라 수정했음 - 혹시 몰라서 주석처리 (sunko)

# Tool to get reservations by phone

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field


class UpdateReservationDateInput(BaseModel):
    reservation_uuid: str = Field(
        ..., description="The UUID of the reservation to update"
    )
    new_date: str = Field(
        ...,
        description="The new date and time for the reservation (format: YYYY-MM-DD HH:MM:SS)",
    )


update_reservation = StructuredTool.from_function(
    func=update_reservation_date,
    name="UpdateReservationDate",
    description="Update the date of an existing reservation",
    args_schema=UpdateReservationDateInput,
)


@tool
def search_reservation(config: RunnableConfig):
    """
    Retrieve reservations based on a phone number.
    The phone_number is retrieved from the RunnableConfig
    Don't ask user for the phone number.
    Output: reservation details.
    """
    phone_number = config.get("configurable", {}).get("phone_number")
    return get_reservations_by_phone(phone_number)


# @tool
# def update_reservation(reservation_uuid: str, new_date: str):
#     """
#     Update the date of an existing reservation.
#     Input: reservation_uuid (str), new_date (str in format YYYY-MM-DD).
#     Output: Success message.
#     """
#     return update_reservation_date(reservation_uuid, new_date)


@tool
def delete_reservation(reservation_uuid: str):
    """
    Cancel an existing reservation based on its UUID.
    Input: reservation_uuid (str). Output: Success message.
    """
    return cancel_reservation(reservation_uuid)


primary_safe_tools = [search_reservation]
primary_sensitive_tools = [update_reservation, delete_reservation]
primary_sensitive_tool_names = {t.name for t in primary_sensitive_tools}

primary_tools: list[Tool] = primary_safe_tools + primary_sensitive_tools

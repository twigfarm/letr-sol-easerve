from langchain.tools import Tool
from ..rpc import get_reservations_by_phone, update_reservation_date, cancel_reservation

# @tool vs Tool
# Tool은 클래스이며 @tool 데코레이터는 함수를 Tool 객체로 더 쉽게 반환해준다.
# @tool 사용 권장

# Tool to get reservations by phone
search_reservation = Tool(
    name="GetReservationsByPhone",
    func=lambda phone: get_reservations_by_phone(phone),
    description=(
        "Retrieve reservations based on a phone number. "
        "phone number is get from config: configurable: phone_number"
        "Input: a phone number as a string. Output: reservation details."
        "if reservation data is empty stop find reservation data and return message"
    ),
)

# # Tool to update reservation date
# update_reservation = Tool(
#     name="UpdateReservationDate",
#     func=lambda reservation_uuid, new_date: update_reservation_date(
#         reservation_uuid, new_date
#     ),
#     description=(
#         "Update the date of an existing reservation. "
#         "Input: reservation_uuid (str), new_date (str in format YYYY-MM-DD HH:MM:SS). "
#         "Output: Success message."
#     ),
# )

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

class UpdateReservationDateInput(BaseModel):
    reservation_uuid: str = Field(..., description="The UUID of the reservation to update")
    new_date: str = Field(..., description="The new date and time for the reservation (format: YYYY-MM-DD HH:MM:SS)")

update_reservation = StructuredTool.from_function(
    func=update_reservation_date,
    name="UpdateReservationDate",
    description="Update the date of an existing reservation",
    args_schema=UpdateReservationDateInput
)

# Tool to cancel a reservation
delete_reservation = Tool(
    name="CancelReservation",
    func=lambda reservation_uuid: cancel_reservation(reservation_uuid),
    description=(
        "Cancel an existing reservation based on its UUID. "
        "Input: reservation_uuid (str). Output: Success message."
    ),
)

safe_tools = [search_reservation]
sensitive_tools = [update_reservation, delete_reservation]
sensitive_tool_names = {t.name for t in sensitive_tools}

tools: list[Tool] = safe_tools + sensitive_tools

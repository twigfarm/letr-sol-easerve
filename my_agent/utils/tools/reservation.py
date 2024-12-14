from langchain.tools import Tool

# @tool vs Tool
# Tool은 클래스이며 @tool 데코레이터는 함수를 Tool 객체로 더 쉽게 반환해준다.
# @tool 사용 권장

# Tool to get reservations by phone
search_reservation = Tool(
    name="GetReservationsByPhone",
    func=lambda phone: get_reservations_by_phone(phone),
    description=(
        "Retrieve reservations based on a phone number. "
        "Input: a phone number as a string. Output: reservation details."
    ),
)

# Tool to update reservation date
update_reservation = Tool(
    name="UpdateReservationDate",
    func=lambda reservation_uuid, new_date: update_reservation_date(
        reservation_uuid, new_date
    ),
    description=(
        "Update the date of an existing reservation. "
        "Input: reservation_uuid (str), new_date (str in format YYYY-MM-DD). "
        "Output: Success message."
    ),
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

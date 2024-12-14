from langchain.tools import Tool
from langchain_core.tools import tool
from my_agent.utils.rpc import get_reservations_by_phone, update_reservation_date, cancel_reservation
# @tool vs Tool
# Tool은 클래스이며 @tool 데코레이터는 함수를 Tool 객체로 더 쉽게 반환해준다.
# @tool 사용 권장
# 권장사항에 따라 수정했음 - 혹시 몰라서 주석처리 (sunko)

# Tool to get reservations by phone

@tool
def search_reservation(phone: str):
    """
    Retrieve reservations based on a phone number.
    Input: a phone number as a string. Output: reservation details.
    """
    return get_reservations_by_phone(phone)

@tool
def update_reservation(reservation_uuid: str, new_date: str):
    """
    Update the date of an existing reservation.
    Input: reservation_uuid (str), new_date (str in format YYYY-MM-DD).
    Output: Success message.
    """
    return update_reservation_date(reservation_uuid, new_date)

@tool
def delete_reservation(reservation_uuid: str):
    """
    Cancel an existing reservation based on its UUID.
    Input: reservation_uuid (str). Output: Success message.
    """
    return cancel_reservation(reservation_uuid)

safe_tools = [search_reservation]
sensitive_tools = [update_reservation, delete_reservation]
sensitive_tool_names = {t.name for t in sensitive_tools}

tools: list[Tool] = safe_tools + sensitive_tools

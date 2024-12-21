from langchain.tools import Tool
from langchain_core.tools import tool
from my_agent.utils.rpc import get_reservations_by_phone, update_reservation_date, cancel_reservation
from langchain_core.runnables.config import RunnableConfig
# @tool vs Tool
# Tool은 클래스이며 @tool 데코레이터는 함수를 Tool 객체로 더 쉽게 반환해준다.
# @tool 사용 권장
# 권장사항에 따라 수정했음 - 혹시 몰라서 주석처리 (sunko)

# Tool to get reservations by phone

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class UpdateReservationDateInput(BaseModel):
    reservation_uuid: str = Field(..., description="The UUID of the reservation to update")
    new_date: str = Field(..., description="The new date and time for the reservation (format: YYYY-MM-DD HH:MM:SS)")

update_reservation = StructuredTool.from_function(
    func=update_reservation_date,
    name="UpdateReservationDate",
    description="Update the date of an existing reservation",
    args_schema=UpdateReservationDateInput
)

@tool
def search_reservation(config: RunnableConfig):
    """
    Retrieve reservations based on a phone number.
    The phone_number is retrieved from the RunnableConfig
    Don't ask user for the phone number.
    Show me reservations after the current time.
    Output: 
    ex1) 안녕하세요! 현재 다가오는 예약은 다음과 같습니다

    1. 서비스: 위생미용
       예약 날짜: 2024년 12월 20일 14:00
       상태: 예약대기
       가격: 15,000원

    2. 서비스: 위생미용
       예약 날짜: 2024년 12월 26일 14:00
       상태: 예약대기
       가격: 15,000원

    예약과 관련해 도움이 필요하시면 언제든지 말씀해 주세요!

    ex2) 안녕하세요! 현재 예약이 존재하지 않습니다. 새로운 예약을 원하시면 말씀해주세요!
    """
    #few shot
    phone_number = config.get("configurable", {}).get("phone_number")
    reservations = get_reservations_by_phone(phone_number)
    current_time = datetime.now(timezone.utc)

    #현재시간 이후의 예약만 가져오기
    upcoming_reservations = [
        reservation for reservation in reservations
        if datetime.fromisoformat(reservation['reservation_date']) > current_time
    ]

    return upcoming_reservations

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

safe_tools = [search_reservation]
sensitive_tools = [update_reservation, delete_reservation]
sensitive_tool_names = {t.name for t in sensitive_tools}

tools: list[Tool] = safe_tools + sensitive_tools

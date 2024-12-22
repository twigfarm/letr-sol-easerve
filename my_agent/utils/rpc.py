from .supabase_client import supabase
import os
from supabase import create_client, Client
from dotenv import load_dotenv


def get_supabase_client() -> Client:
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


def get_reservations_by_phone(phone: str) -> dict:
    supabase: Client = get_supabase_client()
    response = supabase.rpc(
        "get_reservations_by_phone", {"phone_number": phone}
    ).execute()
    # ret = json.loads(response.data)
    # return ret
    return response.data


def update_reservation_date(reservation_uuid: str, new_date: str):
    supabase: Client = get_supabase_client()
    response = supabase.rpc(
        "update_reservation_date",
        {"reservation_uuid": reservation_uuid, "new_reservation_date": new_date},
    ).execute()
    return "reservation successfully updated"


def cancel_reservation(reservation_uuid: str) -> dict:
    supabase: Client = get_supabase_client()
    response = supabase.rpc(
        "cancel_reservation", {"reservation_uuid": reservation_uuid}
    ).execute()
    return "reservation successfully cancelled"


def get_service_by_breed_and_weight(breed_type: int, weight_range: int):
    response = supabase.rpc(
        "get_services_by_breed_and_weight",
        {"breed_type_id": breed_type, "weight_range_id": weight_range},
    ).execute()
    return response


def create_reservation(
    reservation_info,
):
    response = supabase.rpc(
        "create_reservation",
        {
            "pet_id": reservation_info.pet_id,
            "status": reservation_info.status,
            "service_name": reservation_info.service_name,
            "weight": reservation_info.weight,
            "reservation_date": reservation_info.reservation_date,
            "price": reservation_info.price,
            "phone": reservation_info.phone,
        },
    ).execute()
    return response

# RPC
def get_reservations_by_phone(phone: str) -> dict:
    response = supabase.rpc(
        "get_reservations_by_phone", {"phone_number": phone}
    ).execute()
    # ret = json.loads(response.data)
    # return ret
    return response.data


def update_reservation_date(reservation_uuid: str, new_date: str):
    response = supabase.rpc(
        "update_reservation_date",
        {"reservation_uuid": reservation_uuid, "new_reservation_date": new_date},
    ).execute()
    return "reservation successfully updated"


def cancel_reservation(reservation_uuid: str) -> dict:
    response = supabase.rpc(
        "cancel_reservation", {"reservation_uuid": reservation_uuid}
    ).execute()
    return "reservation successfully cancelled"

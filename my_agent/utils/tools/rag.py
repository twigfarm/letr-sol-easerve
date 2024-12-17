from pydantic import BaseModel, Field
from typing import Optional

class Reservation(BaseModel):
    """Information about a reservation.
    ^ Doc-string for the entity Reservation
    This doc-string is sent to the LLM as the description of the schema Reservation,
    and it can help to improve extraction results.

    Note that:
    1. Each field is an `optional` except for `reservation_date`, `price` which is required.
       Optional fields allow the model to decline to extract their values if not provided.
    2. Providing detailed descriptions for each field can help improve the accuracy of extraction results.
"""
    pet_id: Optional[str] = Field(default=None, description="The ID of the pet")
    status: Optional[str] = Field(default="예약대기", description="The status of the reservation")
    service_name: Optional[str] = Field(description="The name of the service")
    weight: Optional[float] = Field(description="The weight of the pet")
    reservation_date: Optional[str] = Field(description="The date of the reservation, must have a value")
    price: Optional[int] = Field(description="The price of the service")

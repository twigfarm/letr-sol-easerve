from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool, Tool
from .tools_prompt import (
    pet_prompt_template,
    reservation_prompt_template,
    grade_weight_range_chain,
    weight_dictionary,
)
from langchain_openai import ChatOpenAI
from ..rpc import get_service_by_breed_and_weight, create_reservation
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from langgraph.prebuilt import ToolNode
from my_agent.utils.grade_doc import retrieval_grader
from my_agent.utils.vector_db import breeds_database
from langchain_core.runnables.config import RunnableConfig

llm = ChatOpenAI(model="gpt-4o-mini")


class Pet(BaseModel):
    """Information about a pet.
    ^ Doc-string for the entity Pet
    This doc-string is sent to the LLM as the description of the schema Pet,
    and it can help to improve extraction results.

    Note that:
    1. Each field is an `optional` -- this allows the model to decline to extract it!
    2. `weight` and `breedType` are required fields and must be provided during validation.
    3. Each field has a `description` -- this description is used by the LLM.
    Having a good description can help improve extraction results.
    """

    name: Optional[str] = Field(description="The name of the pet")
    breed_type: Optional[str] = Field(description="The type of the breed")
    breed: Optional[str] = Field(description="The breed of the pet")
    weight: Optional[float] = Field(description="The weight of the pet")
    age: Optional[int] = Field(description="The age of the pet")


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
    status: Optional[str] = Field(
        default="예약대기", description="The status of the reservation, must have a value"
    )
    service_name: Optional[str] = Field(description="The name of the service, must have a value")
    weight: Optional[float] = Field(description="The weight of the pet")
    reservation_date: Optional[str] = Field(
        description="The date of the reservation, must have a value"
    )
    price: Optional[int] = Field(description="The price of the service, must have a value")
    phone: Optional[str] = Field(description="The phone number of the customer, must have a value")


structured_pet_llm = llm.with_structured_output(schema=Pet)
structured_reservation_llm = llm.with_structured_output(schema=Reservation)
fill_pet_info_runnable = pet_prompt_template | structured_pet_llm
fill_reservation_info_runnable = (
    reservation_prompt_template | structured_reservation_llm
)


# 주어진 강아지 정보로부터 breed type을 채워넣는 함수
def fill_breed_type(query: str, retrieved_docs) -> Pet:
    extracted_pet: Pet = fill_pet_info_runnable.invoke({"query": query})
    breed_type_info = None
    for doc in retrieved_docs:
        # 각 문서의 page_content에서 name과 type을 파싱
        lines = doc.page_content.split("\n")
        name_line = next((line for line in lines if line.startswith("name:")), None)
        type_line = next((line for line in lines if line.startswith("type:")), None)
        breed = name_line.split(":")[-1].strip()  # name 값 추출
        breed_type_info = type_line.split(":")[-1].strip()  # type 값 추출
    if breed:
        extracted_pet.breed = breed
    if breed_type_info:
        extracted_pet.breed_type = breed_type_info
    return extracted_pet


def fill_reservation_info(query: str) -> Reservation:
    return fill_reservation_info_runnable.invoke({"query": query})


@tool
def get_service_menu(query: str):
    """
    Retrieves the available services based on the provided query describing the pet.

    Steps:
    1. Extracts pet information such as breed type, weight, and other attributes.
    2. Maps the weight to the appropriate weight range using the weight dictionary.
    3. Fetches the services available for the given breed type and weight range from the database.

    Note:
        - This tool must be used to select services when making a grooming reservation for your pet.
        - Without using this tool, it is not possible to proceed with a grooming reservation as it ensures
          accurate matching of services based on the pet's breed type and weight range.
    """
    documents = breeds_database.similarity_search(query, k=1)
    grade_result = retrieval_grader.invoke(
        {"document": documents[0].page_content, "question": query}
    )
    if grade_result.binary_score == "no":
        return "강아지 품종명을 정확하게 알려주세요. 예: '포메라니안, 5kg'"
    pet_info: Pet = fill_breed_type(query, documents)
    weight_range = grade_weight_range_chain.invoke(
        {"pet_info": pet_info, "weight_dictionary": weight_dictionary}
    )
    if pet_info.breed_type != "4":
        return get_service_by_breed_and_weight(int(pet_info.breed_type), weight_range)
    else:
        service_data = get_service_by_breed_and_weight(
            3, weight_range
        )  # 일단 3으로 설정하고 다시 세팅, DB에 데이터가 없음
        price_per_kg = {
            "위생미용+목욕": 7000,
            "클리핑": 10000,
            "스포팅": 13000,
            "가위컷": 20000,
            "위생미용": 5000,
        }
        for service in service_data.data:
            service_name = service["service_name"]
            if service_name in price_per_kg:
                service["price"] = price_per_kg[service_name] * int(pet_info.weight)
    return service_data


@tool
def make_reservation(
    query: str,
    config: RunnableConfig,
):
    """
    Creates a reservation for a pet grooming service.

    Steps:
    1. Extracts the reservation information, and reservation date.
    1. Creates a reservation for the provided pet with the specified service
    2. Returns the reservation details.

    Note:
        - This tool must be used to create a grooming reservation for your pet after selecting the services using the `get_service_menu` tool.
        - Without using this tool, it is not possible to proceed with a grooming reservation.
        - Ensure to include both **date** and **time** in the reservation query to successfully schedule the grooming service.
        - The **price** of the selected service must be included and stored when creating the reservation.
    """
    reservation_info: Reservation = fill_reservation_info(query)
    response = create_reservation(reservation_info=reservation_info, phone=config["configurable"]["phone_number"])
    return response


# using co-star
add_reservation_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are assisting users in creating dog grooming reservations easily and quickly. You assist users in booking grooming appointments for their dogs by gathering necessary information.
            First, collect the dog’s breed and weight to determine the suitable grooming options using the provided tool(get_service_menu).
            if user already input what type of grooming service pass the show options and final check of price
            Then, display the available grooming options along with their prices. Finally, guide users to select a grooming service and their preferred date, and proceed to complete the reservation.
            If the user provides all the necessary inputs, confirm the final price once more before proceeding.
            Guide users through the reservation process in clear, simple steps while making it easy to understand.
            Concise and friendly conversational style.
            Kind and professional tone.
            Dog owners, including those who are new to making grooming reservations.
            Provide questions in 2-3 sentences per step, wait for the user's input, and proceed to the next step based on their responses. Include examples to make it easier for the user.
            If the selected date is earlier than today, adjust it to the same date in the next year.
            """
            "\nCurrent time: {time}.",
        ),
        ("human", "{messages}"),
    ]
).partial(time=datetime.now)

rag_safe_tools = [get_service_menu]
rag_sensitive_tools = [make_reservation]
rag_sensitive_tool_names = {t.name for t in rag_sensitive_tools}
rag_tools: list[Tool] = rag_safe_tools + rag_sensitive_tools
llm_with_reservation_rag = llm.bind_tools(rag_tools)
rag_runnable = add_reservation_assistant_prompt | llm_with_reservation_rag

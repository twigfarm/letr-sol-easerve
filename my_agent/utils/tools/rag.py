from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool
from langchain_community.document_loaders.csv_loader import CSVLoader
from dotenv import load_dotenv
import os
from langchain_upstage import UpstageEmbeddings
from supabase import create_client, Client
from langchain_pinecone import PineconeVectorStore
from .tools_prompt import pet_prompt_template, reservation_prompt_template, pet_info_chain, weight_dictionary
from langchain_openai import ChatOpenAI
from ..rpc import get_service_by_breed_and_weight, create_reservation
from langgraph.prebuilt import ToolNode, tools_condition

llm = ChatOpenAI(model="gpt-4o-mini")
breeds_file_path = "csv/breeds.csv"
breeds_loader = CSVLoader(breeds_file_path)
breeds_data = breeds_loader.load()

# 임베딩
load_dotenv()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
embedding = UpstageEmbeddings(
    api_key=UPSTAGE_API_KEY,
    model="embedding-query"
)

# 벡터 스토어 불러오기
breeds_database_index = "breeds"
breeds_database = PineconeVectorStore(index_name=breeds_database_index, embedding=embedding)

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
    breedType: Optional[str] = Field(description="The type of the breed")
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
    pet_id: Optional[str] = Field(default=None, description="The ID of the pet")
    status: Optional[str] = Field(default="예약대기", description="The status of the reservation")
    service_name: Optional[str] = Field(description="The name of the service")
    weight: Optional[float] = Field(description="The weight of the pet")
    reservation_date: Optional[str] = Field(description="The date of the reservation, must have a value")
    price: Optional[int] = Field(description="The price of the service")

structured_pet_llm = llm.with_structured_output(schema=Pet)
structured_reservation_llm = llm.with_structured_output(schema=Reservation)

# 주어진 강아지 정보로부터 breed type을 채워넣는 함수
def fill_breed_type(query: str, retrieved_docs):
    prompt = pet_prompt_template.invoke({"query": query})
    extracted_pet: Pet = structured_pet_llm.invoke(prompt)
    breed_type_info = None
    for doc in retrieved_docs:
        # 각 문서의 page_content에서 name과 type을 파싱
        lines = doc.page_content.split('\n')
        name_line = next((line for line in lines if line.startswith("name:")), None)
        type_line = next((line for line in lines if line.startswith("type:")), None)
        breed = name_line.split(":")[-1].strip()  # name 값 추출
        breed_type_info = type_line.split(":")[-1].strip()  # type 값 추출
    if breed:
        extracted_pet.breed = breed
    if breed_type_info:
        extracted_pet.breedType = breed_type_info
    return extracted_pet

def fill_reservation_info(query: str) -> Reservation:
    prompt = reservation_prompt_template.invoke({"query": query})
    extracted_reservation: Reservation = structured_reservation_llm.invoke(prompt)
    return extracted_reservation

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
    # Step 1: Pet 정보 추출
    retrieved_docs = breeds_database.similarity_search(query, k=1)
    extracted_pet = fill_breed_type(query, retrieved_docs)
    weight = int(extracted_pet.weight) if extracted_pet.weight else 1
    weight_range = pet_info_chain.invoke({"pet_info": extracted_pet, "weight_dictionary": weight_dictionary})
    weight_range = int(weight_range) if weight_range else 1
    breed_type = int(extracted_pet.breedType) if extracted_pet.breedType else 1
    print(f"weight: {weight}, weight_range: {weight_range}, breed_type: {breed_type}")
    if breed_type != 4:
        service_data = get_service_by_breed_and_weight(breed_type, weight_range)
    else:
        service_data = get_service_by_breed_and_weight(3, weight_range) #일단 3으로 설정하고 다시 세팅, DB에 데이터가 없음
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
                service["price"] = price_per_kg[service_name] * weight
    return service_data

@tool
def make_reservation(
    query: str,
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
    """
    reservation_info: Reservation = fill_reservation_info(query)
    print(f"reservation_info: {reservation_info}")
    response = create_reservation(
       reservation_info=reservation_info
    )
    return response

tools = [get_service_menu, make_reservation]
llm_with_reservation_rag = llm.bind_tools(tools)
rag_assistant_tool_node = ToolNode(tools=tools)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Define a custom prompt to provide instructions and any additional context.
# 1) You can add examples into the prompt template to improve extraction quality
# 2) Introduce additional parameters to take context into account (e.g., include metadata
#    about the document from which the text was extracted.)


pet_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm. "
            "Only extract relevant information from the text. "
            "If you do not know the value of an attribute asked to extract, "
            "return null for the attribute's value.",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{query}"),
    ]
)

reservation_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm. "
            "Only extract reservation information from the text. "
            "If you do not know the value of an attribute asked to extract, "
            "return null for the attribute's value.",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{query}"),
    ]
)

weight_dictionary = [
	"4kg 이하 -> weight_range=1",
	"4kg 이상 6kg 이하 -> weight_range=2",
	"6kg 이상 8kg 이하 -> weight_range=3",
	"8kg 이상 10kg 이하 -> weight_range=4"
]

service_prompt = ChatPromptTemplate.from_template("""
    you are an expert in pet services.
    you can help you find the price of a service for your pet.
    주어지는 petInfo를 적극 활용해주세요.
    [pet_info]
    {pet_info}
    [weight_dictionary]
    {weight_dictionary}
    다음과 같은 요구사항이 있습니다
    1. weight_dictionary를 참고해서 weight를 weight_range로 바꿔주세요
    2. 다른 설명은 하지 마시고, weight_range의 숫자만 출력해주세요
    ex) weight_range=1 이라면 1만
""")

llm = ChatOpenAI(model="gpt-4o-mini")
pet_info_chain = service_prompt | llm | StrOutputParser()


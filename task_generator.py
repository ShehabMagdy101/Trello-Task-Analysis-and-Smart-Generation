from dotenv import dotenv_values
env_values = dotenv_values("./app.env")
api_key = env_values["GOOGLE_API_KEY"]

from config import settings
from prompt import system_prompt, user_prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from output_format import parser

llm = ChatGoogleGenerativeAI(
    model=settings.MODEL,
    google_api_key=api_key,
    temperature=0.7,
)

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt.prompt_text + "\n\n{format_instructions}"),
    ("user", user_prompt.prompt_text)
])



parser = parser

chain = chat_prompt | llm | parser

def generate_daily_tasks(csv_data, user_notes: str = "None", user_goals: str = "None", analytics_summary: str = "None" , include_reasoning:bool = False):
    response =  chain.invoke({
        "csv_data": csv_data,
        "user_notes": user_notes,
        "user_goals": user_goals,
        "analytics_summary": analytics_summary,
        "include_reasoning": "Yes, provide detailed reasoning" if include_reasoning else "No, skip reasoning",
        "format_instructions": parser.get_format_instructions()
        })
    return response

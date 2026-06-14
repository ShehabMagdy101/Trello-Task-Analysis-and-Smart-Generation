from dotenv import dotenv_values
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser

from src.core.config import settings
from src.application.task_generation.prompts import system_prompt, user_prompt
from src.domain.models.task_generation import DailyTaskPlan

# Try to find app.env in the project root
ROOT_DIR = Path(__file__).parent.parent.parent.parent
env_path = ROOT_DIR / "app.env"
env_values = dotenv_values(str(env_path) if env_path.exists() else "./app.env")
api_key = env_values.get("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model=settings.MODEL,
    google_api_key=api_key,
    temperature=0.7,
)

parser = JsonOutputParser(pydantic_object=DailyTaskPlan)

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt.prompt_text + "\n\n{format_instructions}"),
    ("user", user_prompt.prompt_text)
])

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

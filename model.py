from dotenv import dotenv_values
env_values = dotenv_values("./app.env")
api_key = env_values["GOOGLE_API_KEY"]

from config import settings
from prompt import system_prompt, user_prompt


from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model=settings.MODEL,
    google_api_key=api_key,
    temperature=0.7,
)

from langchain_core.prompts import ChatPromptTemplate

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt.prompt_text + "\n\n{format_instructions}"),
    ("user", user_prompt.prompt_text)
])


from output_format import parser
parser = parser

chain = chat_prompt | llm | parser

def generate_daily_tasks(csv_data, user_notes: str = "None", include_reasoning:bool = False):
    response =  chain.invoke({
        "csv_data": csv_data,
        "user_notes": user_notes,
        "include_reasoning": "Yes, provide detailed reasoning" if include_reasoning else "No, skip reasoning",
        "format_instructions": parser.get_format_instructions()
        })
    return response


# Example usage
csv_data = """list,card,card_due
Marketing,Q4 Report,2024-01-15
Development,Fix login bug,2024-01-14
Marketing,Social media posts,2024-01-16
Development,Update documentation,2024-01-20
Sales,Follow up with leads,2024-01-14"""

user_notes = "Focus on Marketing list today. Need to finish the Q4 report. Low energy day."

result = generate_daily_tasks(csv_data, user_notes, include_reasoning=False)
result['tasks']
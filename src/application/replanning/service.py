from datetime import date
from pathlib import Path
from dotenv import dotenv_values
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser

from src.application.replanning.prompts import replanner_system_prompt, replanner_user_prompt
from src.domain.models.replanning import ReplanResult

# Try to find app.env in the project root
ROOT_DIR = Path(__file__).parent.parent.parent.parent
env_path = ROOT_DIR / "app.env"
env_values = dotenv_values(str(env_path) if env_path.exists() else "./app.env")

replanner_parser = JsonOutputParser(pydantic_object=ReplanResult)

def _build_llm(provider: str):
    provider = provider.lower().strip()

    if provider == "gemini":
        api_key = env_values.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing GOOGLE_API_KEY in app.env")

        return ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=api_key,
            temperature=0.2,
        )

    if provider == "mistral":
        api_key = env_values.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("Missing MISTRAL_API_KEY in app.env")

        try:
            from langchain_mistralai import ChatMistralAI
        except ImportError as exc:
            raise ImportError(
                "langchain_mistralai is required for Mistral provider. "
                "Install it with: pip install langchain-mistralai"
            ) from exc

        return ChatMistralAI(
            model="mistral-small-latest",
            api_key=api_key,
            temperature=0.2,
        )

    raise ValueError("Unsupported provider. Use 'gemini' or 'mistral'.")


def generate_replan_dataset(csv_data: str, user_instruction: str, provider: str = "gemini"):
    llm = _build_llm(provider)
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                replanner_system_prompt.prompt_text + "\n\n{format_instructions}",
            ),
            ("user", replanner_user_prompt.prompt_text),
        ]
    )

    chain = chat_prompt | llm | replanner_parser

    return chain.invoke(
        {
            "today_date": str(date.today()),
            "csv_data": csv_data,
            "user_instruction": user_instruction,
            "format_instructions": replanner_parser.get_format_instructions(),
        }
    )

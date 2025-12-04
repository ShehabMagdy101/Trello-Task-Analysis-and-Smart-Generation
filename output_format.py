from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class Task(BaseModel):
    list: str = Field(description="The Trello list/category")
    card: str = Field(description="Task name/description")
    priority: str = Field(description="Priority level: high, medium, or low")
    order: int = Field(description="Suggested order of execution (1, 2, 3...)")
    reason: str = Field(description="Why this task is prioritized for today")

class DailyTaskPlan(BaseModel):
    tasks: list[Task] = Field(description="List of recommended tasks for today")
    reasoning: str | None = Field(default=None, description="Overall reasoning for the task selection (optional)")

parser = JsonOutputParser(pydantic_object=DailyTaskPlan)   
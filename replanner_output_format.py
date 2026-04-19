from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


class ReplannedTask(BaseModel):
    card_id: str = Field(description="Exact Trello card ID")
    card: str = Field(description="Task name")
    list: str = Field(description="Trello list/category")
    current_due: str | None = Field(description="Current due date ISO string or null")
    new_due: str | None = Field(
        description="New due date in YYYY-MM-DD format. Keep null if no change needed."
    )
    reason: str = Field(description="Why this due-date change is suggested")


class ReplanResult(BaseModel):
    summary: str = Field(description="Short summary of the replanning strategy")
    tasks_to_update: list[ReplannedTask] = Field(
        description="Dataset of tasks selected for due-date updates"
    )


replanner_parser = JsonOutputParser(pydantic_object=ReplanResult)

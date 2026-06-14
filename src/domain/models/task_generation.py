from pydantic import BaseModel, Field

class GeneratedTask(BaseModel):
    list: str = Field(description="The Trello list/category")
    card: str = Field(description="Task name/description")
    priority: str = Field(description="Priority level: high, medium, or low")
    order: int = Field(description="Suggested order of execution (1, 2, 3...)")
    reason: str = Field(description="Why this task is prioritized for today")
    goal: str = Field(description="Task goal alignment with user predefined goals")

class DailyTaskPlan(BaseModel):
    tasks: list[GeneratedTask] = Field(description="List of recommended tasks for today")
    reasoning: str | None = Field(default=None, description="Overall reasoning for the task selection (optional)")

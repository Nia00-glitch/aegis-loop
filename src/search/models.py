from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str
    purpose: str
    priority: int = Field(ge=1, le=3)


class SearchPlan(BaseModel):
    task_id: str
    category: str
    queries: list[SearchQuery]

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ResearchRequest(BaseModel):
    query: str = Field(min_length=10)
    objective: str = Field(min_length=3)

    geography: str = "Global"
    industry: str = "General"
    time_period: str = "Current"

    max_iterations: int = Field(default=5, ge=1, le=20)
    time_budget_minutes: int = Field(default=30, ge=1, le=1440)

    evidence_required: bool = True
    include_competitors: bool = True
    include_customer_pain: bool = True

    @field_validator(
        "query",
        "objective",
        "geography",
        "industry",
        "time_period",
    )
    @classmethod
    def cannot_be_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be blank")

        return value


def validate_research_request(
    data: dict,
) -> ResearchRequest:
    return ResearchRequest(**data)

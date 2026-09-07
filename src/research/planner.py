from pydantic import BaseModel, Field

from src.core.gatekeeper import ResearchRequest


class ResearchTask(BaseModel):
    id: str
    title: str
    question: str
    category: str
    priority: int = Field(ge=1, le=3)


class ResearchPlan(BaseModel):
    query: str
    objective: str
    tasks: list[ResearchTask]


DEFAULT_DIMENSIONS = [
    (
        "market",
        "Market Overview",
        "What is the size, growth, structure, and current state of the market?",
    ),
    (
        "competitors",
        "Competitor Analysis",
        "Who are the major competitors and what capabilities do they offer?",
    ),
    (
        "customers",
        "Customer Analysis",
        "Who are the target customers and what problems or unmet needs do they have?",
    ),
    (
        "trends",
        "Market Trends",
        "What major trends are shaping this market?",
    ),
    (
        "opportunities",
        "Opportunity Analysis",
        "What evidence-backed product or market opportunities exist?",
    ),
    (
        "risks",
        "Risk Analysis",
        "What risks, barriers, or uncertainties could affect this market?",
    ),
]


def create_research_plan(
    request: ResearchRequest,
) -> ResearchPlan:
    tasks = []

    for index, (
        category,
        title,
        question,
    ) in enumerate(DEFAULT_DIMENSIONS, start=1):

        if category == "competitors" and not request.include_competitors:
            continue

        if category == "customers" and not request.include_customer_pain:
            continue

        tasks.append(
            ResearchTask(
                id=f"task-{index:02d}",
                title=title,
                question=question,
                category=category,
                priority=1 if category in {"market", "competitors"} else 2,
            )
        )

    return ResearchPlan(
        query=request.query,
        objective=request.objective,
        tasks=tasks,
    )

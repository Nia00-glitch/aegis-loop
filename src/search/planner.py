from src.research.planner import ResearchTask
from src.search.models import SearchPlan, SearchQuery


CATEGORY_TEMPLATES = {
    "market": [
        "{query} market size growth",
        "{query} market trends {time_period}",
        "{query} market report industry analysis",
    ],
    "competitors": [
        "{query} competitors companies",
        "{query} alternatives comparison",
        "{query} leading companies market share",
    ],
    "customers": [
        "{query} customer problems pain points",
        "{query} user complaints unmet needs",
        "{query} customer needs challenges",
    ],
    "trends": [
        "{query} latest trends",
        "{query} emerging trends innovation",
        "{query} future outlook",
    ],
    "opportunities": [
        "{query} market gaps opportunities",
        "{query} unmet customer needs",
        "{query} underserved market opportunities",
    ],
    "risks": [
        "{query} market risks challenges",
        "{query} barriers regulation",
        "{query} industry threats",
    ],
}


def create_search_plan(
    task: ResearchTask,
    research_query: str,
    time_period: str = "current",
) -> SearchPlan:

    templates = CATEGORY_TEMPLATES.get(
        task.category,
        [
            "{query} research",
            "{query} analysis",
            "{query} latest information",
        ],
    )

    queries = []

    for index, template in enumerate(
        templates,
        start=1,
    ):
        query = template.format(
            query=research_query,
            time_period=time_period,
        )

        queries.append(
            SearchQuery(
                query=query,
                purpose=task.category,
                priority=1 if index == 1 else 2,
            )
        )

    return SearchPlan(
        task_id=task.id,
        category=task.category,
        queries=queries,
    )

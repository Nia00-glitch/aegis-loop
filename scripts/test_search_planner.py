from src.core.gatekeeper import validate_research_request
from src.research.planner import create_research_plan
from src.search.planner import create_search_plan


def main():
    request = validate_research_request(
        {
            "query": (
                "Analyze the global AI market and identify "
                "evidence-backed product opportunities."
            ),
            "objective": "Find product opportunities",
            "time_period": "2025-2026",
        }
    )

    research_plan = create_research_plan(request)

    task = research_plan.tasks[0]

    search_plan = create_search_plan(
        task=task,
        research_query=request.query,
        time_period=request.time_period,
    )

    print("ADAPTIVE SEARCH CHECK")
    print("=" * 50)
    print(f"Task: {task.category}")
    print()

    for query in search_plan.queries:
        print(
            f"P{query.priority} ? {query.query}"
        )

    if len(search_plan.queries) < 3:
        raise RuntimeError(
            "Insufficient search diversification"
        )

    print("=" * 50)
    print("ADAPTIVE SEARCH: PASSED")


if __name__ == "__main__":
    main()

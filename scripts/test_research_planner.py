from src.core.gatekeeper import validate_research_request
from src.research.planner import create_research_plan


def main():
    request = validate_research_request(
        {
            "query": (
                "Analyze the global AI market and identify "
                "major product opportunities."
            ),
            "objective": "Find evidence-backed opportunities",
            "geography": "Global",
            "industry": "Artificial Intelligence",
            "time_period": "2025-2026",
        }
    )

    plan = create_research_plan(request)

    print("RESEARCH PLANNER CHECK")
    print("=" * 50)
    print(f"Tasks created: {len(plan.tasks)}")
    print()

    for task in plan.tasks:
        print(
            f"[{task.id}] "
            f"{task.category.upper()} "
            f"P{task.priority}"
        )
        print(f"  {task.question}")

    print("=" * 50)

    if len(plan.tasks) < 5:
        raise RuntimeError("Too few research tasks generated")

    print("RESEARCH PLANNER: PASSED")


if __name__ == "__main__":
    main()

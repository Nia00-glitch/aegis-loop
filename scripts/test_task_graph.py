from src.core.gatekeeper import validate_research_request
from src.research.planner import create_research_plan
from src.research.task_graph import (
    create_task_graph,
    mark_completed,
)


def show_ready(graph, label):
    ready = graph.ready_tasks()

    print()
    print(label)

    for node in ready:
        print(
            f"READY ? {node.task.id} | "
            f"{node.task.category}"
        )

    return ready


def main():
    request = validate_research_request(
        {
            "query": (
                "Analyze the global AI market and identify "
                "evidence-backed product opportunities."
            ),
            "objective": "Find product opportunities",
        }
    )

    plan = create_research_plan(request)
    graph = create_task_graph(plan)

    print("TASK GRAPH CHECK")
    print("=" * 50)

    initial_ready = show_ready(
        graph,
        "INITIAL READY TASKS:",
    )

    if not initial_ready:
        raise RuntimeError("No initial tasks are ready")

    # Complete independent tasks
    for task_id in [
        "task-01",
        "task-02",
        "task-03",
    ]:
        if task_id in graph.nodes:
            mark_completed(graph, task_id)

    ready_after_completion = show_ready(
        graph,
        "READY AFTER CORE RESEARCH:",
    )

    categories = {
        node.task.category
        for node in ready_after_completion
    }

    if "opportunities" not in categories:
        raise RuntimeError(
            "Opportunity task did not unlock"
        )

    print()
    print("=" * 50)
    print("RESEARCH TASK GRAPH: PASSED")


if __name__ == "__main__":
    main()

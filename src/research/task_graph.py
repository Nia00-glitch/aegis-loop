from collections import defaultdict
from pydantic import BaseModel

from src.research.planner import ResearchPlan, ResearchTask


class TaskNode(BaseModel):
    task: ResearchTask
    depends_on: list[str] = []
    status: str = "pending"


class ResearchTaskGraph(BaseModel):
    nodes: dict[str, TaskNode]

    def ready_tasks(self) -> list[TaskNode]:
        return [
            node
            for node in self.nodes.values()
            if node.status == "pending"
            and all(
                self.nodes[dependency].status == "completed"
                for dependency in node.depends_on
            )
        ]


DEPENDENCIES = {
    "market": [],
    "competitors": [],
    "customers": [],
    "trends": ["task-01"],
    "opportunities": [
        "task-01",
        "task-02",
        "task-03",
    ],
    "risks": ["task-01"],
}


def create_task_graph(
    plan: ResearchPlan,
) -> ResearchTaskGraph:
    nodes = {}

    for task in plan.tasks:
        dependencies = DEPENDENCIES.get(task.category, [])

        # Keep only dependencies that actually exist
        dependencies = [
            dependency
            for dependency in dependencies
            if dependency in {
                existing_task.id
                for existing_task in plan.tasks
            }
        ]

        nodes[task.id] = TaskNode(
            task=task,
            depends_on=dependencies,
        )

    return ResearchTaskGraph(nodes=nodes)


def mark_completed(
    graph: ResearchTaskGraph,
    task_id: str,
) -> None:
    if task_id not in graph.nodes:
        raise ValueError(f"Unknown task: {task_id}")

    graph.nodes[task_id].status = "completed"

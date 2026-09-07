from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


class ResearchState(TypedDict):
    query: str
    iteration: int
    max_iterations: int
    status: str
    history: list[str]


def plan(state: ResearchState):
    print("? PLAN")
    return {
        "status": "planned",
        "history": state["history"] + ["PLAN"],
    }


def execute(state: ResearchState):
    print("? EXECUTE")
    return {
        "status": "executed",
        "history": state["history"] + ["EXECUTE"],
    }


def verify(state: ResearchState):
    print("? VERIFY")
    return {
        "status": "verified",
        "history": state["history"] + ["VERIFY"],
    }


def critique(state: ResearchState):
    print("? CRITIQUE")
    return {
        "status": "critiqued",
        "history": state["history"] + ["CRITIQUE"],
    }


def repair(state: ResearchState):
    print("? REPAIR")
    return {
        "iteration": state["iteration"] + 1,
        "status": "repaired",
        "history": state["history"] + ["REPAIR"],
    }


def evaluate(state: ResearchState):
    print("? EVALUATE")
    return {
        "status": "evaluated",
        "history": state["history"] + ["EVALUATE"],
    }


def should_continue(
    state: ResearchState,
) -> Literal["plan", "finish"]:
    if state["iteration"] < state["max_iterations"]:
        print(f"? LOOP AGAIN ({state['iteration']}/{state['max_iterations']})")
        return "plan"

    print("? STOP")
    return "finish"


def build_master_loop():
    graph = StateGraph(ResearchState)

    graph.add_node("plan", plan)
    graph.add_node("execute", execute)
    graph.add_node("verify", verify)
    graph.add_node("critique", critique)
    graph.add_node("repair", repair)
    graph.add_node("evaluate", evaluate)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "verify")
    graph.add_edge("verify", "critique")
    graph.add_edge("critique", "repair")
    graph.add_edge("repair", "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "plan": "plan",
            "finish": END,
        },
    )

    return graph.compile()

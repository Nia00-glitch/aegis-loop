from src.loops.master_loop import build_master_loop


def main():
    graph = build_master_loop()

    result = graph.invoke(
        {
            "query": "Test the Market Intelligence OS loop",
            "iteration": 1,
            "max_iterations": 3,
            "status": "started",
            "history": [],
        }
    )

    print()
    print("=" * 50)
    print("MASTER LOOP: PASSED")
    print(f"Final iteration: {result['iteration']}")
    print(f"History: {' ? '.join(result['history'])}")


if __name__ == "__main__":
    main()

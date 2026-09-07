from pydantic import ValidationError

from src.core.gatekeeper import validate_research_request


def test_valid_request():
    request = validate_research_request(
        {
            "query": (
                "Analyze the global AI market "
                "and identify major competitors."
            ),
            "objective": "Find product opportunities",
            "geography": "Global",
            "industry": "Artificial Intelligence",
            "time_period": "2025-2026",
            "max_iterations": 5,
            "time_budget_minutes": 30,
        }
    )

    print("VALID REQUEST: PASS")
    print(f"Query: {request.query}")
    print(f"Objective: {request.objective}")
    print(f"Geography: {request.geography}")
    print(f"Industry: {request.industry}")


def test_invalid_request():
    try:
        validate_research_request(
            {
                "query": "",
                "objective": "Test",
            }
        )

    except ValidationError:
        print("INVALID REQUEST BLOCKED: PASS")
        return

    raise RuntimeError(
        "Gatekeeper failed to block invalid request"
    )


def main():
    print("RESEARCH GATEKEEPER CHECK")
    print("=" * 40)

    test_valid_request()

    print("-" * 40)

    test_invalid_request()

    print("=" * 40)
    print("RESEARCH GATEKEEPER: PASSED")


if __name__ == "__main__":
    main()

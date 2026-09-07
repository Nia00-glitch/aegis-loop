import json
import requests


ALLOWED_TYPES = {
    "FACT",
    "METRIC",
    "FEATURE",
    "MARKET",
    "COMPETITIVE",
}


TEST_CASES = [
    {
        "name": "basic_market_facts",
        "text": (
            "The company launched a new analytics platform in 2025. "
            "The platform costs $20 per month. "
            "The company has 10 million users worldwide. "
            "The global analytics market is growing rapidly."
        ),
        "expected_claims": 4,
    },
    {
        "name": "funding_facts",
        "text": (
            "The startup raised $15 million in Series A funding. "
            "The round was led by Example Ventures. "
            "The company operates in India."
        ),
        "expected_claims": 3,
    },
    {
        "name": "product_features",
        "text": (
            "The platform supports automated reporting. "
            "It includes competitor monitoring. "
            "It provides API access."
        ),
        "expected_claims": 3,
    },
]


def run_model(text: str) -> dict:
    prompt = f"""
Extract atomic factual claims from the text below.

Return ONLY valid JSON in exactly this structure:

{{
  "claims": [
    {{
      "text": "claim text",
      "type": "FACT"
    }}
  ]
}}

Rules:
- Extract every independent factual claim.
- Do not invent information.
- Do not rewrite facts with new information.
- Preserve numbers exactly.
- Allowed types:
  FACT, METRIC, FEATURE, MARKET, COMPETITIVE
- Do not return any fields other than "claims".

TEXT:
{text}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "deepseek-coder:latest",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
            },
        },
        timeout=120,
    )

    response.raise_for_status()

    return json.loads(
        response.json()["response"]
    )


def validate_result(
    result: dict,
    expected_claims: int,
) -> dict:

    score = 0
    max_score = 5
    reasons = []

    if isinstance(result, dict):
        score += 1
    else:
        reasons.append("Root JSON is not an object")
        return {
            "score": score,
            "max_score": max_score,
            "reasons": reasons,
        }

    claims = result.get("claims")

    if isinstance(claims, list):
        score += 1
    else:
        reasons.append("Missing or invalid claims array")
        return {
            "score": score,
            "max_score": max_score,
            "reasons": reasons,
        }

    valid_claims = True

    for claim in claims:
        if not isinstance(claim, dict):
            valid_claims = False
            reasons.append("Claim is not an object")
            continue

        if not claim.get("text"):
            valid_claims = False
            reasons.append("Claim text missing")

        if claim.get("type") not in ALLOWED_TYPES:
            valid_claims = False
            reasons.append(
                f"Invalid/missing type: {claim.get('type')}"
            )

    if valid_claims:
        score += 1

    if len(claims) == expected_claims:
        score += 1
    else:
        reasons.append(
            f"Expected {expected_claims} claims, "
            f"got {len(claims)}"
        )

    allowed_keys = {"text", "type"}

    extra_fields = set()

    for claim in claims:
        if isinstance(claim, dict):
            extra_fields.update(
                set(claim.keys()) - allowed_keys
            )

    if not extra_fields and set(result.keys()) == {"claims"}:
        score += 1
    else:
        reasons.append(
            f"Extra fields detected: {sorted(extra_fields)}"
        )

    return {
        "score": score,
        "max_score": max_score,
        "reasons": reasons,
        "claim_count": len(claims),
    }


def main():
    print("SEMANTIC EXTRACTION BENCHMARK")
    print("=" * 70)

    total_score = 0
    total_max = 0

    for case in TEST_CASES:
        print(f"\nCASE: {case['name']}")
        print("-" * 70)

        try:
            result = run_model(case["text"])
            validation = validate_result(
                result,
                case["expected_claims"],
            )

            total_score += validation["score"]
            total_max += validation["max_score"]

            print(
                f"Score: "
                f"{validation['score']}/"
                f"{validation['max_score']}"
            )

            print(
                f"Claims returned: "
                f"{validation.get('claim_count', 0)}"
            )

            if validation["reasons"]:
                print("Problems:")
                for reason in validation["reasons"]:
                    print(f"  - {reason}")
            else:
                print("Case: PASS")

        except Exception as exc:
            total_max += 5
            print(f"Case ERROR: {exc}")

    print("\n" + "=" * 70)

    percentage = (
        (total_score / total_max) * 100
        if total_max
        else 0
    )

    print(
        f"TOTAL SCORE: "
        f"{total_score}/{total_max}"
    )
    print(
        f"QUALITY SCORE: "
        f"{percentage:.1f}%"
    )

    if percentage >= 90:
        print("MODEL QUALITY: STRONG")
    elif percentage >= 70:
        print("MODEL QUALITY: USABLE WITH GUARDRAILS")
    else:
        print("MODEL QUALITY: REJECT FOR SEMANTIC ROLE")


if __name__ == "__main__":
    main()

import json
import requests

url = "http://localhost:11434/api/generate"

prompt = """
Extract atomic factual claims from the text below.

Return ONLY valid JSON in this exact format:

{
  "claims": [
    {
      "text": "claim text",
      "type": "FACT"
    }
  ]
}

Rules:
- Split independent facts into separate claims.
- Do not invent information.
- Preserve numbers exactly.
- Allowed types: FACT, METRIC, FEATURE, MARKET, COMPETITIVE.

TEXT:
The company launched a new analytics platform in 2025.
The platform costs $20 per month.
The company has 10 million users worldwide.
The analytics market is growing rapidly.
"""

payload = {
    "model": "deepseek-coder:latest",
    "prompt": prompt,
    "stream": False,
    "format": "json",
    "options": {
        "temperature": 0
    }
}

response = requests.post(
    url,
    json=payload,
    timeout=120,
)

response.raise_for_status()

result = response.json()

print("MODEL RESPONSE")
print("=" * 60)

raw = result["response"]
print(raw)

print("\n" + "=" * 60)

parsed = json.loads(raw)

claims = parsed.get("claims", [])

if len(claims) < 3:
    raise RuntimeError(
        f"Too few claims extracted: {len(claims)}"
    )

for claim in claims:
    if not claim.get("text"):
        raise RuntimeError("Empty claim text")

    if claim.get("type") not in {
        "FACT",
        "METRIC",
        "FEATURE",
        "MARKET",
        "COMPETITIVE",
    }:
        raise RuntimeError(
            f"Invalid claim type: {claim.get('type')}"
        )

print(f"\nTotal valid claims: {len(claims)}")
print("SEMANTIC MODEL CAPABILITY: PASSED")

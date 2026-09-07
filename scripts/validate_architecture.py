from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "src/core",
    "src/loops",
    "src/research",
    "src/search",
    "src/extraction",
    "src/evidence",
    "src/entities",
    "src/verification",
    "src/memory",
    "src/analysis",
    "src/competitive",
    "src/product",
    "src/gap",
    "src/opportunity",
    "src/decision",
    "src/reasoning",
    "src/synthesis",
    "src/critics",
    "src/evaluation",
    "src/reporting",
    "config",
    "data",
    "tests",
    "benchmarks",
    "scripts",
    "docs",
    "infra",
    "ARCHITECTURE.md",
]

missing = []

for relative_path in REQUIRED_PATHS:
    path = ROOT / relative_path

    if path.exists():
        print(f"PASS  {relative_path}")
    else:
        print(f"FAIL  {relative_path}")
        missing.append(relative_path)

print("\n" + "=" * 50)

if missing:
    print("ARCHITECTURE VALIDATION: FAILED")
    print(f"Missing items: {len(missing)}")
    sys.exit(1)

print("ARCHITECTURE VALIDATION: PASSED")
print("All locked structural components are present.")

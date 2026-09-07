# Contributing to AegisLoop

Thank you for your interest in contributing to **AegisLoop**! We welcome bug fixes, documentation improvements, benchmark tasks, and architectural enhancements that adhere to our core scientific and governance principles.

---

## Code of Conduct

All contributors and participants agree to abide by the project's [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Core Engineering Principles

When contributing to AegisLoop, please keep the following immutable rules in mind:

1. **Evidence-First**: No mechanism or guard may be added unless empirical evidence demonstrates that it solves a real failure mode without degrading general reliability.
2. **Deterministic Governance**: State machine transitions, rollback mechanisms, and test integrity verification must remain deterministic and reproducible.
3. **Multi-Tier Verification**: Never assume an agent's self-certification is correct. Every patch must be independently evaluated against Visible, Regression, and Hidden Invariant suites.
4. **Preserve Locked Architecture**: All contributions must conform to the 28 locked architectural components outlined in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Nia00-glitch/aegis-loop.git
   cd aegis-loop
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Verification Suite**:
   ```bash
   pytest tests/test_e2e_governance_requirements.py -v
   python scripts/validate_architecture.py
   python scripts/test_loop_engineering_enhancements.py
   python scripts/test_remediation_target_swap.py
   ```

---

## Pull Request Guidelines

1. **Branch Naming**: Use clear prefixes:
   - `feat/`: New governance capabilities or research adapters
   - `fix/`: Bug fixes or repair loop improvements
   - `test/`: New benchmark tasks or invariant tests
   - `docs/`: Documentation and diagram improvements
2. **Test Coverage**: Every PR must include corresponding automated tests.
3. **Clean Diffs**: Ensure no secrets, `.env` files, or binary caches are included.
4. **Commit Messages**: Follow Conventional Commits formatting (e.g., `feat(loop): add multi-tier invariant validator`).

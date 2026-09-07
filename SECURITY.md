# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Security Architecture & Protections

AegisLoop is designed with defense-in-depth safeguards against rogue agent execution and evaluator gaming:

1. **G3 Anti-Gaming Cryptographic Test Integrity**:
   - Computes a SHA-256 hash of all test targets prior to agent dispatch.
   - Re-verifies hashes during `verify_stage`. Any unauthorized mutation to test files instantly halts execution and triggers deterministic rollback (`test_tampering_rolled_back`).

2. **G2 Regression Invariant Gate**:
   - Executes regression test targets against untouched baseline APIs after mutations.
   - Prevents unverified changes from leaking into production baselines.

3. **Deterministic Rollback**:
   - Git checkpoints are captured at `define_stage`.
   - Any fatal violation, budget exhaustion, or structural blocker triggers clean atomic rollback (`git_rollback`).

4. **Secret Hygiene**:
   - No credentials, tokens, or private endpoints are hardcoded.
   - Model routers and workers consume credentials strictly via environment variables (`OMNIROUTE_API_KEY`, `OPENAI_API_KEY`, etc.).

---

## Reporting a Vulnerability

If you discover a security vulnerability in AegisLoop, please do **NOT** open a public GitHub issue.

Instead, please email security disclosures to **security@loopengineering.dev** or submit a private security advisory through GitHub's Security tab.

Please include:
- Description of the vulnerability and attack vector
- Steps to reproduce or proof-of-concept script
- Impact assessment on host systems or repositories

We commit to acknowledging your disclosure within 48 hours and providing a remediation timeline.

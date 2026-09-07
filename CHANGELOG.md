# Changelog

All notable changes to **AegisLoop** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-07

### Added
- **LangGraph Governed State Machine**: Formal state transitions for `DEFINE`, `PLAN`, `IMPLEMENT`, `TEST`, `VERIFY`, `RE-EVALUATE`, `FAILURE`, and `REFINE`.
- **G1 Evidence & Provenance Ledger**: Monotonic stage transition tracking, duration profiling, and structured audit logs via `src/loops/loop_ledger.py`.
- **G2 Regression & Invariant Protection Gate**: Dedicated re-evaluation suite intercepting regressions in untouched baseline APIs with automated retry and rollback.
- **G3 Anti-Gaming Cryptographic Test Integrity**: SHA-256 pre-mutation test file hashing preventing agents from tampering with test assertions to pass benchmarks.
- **G4 Structural Unrepairability Gate**: Early detection of fatal blocker loops (e.g. repeated `IMPORT_ERROR` or syntax anomalies) to prevent budget burn.
- **G5.1 Dynamic Remediation Target Swapping**: Dynamically redirects test feedback during repair cycles from original task targets to failing regression targets, backed by Dual-Target Verification.
- **G5.2 Adaptive Turn-Budget Handover & Context Preservation**: Compact decision-relevant context handover across macro-iterations with dynamic turn budget expansion under a strict 25-turn global ceiling.
- **Multi-File Benchmark Suite**: 4 realistic engineering benchmark tasks (`ledger_reconciliation`, `rate_limiter_invariants`, `tiered_lru_cache`, `stream_watermark_aggregator`) with 3-tier independent evaluation (Visible, Regression, Hidden Invariants).
- **Opaque-Box E2E Governance Test Suite**: 31 comprehensive test assertions (`tests/test_e2e_governance_requirements.py`) validating G1–G5 safety guarantees across Tiers 1–4.
- **Causal Ablation Experiment Harness**: 12-trial controlled harness measuring causal advantage of Loop Engineering controls over uncontrolled baseline agents.
- **Model Router Gateway**: Pluggable provider routing supporting local OmniRoute daemon, OpenAI, Anthropic, LiteLLM, and local Ollama weights.
- **Evidence-First Research Pipeline**: Crawl4AI headless crawler, SearXNG search adapter, sentence-level claim extraction, and document chunking.

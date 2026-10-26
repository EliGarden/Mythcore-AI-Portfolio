# Orchestrator | A permit is not a completion receipt

**Selected version:** 0.4.1 Governed Promotion Corrective Closure. **Capability demonstrated:** decomposition of authority, execution and recovery. This is a local reference implementation, not a production orchestration platform.

The concrete problem is preventing an accepted candidate, a governance decision or a reserved permit from being mistaken for a completed canonical promotion. The package separates a verified Governance OS decision, Authorization-Kernel-owned permission, Orchestrator execution and a Flower Garden durable receipt. Its native permit binds the exact candidate, parameter hash, expected current version, operation, executor and handler. [O1-O3]

**Source-grounded mechanism walkthrough, not a new run:** a permit is issued for a specific candidate and expected version; the execution identity reserves it; reservation alone is insufficient to mark completion; durable completion evidence is required. The source capability profile declares atomic lease reservation, retry under the same execution identity until terminal, and rejection of replay after completion. Exact behavior outside the tested fault matrix remains unresolved. No new retries or recovery rules are added here. [O3]

**Trade-off:** explicit state and version bindings improve auditability but introduce distributed state, lease, key-lifecycle and crash-recovery obligations. The local signing key is generated in the existing implementation; that is not proof of a production trust infrastructure. The source reports a six-process local workflow, not adoption by the independently deployed ecosystem. [O1-O3]

**Evidence:** the conformance record reports 173 passing Orchestrator tests, but only 77.79% line and 61.92% branch coverage, below its required 94% and 90%. Per-route/per-command and cross-process fault matrices remain incomplete. Overall acceptance, pilot readiness and production readiness remain false/incomplete. These are historical records, not rerun benchmarks. [O2]

**Contribution boundary:** use this sample to assess Lux's architecture and boundary reasoning, with AI-assisted implementation; do not infer independent coding authorship. The portfolio's critique is internal editorial review, not external validation.

O1: [Implementation status](../sources/orchestrator/IMPLEMENTATION_STATUS.json) · O2: [Conformance report](../sources/orchestrator/CONFORMANCE_REPORT.json) · O3: [Existing permit implementation](../sources/orchestrator/src/governance_kernel_promotion_extension/runtime.py)

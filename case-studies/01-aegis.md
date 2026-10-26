# Aegis | Verifying meaning as well as bytes

**Selected version:** Aegis 0.4.2. **Role:** flagship AI work sample. **Maturity:** bounded research/education implementation with historical test evidence; overall validation blocked. The release title does not override the manifest's false pilot-deployability and production-readiness flags.

## 1. Concrete problem

A structured artifact can have internally consistent hashes while telling a false story about a decision or its consequences. Recomputing an artifact's own hashes is insufficient if its author changed the claimed governance outcome, permit, execution state or explanation. A second risk is equating 'the verifier accepts this representation' with 'a legitimate institution authorized this action.'

Aegis addresses a narrower, inspectable problem: preserve one source episode and construct bounded counterfactual branches whose content can be checked against a registered deterministic engine and the exact authority material it used. It does not solve AI alignment or implement real constitutional government. [A1, A2, A3]

## 2. Intended users and context

The source positions Aegis as a constitutional-AI research and education laboratory. A reviewer or learner inspects the immutable CEE-001 episode, a constrained alternative and their differences. The existing Python/FastAPI modular monolith has static Gate, Grow and Map surfaces. A reviewer is studying a local model of a workflow, not exercising the real-world authority represented by that workflow. Intended research/education use is not evidence of actual adoption or learning benefit. [A1, A2]

## 3. Mechanisms and boundaries

| Boundary | What it checks | What it cannot establish |
|---|---|---|
| Integrity consistency | Artifact hashes, references, identity and root consistency. | Whether a self-consistent story is the right story. |
| Semantic reconstruction | Agreement with the branch reconstructed from canonical parent, mutations and registered engine. | Whether the engine represents the real world accurately. |
| Exact authority-content agreement | Digests for engine, variable/template registries, selected template, invariants, disclosure and serialization policies, and parent content. | Institutional legitimacy, independent trust or real execution authority. |

The canonical episode is preserved; counterfactual mutation is confined to approved variables/templates. Claim-safe metadata and strict operating modes keep user-authored wording from becoming a runtime declaration of legitimacy. No live Governance, Hydra Twin, Flower Garden or Mirror AI runtime is connected. [A1-A4]

## 4. Worked example

The existing `lab-004-reviewer-denies` template sets `governance.review_outcome` to `deny`. Its stated causal effects are: authorization absent; permit and execution blocked; completion withheld. Its uncertainty field says that the hypothetical denial rationale is not supplied. The portfolio adds no rationale. [A5]

The stored branch-conformance report records successful reconstruction of this branch against its declared authority content. Separately, the semantic-forgery report lists nine changed-state variants whose integrity passes while semantic and composite verification fail. This contrast demonstrates the intended distinction between consistent bytes and conforming semantics. These are **historical source-reported results**, not fresh executions or independent attack testing performed for this portfolio. [A6, A7]

Read the [annotated sequence](../walkthroughs/aegis-denial-and-tamper.md) without installing software.

## 5. Alternatives and trade-offs

- **Hash-only checking:** simpler and cheaper, but the source's forgery records show why internal consistency alone is insufficient for the modeled claim.
- **Version-label-only binding:** easy to read, but a version string does not identify the exact code or registry bytes. Content binding improves traceability while increasing maintenance and migration burden.
- **Unbounded generated alternatives:** broader exploration, but harder to reconstruct and to keep within the source's claims. Aegis chooses bounded templates; that limits expressiveness and external validity.
- **A live integrated governance service:** potentially more operationally useful, but requires real identity, institutional authority, security and operations evidence that this package does not establish. The current separation is an intentional scope boundary, not an accomplished integration. [A1-A4, A7]

These comparisons are editorial analysis of existing design choices, not new architectural decisions.

## 6. Failure modes and open questions

An exact reconstruction can faithfully reproduce a flawed engine. A content digest binds bytes; it does not establish a trusted origin. Curated templates may teach users the author's assumptions rather than general constitutional reasoning. UI wording may encourage users to mistake verification for legitimacy. The historical overall validation also leaves full-pipeline reproducibility, real browser/accessibility checks, container enforcement and parts of supply-chain verification unresolved. [A2, A3, A4, A8]

## 7. Implemented, tested, conceptual

The selected package contains source code, schemas, templates, tests and status records. Its validation report records **433 passing tests**, while the overall report remains **blocked** and public-pilot deployability is **false**. This is not a contradiction to erase: passing technical checks and completing all release gates are different claims. There is no empirical study of comprehension, institutional legitimacy or production operation established here. Source tests were not rerun for this curation. [A2, A8]

## 8. Contribution and AI assistance

This work sample supports discussion of Lux's problem framing, requirements, distinctions and iterative design direction. AI assisted formalization, documentation, implementation and checking. The repository is not evidence that Lux independently programmed the implementation. Exact responsibility for each code change has not been independently established; the [contribution statement](../CONTRIBUTIONS.md) makes that boundary explicit.

## 9. Relevance to an AI team

The assessable skill is turning a broad governance concern into an inspectable failure condition, multiple verification boundaries, a constrained example and falsifiable limitations. Teams can review the logic, question the assumptions and compare the proposed evaluation with the evidence already available. This work sample makes no claim that terminology or test counts establish novelty or research validity.

## Included sources

- A1: [Source README](../sources/aegis/README.md)
- A2: [Release manifest](../sources/aegis/RELEASE_MANIFEST.json)
- A3: [Implementation status](../sources/aegis/docs/IMPLEMENTATION_STATUS.md)
- A4: [Contradictions and decisions](../sources/aegis/docs/CONTRADICTIONS_AND_DECISIONS.md)
- A5: [Reviewer-denies template](../sources/aegis/data/lab_templates/lab-004-reviewer-denies.json)
- A6: [Branch-conformance report](../sources/aegis/reports/branch-semantic-conformance-report.json)
- A7: [Semantic-forgery report](../sources/aegis/reports/semantic-forgery-test-report.json)
- A8: [Historical validation report](../sources/aegis/reports/validation-report.json)

# Content-Addressed Semantic Authority

Aegis v0.4.2 treats version strings as labels, not sufficient evidence. `canonical/semantic_authority_registry_v0.4.2.json` records a stable ID, version, exact SHA-256 content digest, source allowlist, serialization rule, generation method, compatibility status, and limitation statement for every authority used in branch derivation.

The branch engine binds the exact engine bundle, variable registry, template registry, selected template, invariant registry, disclosure policy, serialization policy, and canonical parent. The semantic verifier independently recalculates packaged content digests before reconstruction. Unknown IDs, unsupported versions, changed content, missing templates, and evaluator/registry divergence fail closed.

Code bundles bind repository-relative path and LF-normalized content. JSON authorities reject duplicate keys and use canonical JSON. Selected-template digests cover the authoritative entry in the template registry; derived expected-output fields are excluded from template authority to avoid a self-referential digest.

The semantic-verifier bundle digest is reported by verification results but is not trusted from the submitted branch.

This mechanism proves agreement with packaged Aegis authority content. It does not establish truth, legitimacy, authorization, execution, or external certification.

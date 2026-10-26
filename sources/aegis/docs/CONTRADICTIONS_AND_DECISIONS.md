# Contradictions and Decisions

## v0.4.1 corrective decisions

- The root-preimage instruction listed three exclusions while also requiring deprecated `branch_id` to equal the artifact ID. The alias is equally self-referential. Decision: exclude it and disclose the exception.
- Clean installation failure was named for reproduction, but the supplied archive installed successfully. Decision: record the successful investigation and remove the hidden `PYTHONPATH` injection.
- Duplicate mapping keys were named, but Python AST inspection found none. Decision: record “not reproduced.”
- Container and browser binaries are unavailable. Decision: preserve hardened definitions and blocked evidence without passing either gate.
- The v0.4.0 engine is not registered as an authoritative semantic verifier. Decision: provide a read-only compatibility projection with semantic status `unavailable`.

## v0.4 decisions

- The v0.4 master prompt names a v0.3 master prompt and Aegipedia v0.0.2 as authorities, but neither was supplied. Decision: use the v0.3 release archive/canonical JSON and v0.4 prompt, record the absence, and create only the required Aegipedia update input.
- Duplicate Governance and Flower Garden archives were byte-identical. Decision: inventory duplicates and never merge them into the baseline.
- Older v0.1/v0.2 Aegis and older standalone ecosystem artifacts conflict with the explicit v0.3 baseline. Decision: treat them only as lineage/boundary evidence.
- The task asks for a deployment package but forbids fabricated deployment checks. Docker and Podman are absent. Decision: implement the package, mark Gate 7 and full Gate 8 failed, and set public-pilot deployability false.
- The canonical timestamp is used for branch output to guarantee deterministic bytes. It is disclosed as inherited, not a real branch creation time.

1. **Product identity:** the early design called the whole product “Constitutional Episode Explorer.” The v0.3 authority prompt defines Aegis as the top-level dual-surface product and Explorer as a shared module. The v0.3 model controls.
2. **Mirror version:** the standalone donor describes Mirror v1.1, while the source Vertical Slice integrates Mirror AI Canonical v1.2. The source episode’s v1.2 facts control; v1.1 contributes only compatible non-executive boundaries.
3. **Public mutation:** v0.2 exposed fixture creation as a normal public route. v0.3 defaults to immutable public projection; fixture mutation is development-only.
4. **Verification booleans:** v0.2 contained declared or hardcoded verification states. v0.3 computes importer, replay, and public-bundle results.
5. **Signature meaning:** source records contain local Ed25519 metadata, but the archive does not establish an independently trusted key set. Metadata is retained; independent verification and legitimacy are not claimed.
6. **Archtopia and Arcadian context:** those systems provide wider civilizational and participatory principles, but the v0.3 scope explicitly prohibits their runtime integration. They are not implemented or absorbed.
7. **EduKa scope:** EduKa’s wider architecture includes Archtopia-first functions. Aegis implements only the read-only educational adapter and anti-capture rules required by Grow.

# Mirror AI v1.3.0 — Relational Interpretation

A complete architecture release extending Mirror AI v1.2.0, with an opt-in typed relational reference and preserved fifteen-faculty runtime.

**Decision:** include the update. Evidence-linked alternatives improve inspectability; symbolic morphology remains optional and experimental. This is not a production or empirically validated cognition release.

## Read

- `ARCHITECTURE.md` — complete standalone architecture and scope.
- `Mirror_AI_v1.3.0_FULL.json` — unified machine-readable architecture, contracts, schemas, examples, and evidence.
- `ASSESSMENT.md` — necessity, benefits, costs, and acceptance conditions.
- `docs/MIGRATION_v1.2.0_to_v1.3.0.md` — compatible rollout and rollback.
- `docs/IMPLEMENTATION_STATUS.md` — implemented versus specified capabilities.
- `evidence/validation_report.json` — tests actually run for this release.
- `lineage/` — unchanged parent archives, proposal, historical documents and records.

## Run the bounded reference

Python 3.11 or newer is declared by the inherited project. This release was executed on Python 3.12.14 only.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]' 'jsonschema>=4,<5'
python -m pytest -q
PYTHONPATH=src python scripts/demo_relational.py
PYTHONPATH=src python scripts/export_schemas.py
python scripts/validate_release.py
```

`demo_relational.py` uses a fixed logical clock and synthetic data. It validates authored candidates and creates a source-linked view; it does not generate psychological interpretations. The relational service accepts only explicitly enabled untrusted fixtures. There is no relational HTTP route, profile-writing hook, live Gaia integration, or new authorization capability.

The inherited API/CLI remain available after installation. API path versions remain `/v1/` and `/v1.2/`; the runtime release version is 1.3.0. The default faculties preserve the inherited reference behavior.

The JSON Schemas encode structural rules. Python model/service validators additionally enforce graph references, evidence-account completeness, temporal/profile binding, source lineage, and faithful views. JSON Schema validation alone is insufficient.

## Evidence and limitations

See `evidence/validation_report.json` for exact results. Original v1.2.0 regression execution reproduced 67 passes and one expired-fixture failure. The successor applies the provided test-only timestamp correction without weakening expiry checks. Source-reported historical results remain separately labeled.

The package does not claim that its explanations are true, its confidence is calibrated, its symbols measure cognition, or external systems have adopted the contracts. Existing ISSUE-005 and production trust/persistence gaps remain open. No external canonical pointer or deployment has been changed.

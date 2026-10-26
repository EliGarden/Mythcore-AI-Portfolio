# Aegis v0.4.2

**Content-Addressed Semantic Authority, Reproducible Validation & Verified Public-Pilot Release**

Aegis is a bounded constitutional-AI research and education laboratory. It publishes one immutable public episode, CEE-001, and generates only constrained counterfactual branches. It does not connect to live Governance, Hydra Twin, Flower Garden, or Mirror AI runtimes and cannot issue real decisions, authorizations, permits, or execution requests.

## Release status

- Stable system ID: `sys.aegis`
- Canonical URN: `urn:mythcorelabs:system:aegis`
- Default mode: `public_laboratory`
- Feedback: disabled by default
- Public-pilot deployability: see `RELEASE_MANIFEST.json` and `reports/public-pilot-readiness-report.json`
- Production readiness: **false**
- Institutional legitimacy: **not verified**
- External penetration test: **not completed**
- Formal accessibility certification: **not completed**

## What v0.4.2 verifies

Branch verification has three distinct boundaries:

1. **Integrity consistency** checks hashes, identifiers, references, and the artifact root.
2. **Semantic conformance** independently reconstructs the branch.
3. **Content-addressed authority agreement** binds that reconstruction to the exact engine, variable registry, template registry, selected template, invariant registry, disclosure policy, serialization policy, and canonical-parent content.

Passing these checks does not prove empirical truth, institutional legitimacy, authorization, execution, or production suitability.

## Installation

Supported release-builder target: CPython 3.12 on Linux x86_64.

```text
python -m pip install -e .
python -m pip install -e ".[dev]"
```

Build and install the project wheel:

```text
python -m build
python -m pip install dist/aegis_constitutional_ai_laboratory-0.4.2-py3-none-any.whl
```

Verified offline installation for the declared target:

```text
unzip aegis_v0.4.2_wheelhouse.zip
python -m pip install --no-index --find-links aegis_v0.4.2_wheelhouse aegis-constitutional-ai-laboratory==0.4.2
```

See `docs/INSTALLATION.md` and `docs/OFFLINE_INSTALLATION.md` for evidence boundaries.

## Run locally

```text
python -m aegis_lab
```

Open `http://127.0.0.1:8000`.

Operating modes are strictly limited to:

- `public_projection`
- `public_laboratory`
- `development_fixture`

## Validation

Standard validation writes reports and runtime state outside the repository:

```text
python -m scripts.run_validation
```

Release evidence generation requires an explicit output:

```text
AEGIS_REPORT_OUTPUT=/absolute/staging/reports \
python -m scripts.run_validation --output-dir /absolute/staging/reports --release-output
```

Core checks:

```text
python -m pytest
ruff check aegis_lab scripts tests
ruff format --check aegis_lab scripts tests
mypy aegis_lab scripts
python -m scripts.verify_semantic_authorities
python -m scripts.verify_semantic_conformance
python -m scripts.check_repository_mutation
```

## Public-pilot profile

`AEGIS_DEPLOYMENT_PROFILE=public_pilot` requires operator, support, privacy, and region configuration. `/api/v1/ready` returns HTTP 503 when required authorities, canonical content, templates, notices, or configuration are unavailable.

The eight public notices are available without JavaScript under `/pilot/*`. The public profile disables development routes, debug output, and feedback by default; uses privacy-minimized structured logs; and enables an anonymous global abuse bound. See `deploy/PUBLIC_PILOT_CHECKLIST.md`.

## Repository map

- `aegis_lab/` — typed FastAPI modular monolith
- `canonical/` — canonical architecture and semantic-authority registries
- `data/public_episodes/` — immutable CEE-001
- `data/lab_templates/` — twelve bounded templates
- `static/` — Gate, Grow, Map, and public notices
- `schemas/` — JSON Schema 2020-12 contracts
- `scripts/` — validation, distribution, packaging, and operations tools
- `deploy/` — container and reverse-proxy examples
- `ops/` — incident, rollback, revocation, shutdown, and data-response runbooks
- `reports/` — sealed evidence

## Canonical preservation

CEE-001 remains unchanged:

- Public file SHA-256: `9e06ecbf1afb5b885b3d353e4b6d905b3aee8522d11c85640f0b8f42abf15521`
- Canonical bundle digest: `98fab60b1964d912b0acfcab02b0768c8cc5fcc692e68a40ddebf6b0315d7470`
- Fifteen public records and ten public stages

No future migration may silently delete prior architecture.

from __future__ import annotations

import os
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Literal

from aegis_lab.canonical import canonical_hash
from aegis_lab.laboratory.authorities import (
    DISCLOSURE_POLICY_VERSION,
    ENGINE_VERSION,
    SEMANTIC_VERIFIER_ID,
    SEMANTIC_VERIFIER_VERSION,
    TEMPLATE_REGISTRY_VERSION,
    VARIABLE_REGISTRY_VERSION,
    calculate_descriptor_digest,
    load_authority_registry,
    select_authority,
    verify_branch_authority_bindings,
)
from aegis_lab.laboratory.branches import (
    BranchEngine,
    branch_record_digest_payload,
    branch_root_digest_payload,
    disclosure_digest_payload,
)
from aegis_lab.laboratory.comparison import comparison_digest_payload
from aegis_lab.laboratory.models import (
    BranchCreateRequest,
    BranchIntegrityVerificationResult,
    BranchSemanticConformanceResult,
    CompositeBranchVerificationResult,
    CounterfactualBranchBundle,
    RequestedMutation,
    SemanticAuthorityType,
    SemanticMismatch,
    SourceClass,
)
from aegis_lab.laboratory.templates import TemplateRepository
from aegis_lab.models import PublicEpisodeBundle

INTEGRITY_VERIFIER_VERSION = "aegis.integrity_verifier.v0.4.2"
SUPPORTED_ENGINES = {ENGINE_VERSION}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _deterministic_evidence_timestamp() -> str | None:
    raw = os.getenv("SOURCE_DATE_EPOCH")
    if raw is None:
        return None
    try:
        return datetime.fromtimestamp(int(raw), UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        return None


def verify_branch_integrity(
    branch: CounterfactualBranchBundle,
    canonical: PublicEpisodeBundle,
) -> BranchIntegrityVerificationResult:
    verification_time = _utc_now()
    errors: list[str] = []
    warnings: list[str] = []
    checked_digests = 0
    canonical_envelope_ids = {record.source_envelope_id for record in canonical.public_records}
    canonical_signatures = {str(envelope.signature) for envelope in canonical.source_envelopes}

    if branch.parent_public_episode_id != canonical.public_episode_id:
        errors.append("canonical parent episode mismatch")
    if branch.parent_bundle_digest != canonical.integrity_manifest.bundle_digest:
        errors.append("canonical parent digest mismatch")
    if branch.source_class not in {SourceClass.COUNTERFACTUAL_DERIVED, SourceClass.INVALID_COUNTERFACTUAL}:
        errors.append("unsupported branch source class")
    if str(branch.branch_definition.authority_claim) != "none":
        errors.append("branch definition claims authority")
    if bool(branch.branch_definition.execution_requested):
        errors.append("branch definition requests real execution")
    if branch.branch_id != branch.branch_artifact_id:
        errors.append("deprecated branch_id is not an alias of branch_artifact_id")
    if branch.branch_semantic_id != f"branch-sem-{branch.branch_semantic_digest[:24]}":
        errors.append("SEMANTIC_ID_MISMATCH: semantic ID does not match the semantic digest")

    record_ids = {record.branch_record_id for record in branch.branch_records}
    checked_links = 0
    for record in branch.branch_records:
        checked_digests += 1
        if record.branch_record_id in canonical_envelope_ids:
            errors.append(f"canonical envelope id reused: {record.branch_record_id}")
        if str(record.authority_claim) != "none" or not bool(record.illustrative):
            errors.append(f"branch record misstates authority: {record.branch_record_id}")
        if record.simulated_producer_role in {item.producer_system_id for item in canonical.public_records}:
            errors.append(f"canonical producer impersonated: {record.branch_record_id}")
        if str(record.public_payload.get("signature")) in canonical_signatures:
            errors.append(f"canonical signature reused: {record.branch_record_id}")
        expected = canonical_hash(branch_record_digest_payload(record))
        if expected != record.branch_record_digest:
            errors.append(f"branch record digest mismatch: {record.branch_record_id}")
        if branch.integrity_manifest.branch_record_digests.get(record.branch_record_id) != expected:
            errors.append(f"branch record manifest mismatch: {record.branch_record_id}")
        for parent_id in record.causal_parent_ids:
            checked_links += 1
            if parent_id not in record_ids:
                errors.append(f"unknown causal parent: {parent_id}")

    checked_digests += 1
    disclosure_expected = canonical_hash(disclosure_digest_payload(branch.disclosure_manifest))
    if disclosure_expected != branch.disclosure_manifest.digest:
        errors.append("branch disclosure digest mismatch")
    if disclosure_expected != branch.integrity_manifest.disclosure_manifest_digest:
        errors.append("branch disclosure manifest inventory mismatch")

    checked_digests += 1
    comparison_expected = canonical_hash(comparison_digest_payload(branch.canonical_comparison))
    if comparison_expected != branch.canonical_comparison.comparison_digest:
        errors.append("canonical comparison digest mismatch")
    if comparison_expected != branch.integrity_manifest.canonical_comparison_digest:
        errors.append("comparison integrity inventory mismatch")

    checked_digests += 1
    definition_expected = canonical_hash(branch.branch_definition.model_dump(mode="json"))
    if definition_expected != branch.integrity_manifest.branch_definition_digest:
        errors.append("branch definition digest mismatch")
    mutation_expected = canonical_hash([item.model_dump(mode="json") for item in branch.branch_definition.mutations])
    checked_digests += 1
    if mutation_expected != branch.integrity_manifest.mutation_set_digest:
        errors.append("mutation-set digest mismatch")
    findings_expected = canonical_hash([item.model_dump(mode="json") for item in branch.constitutional_findings])
    checked_digests += 1
    if findings_expected != branch.integrity_manifest.invariant_findings_digest:
        errors.append("invariant-findings digest mismatch")

    root_expected = canonical_hash(branch_root_digest_payload(branch))
    checked_digests += 1
    if root_expected != branch.branch_root_digest:
        errors.append("branch root digest mismatch")
    if root_expected != branch.integrity_manifest.branch_root_digest:
        errors.append("branch root integrity inventory mismatch")
    if branch.branch_artifact_id != f"branch-art-{root_expected[:24]}":
        errors.append("ARTIFACT_ID_MISMATCH: artifact ID does not match the branch root digest")

    return BranchIntegrityVerificationResult(
        verification_type="aegis_branch_integrity_consistency",
        status="failed" if errors else "passed",
        branch_semantic_id=branch.branch_semantic_id,
        submitted_artifact_id=branch.branch_artifact_id,
        parent_bundle_digest_expected=canonical.integrity_manifest.bundle_digest,
        parent_bundle_digest_observed=branch.parent_bundle_digest,
        checked_records=len(branch.branch_records),
        checked_mutations=len(branch.branch_definition.mutations),
        checked_causal_links=checked_links,
        checked_constraints=len(branch.branch_definition.mutations),
        checked_digests=checked_digests,
        errors=errors,
        warnings=warnings,
        evidence_refs=[
            canonical.public_episode_id,
            canonical.integrity_manifest.bundle_digest,
            branch.branch_artifact_id,
        ],
        verifier_version=INTEGRITY_VERIFIER_VERSION,
        verified_at=verification_time,
        verification_performed_at=verification_time,
        deterministic_evidence_timestamp=_deterministic_evidence_timestamp(),
        limitations=[
            "Integrity consistency does not prove derivation by the official Aegis engine.",
            "It does not establish truth, legitimacy, authorization, execution, or source trust.",
        ],
    )


def _diff(expected: Any, observed: Any, path: str = "$") -> list[SemanticMismatch]:
    if type(expected) is not type(observed):
        return [SemanticMismatch(path=path, expected=expected, observed=observed)]
    if isinstance(expected, dict):
        result: list[SemanticMismatch] = []
        for key in sorted(set(expected) | set(observed)):
            if key not in expected:
                result.append(SemanticMismatch(path=f"{path}.{key}", expected=None, observed=observed[key]))
            elif key not in observed:
                result.append(SemanticMismatch(path=f"{path}.{key}", expected=expected[key], observed=None))
            else:
                result.extend(_diff(expected[key], observed[key], f"{path}.{key}"))
        return result
    if isinstance(expected, list):
        result = []
        for index in range(max(len(expected), len(observed))):
            left = expected[index] if index < len(expected) else None
            right = observed[index] if index < len(observed) else None
            result.extend(_diff(left, right, f"{path}[{index}]"))
        return result
    return [] if expected == observed else [SemanticMismatch(path=path, expected=expected, observed=observed)]


def reconstruct_branch(
    submitted: CounterfactualBranchBundle,
    canonical: PublicEpisodeBundle,
    templates: TemplateRepository,
) -> CounterfactualBranchBundle:
    if submitted.engine_version not in SUPPORTED_ENGINES:
        raise LookupError("ENGINE_VERSION_UNSUPPORTED")
    definition = submitted.branch_definition
    authority_comparison = verify_branch_authority_bindings(
        submitted.semantic_authority_bindings,
        definition.template_id,
    )
    failed_authorities = [item for item in authority_comparison if item["status"] != "passed"]
    if failed_authorities:
        error_by_type = {
            SemanticAuthorityType.BRANCH_ENGINE_BUNDLE.value: "ENGINE_BUNDLE_DIGEST_MISMATCH",
            SemanticAuthorityType.SCENARIO_VARIABLE_REGISTRY.value: "VARIABLE_REGISTRY_DIGEST_MISMATCH",
            SemanticAuthorityType.BRANCH_TEMPLATE_REGISTRY.value: "TEMPLATE_REGISTRY_DIGEST_MISMATCH",
            SemanticAuthorityType.SELECTED_BRANCH_TEMPLATE.value: "SELECTED_TEMPLATE_DIGEST_MISMATCH",
            SemanticAuthorityType.CONSTITUTIONAL_INVARIANT_REGISTRY.value: "INVARIANT_REGISTRY_DIGEST_MISMATCH",
            SemanticAuthorityType.BRANCH_DISCLOSURE_POLICY.value: "DISCLOSURE_POLICY_DIGEST_MISMATCH",
            SemanticAuthorityType.CANONICAL_SERIALIZATION_POLICY.value: "SERIALIZATION_POLICY_UNSUPPORTED",
            SemanticAuthorityType.CANONICAL_PARENT_BUNDLE.value: "SEMANTIC_AUTHORITY_DIGEST_MISMATCH",
        }
        raise LookupError(
            error_by_type.get(failed_authorities[0]["authority_type"], "SEMANTIC_AUTHORITY_DIGEST_MISMATCH")
        )
    if definition.variable_registry_version != VARIABLE_REGISTRY_VERSION:
        raise LookupError("VARIABLE_REGISTRY_VERSION_UNAVAILABLE")
    if definition.template_registry_version != TEMPLATE_REGISTRY_VERSION:
        raise LookupError("TEMPLATE_VERSION_UNAVAILABLE")
    if definition.disclosure_policy_version != DISCLOSURE_POLICY_VERSION:
        raise LookupError("DISCLOSURE_POLICY_VERSION_UNAVAILABLE")
    try:
        template = templates.get(definition.template_id) if definition.template_id else None
    except ValueError as exc:
        raise LookupError("TEMPLATE_VERSION_UNAVAILABLE") from exc
    custom = [
        RequestedMutation(variable_id=item.variable_id, requested_value=item.requested_value)
        for item in definition.mutations
        if item.requested_by == "public_user"
    ]
    request = BranchCreateRequest(
        parent_public_episode_id=definition.parent_public_episode_id,
        parent_bundle_digest=definition.parent_bundle_digest,
        template_id=definition.template_id,
        title=definition.title,
        purpose=definition.purpose,
        question=submitted.question,
        optional_note=definition.optional_note,
        mutations=custom,
    )
    return BranchEngine().build(
        request,
        canonical,
        template_mutations=template.approved_mutations if template else None,
        template_title=template.title if template else None,
        template_question=template.question if template else None,
        operating_mode=submitted.operating_mode,
        metadata_provenance_override=definition.metadata_provenance,
    )


def verify_branch_semantic(
    branch: CounterfactualBranchBundle,
    canonical: PublicEpisodeBundle,
    templates: TemplateRepository | None = None,
) -> BranchSemanticConformanceResult:
    verification_time = _utc_now()
    errors: list[str] = []
    warnings: list[str] = []
    reconstructed: CounterfactualBranchBundle | None = None
    authority_comparison: list[dict[str, Any]] = []
    semantic_verifier_digest = "0" * 64
    try:
        authority_comparison = verify_branch_authority_bindings(
            branch.semantic_authority_bindings,
            branch.branch_definition.template_id,
        )
        registry = load_authority_registry()
        semantic_verifier_descriptor = select_authority(
            registry,
            SemanticAuthorityType.SEMANTIC_VERIFIER_BUNDLE,
            SEMANTIC_VERIFIER_ID,
            SEMANTIC_VERIFIER_VERSION,
        )
        if calculate_descriptor_digest(semantic_verifier_descriptor) != semantic_verifier_descriptor.content_digest:
            raise LookupError("SEMANTIC_AUTHORITY_DIGEST_MISMATCH")
        semantic_verifier_digest = semantic_verifier_descriptor.content_digest
        if templates is None:
            from aegis_lab.config import LAB_TEMPLATES_DIR

            templates = TemplateRepository(LAB_TEMPLATES_DIR)
        reconstructed = reconstruct_branch(branch, canonical, templates)
    except (LookupError, KeyError, ValueError) as exc:
        errors.append(str(exc).strip("'") or "RECONSTRUCTION_MISMATCH")

    expected = reconstructed.model_dump(mode="json") if reconstructed else None
    observed = branch.model_dump(mode="json")
    mismatches = _diff(expected, observed) if expected is not None else []
    paths = [item.path for item in mismatches]
    if mismatches:
        errors.append("SEMANTIC_VERIFICATION_FAILED")
        errors.append("RECONSTRUCTION_MISMATCH")

    def select(prefix: str) -> list[SemanticMismatch]:
        return [item for item in mismatches if item.path.startswith(prefix)]

    requested_observed = [
        {"variable_id": item.variable_id, "requested_value": item.requested_value}
        for item in branch.branch_definition.mutations
        if item.requested_by in {"public_user", "curated_template"}
    ]
    requested_expected = (
        []
        if reconstructed is None
        else [
            {"variable_id": item.variable_id, "requested_value": item.requested_value}
            for item in reconstructed.branch_definition.mutations
            if item.requested_by in {"public_user", "curated_template"}
        ]
    )
    return BranchSemanticConformanceResult(
        status="unavailable" if reconstructed is None else "failed" if mismatches else "passed",
        branch_semantic_id=branch.branch_semantic_id,
        submitted_artifact_id=branch.branch_artifact_id,
        reconstructed_artifact_id=reconstructed.branch_artifact_id if reconstructed else None,
        canonical_parent=canonical.public_episode_id,
        engine_version=branch.engine_version,
        variable_registry_version=branch.branch_definition.variable_registry_version,
        template_registry_version=branch.branch_definition.template_registry_version,
        disclosure_policy_version=branch.branch_definition.disclosure_policy_version,
        semantic_verifier_id=SEMANTIC_VERIFIER_ID,
        semantic_verifier_version=SEMANTIC_VERIFIER_VERSION,
        semantic_verifier_bundle_digest=semantic_verifier_digest,
        authority_digest_comparison=authority_comparison,
        normalized_mutation_comparison={"expected": requested_expected, "observed": requested_observed},
        expected_vs_observed_propagated_state=select("$.stage_groups")
        + select("$.evidence_state")
        + select("$.action_comparison"),
        expected_vs_observed_records=select("$.branch_records"),
        expected_vs_observed_findings=select("$.constitutional_findings"),
        expected_vs_observed_comparison=select("$.canonical_comparison"),
        expected_vs_observed_disclosure=select("$.disclosure_manifest"),
        expected_root_digest=reconstructed.branch_root_digest if reconstructed else None,
        observed_root_digest=branch.branch_root_digest,
        mismatch_paths=paths,
        errors=errors,
        warnings=warnings,
        limitations=[
            "Semantic conformance proves equality to the registered deterministic engine and exact authority content.",
            "It does not establish empirical truth, institutional legitimacy, authorization, or execution.",
        ],
        verifier_version=SEMANTIC_VERIFIER_VERSION,
        verified_at=verification_time,
        verification_performed_at=verification_time,
        deterministic_evidence_timestamp=_deterministic_evidence_timestamp(),
    )


def verify_branch(
    branch: CounterfactualBranchBundle,
    canonical: PublicEpisodeBundle,
    templates: TemplateRepository | None = None,
) -> CompositeBranchVerificationResult:
    integrity = verify_branch_integrity(branch, canonical)
    semantic = verify_branch_semantic(branch, canonical, templates)
    overall: Literal["passed", "failed", "unavailable"] = (
        "passed"
        if integrity.status == semantic.status == "passed"
        else "unavailable"
        if semantic.status == "unavailable"
        else "failed"
    )
    return CompositeBranchVerificationResult(
        integrity_result=integrity,
        semantic_conformance_result=semantic,
        overall_status=overall,
        overall_interpretation=(
            "Integrity consistency and official semantic reconstruction both passed."
            if overall == "passed"
            else "The artifact is not fully verified; inspect both verification layers."
        ),
        evidence_references=[
            canonical.public_episode_id,
            canonical.integrity_manifest.bundle_digest,
            branch.branch_artifact_id,
        ],
        limitations=[
            "Composite verification is not truth, legitimacy, authorization, execution, or external certification."
        ],
    )


def clone_for_adversarial_test(branch: CounterfactualBranchBundle) -> CounterfactualBranchBundle:
    return CounterfactualBranchBundle.model_validate(deepcopy(branch.model_dump(mode="json")))

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aegis_lab.config import OperatingMode
from aegis_lab.laboratory.authorities import (
    ENGINE_VERSION,
    SEMANTIC_VERIFIER_VERSION,
    authority_index,
    calculate_descriptor_digest,
    load_authority_registry,
    verify_authority_registry,
)
from aegis_lab.laboratory.branches import BranchEngine, BranchInvalidError
from aegis_lab.laboratory.compatibility_v041 import adapt_v041_branch
from aegis_lab.laboratory.metadata_policy import MetadataClaimReservedError, validate_claim_safe_text
from aegis_lab.laboratory.models import (
    BranchCreateRequest,
    MetadataProvenance,
    SemanticAuthorityType,
)
from aegis_lab.laboratory.templates import TemplateRepository
from aegis_lab.laboratory.verification import verify_branch, verify_branch_semantic

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ID = "lab-004-reviewer-denies"


@pytest.fixture()
def template_repository() -> TemplateRepository:
    return TemplateRepository(ROOT / "data" / "lab_templates")


@pytest.fixture()
def content_addressed_branch(bundle, template_repository):
    template = template_repository.get(TEMPLATE_ID)
    request = BranchCreateRequest(
        parent_public_episode_id=bundle.public_episode_id,
        parent_bundle_digest=bundle.integrity_manifest.bundle_digest,
        template_id=template.template_id,
    )
    return BranchEngine().build(
        request,
        bundle,
        template_mutations=template.approved_mutations,
        template_title=template.title,
        template_question=template.question,
    )


def test_authority_registry_has_unique_identity_tuples():
    registry = load_authority_registry()
    assert len(authority_index(registry)) == len(registry.authorities)


@pytest.mark.parametrize("descriptor_index", range(20))
def test_every_registered_authority_digest_matches_content(descriptor_index):
    registry = load_authority_registry()
    descriptor = registry.authorities[descriptor_index]
    assert calculate_descriptor_digest(descriptor) == descriptor.content_digest


@pytest.mark.parametrize(
    "authority_type",
    [
        SemanticAuthorityType.BRANCH_ENGINE_BUNDLE,
        SemanticAuthorityType.SEMANTIC_VERIFIER_BUNDLE,
        SemanticAuthorityType.SCENARIO_VARIABLE_REGISTRY,
        SemanticAuthorityType.BRANCH_TEMPLATE_REGISTRY,
        SemanticAuthorityType.SELECTED_BRANCH_TEMPLATE,
        SemanticAuthorityType.CONSTITUTIONAL_INVARIANT_REGISTRY,
        SemanticAuthorityType.BRANCH_DISCLOSURE_POLICY,
        SemanticAuthorityType.CANONICAL_SERIALIZATION_POLICY,
        SemanticAuthorityType.CANONICAL_PARENT_BUNDLE,
    ],
)
def test_required_authority_type_is_registered(authority_type):
    assert any(item.authority_type is authority_type for item in load_authority_registry().authorities)


@pytest.mark.parametrize(
    "field",
    [
        "branch_engine_id",
        "branch_engine_version",
        "branch_engine_bundle_digest",
        "scenario_variable_registry_id",
        "variable_registry_version",
        "scenario_variable_registry_digest",
        "branch_template_registry_id",
        "template_registry_version",
        "branch_template_registry_digest",
        "selected_template_id",
        "selected_template_digest",
        "constitutional_invariant_registry_id",
        "constitutional_invariant_registry_version",
        "constitutional_invariant_registry_digest",
        "disclosure_policy_digest",
        "canonical_serialization_policy_digest",
    ],
)
def test_branch_definition_binds_required_authority_field(content_addressed_branch, field):
    assert getattr(content_addressed_branch.branch_definition, field)


@pytest.mark.parametrize(
    "authority_type",
    [
        SemanticAuthorityType.BRANCH_ENGINE_BUNDLE,
        SemanticAuthorityType.SCENARIO_VARIABLE_REGISTRY,
        SemanticAuthorityType.BRANCH_TEMPLATE_REGISTRY,
        SemanticAuthorityType.SELECTED_BRANCH_TEMPLATE,
        SemanticAuthorityType.CONSTITUTIONAL_INVARIANT_REGISTRY,
        SemanticAuthorityType.BRANCH_DISCLOSURE_POLICY,
        SemanticAuthorityType.CANONICAL_SERIALIZATION_POLICY,
        SemanticAuthorityType.CANONICAL_PARENT_BUNDLE,
    ],
)
def test_every_branch_authority_digest_spoof_fails_closed(
    bundle,
    content_addressed_branch,
    authority_type,
):
    branch = content_addressed_branch.model_copy(deep=True)
    binding = next(item for item in branch.semantic_authority_bindings if item.authority_type is authority_type)
    binding.content_digest = "0" * 64
    result = verify_branch_semantic(branch, bundle)
    assert result.status == "unavailable"
    assert result.errors


@pytest.mark.parametrize("mode", list(OperatingMode))
def test_only_canonical_operating_modes_build(bundle, template_repository, mode):
    template = template_repository.get(TEMPLATE_ID)
    request = BranchCreateRequest(
        parent_public_episode_id=bundle.public_episode_id,
        parent_bundle_digest=bundle.integrity_manifest.bundle_digest,
        template_id=template.template_id,
    )
    branch = BranchEngine().build(
        request,
        bundle,
        template_mutations=template.approved_mutations,
        operating_mode=mode,
    )
    assert branch.operating_mode is mode


@pytest.mark.parametrize(
    "mode",
    ["production", "institutional", "authorized", "live_execution", "public-pilot"],
)
def test_noncanonical_operating_mode_fails_before_branch_creation(bundle, template_repository, mode):
    template = template_repository.get(TEMPLATE_ID)
    request = BranchCreateRequest(
        parent_public_episode_id=bundle.public_episode_id,
        parent_bundle_digest=bundle.integrity_manifest.bundle_digest,
        template_id=template.template_id,
    )
    with pytest.raises(BranchInvalidError, match="OPERATING_MODE_INVALID"):
        BranchEngine().build(request, bundle, template_mutations=template.approved_mutations, operating_mode=mode)


@pytest.mark.parametrize(
    "text",
    [
        "This is canonical",
        "Institutionally approved analysis",
        "A real authorization",
        "Live execution confirmed",
        "Production ready",
        "Security certified",
        "Officially signed",
        "This actually occurred",
    ],
)
def test_reserved_metadata_claim_is_rejected(text):
    with pytest.raises(MetadataClaimReservedError):
        validate_claim_safe_text(text)


@pytest.mark.parametrize("field", ["title", "purpose", "question", "optional_note"])
def test_user_metadata_is_labeled_unverified(bundle, template_repository, field):
    template = template_repository.get(TEMPLATE_ID)
    values = {field: f"bounded user {field}"}
    request = BranchCreateRequest(
        parent_public_episode_id=bundle.public_episode_id,
        parent_bundle_digest=bundle.integrity_manifest.bundle_digest,
        template_id=template.template_id,
        **values,
    )
    branch = BranchEngine().build(
        request,
        bundle,
        template_mutations=template.approved_mutations,
        template_title=template.title,
        template_question=template.question,
    )
    assert branch.metadata_provenance[field] is MetadataProvenance.USER_SUPPLIED_UNVERIFIED


def test_live_verification_time_is_not_artifact_generation_time(bundle, content_addressed_branch):
    result = verify_branch(content_addressed_branch, bundle)
    assert result.integrity_result.verification_performed_at != content_addressed_branch.artifact_generated_at
    assert (
        result.semantic_conformance_result.verification_performed_at != content_addressed_branch.artifact_generated_at
    )


@pytest.mark.parametrize("layer", ["integrity", "semantic"])
def test_live_verification_time_parses_as_utc(bundle, content_addressed_branch, layer):
    result = verify_branch(content_addressed_branch, bundle)
    value = (
        result.integrity_result.verification_performed_at
        if layer == "integrity"
        else result.semantic_conformance_result.verification_performed_at
    )
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo == UTC


def test_semantic_verifier_identity_is_reported(bundle, content_addressed_branch):
    result = verify_branch_semantic(content_addressed_branch, bundle)
    assert result.semantic_verifier_version == SEMANTIC_VERIFIER_VERSION
    assert result.engine_version == ENGINE_VERSION
    assert len(result.semantic_verifier_bundle_digest) == 64


def test_registry_verification_is_complete_and_green():
    results = verify_authority_registry()
    assert len(results) == 20
    assert {item["status"] for item in results} == {"passed"}


def test_v041_adapter_preserves_original_without_native_binding():
    source = {
        "branch_schema": "aegis.counterfactual_branch_bundle.v0.4.1",
        "branch_version": "0.4.1",
        "branch_semantic_id": "branch-sem-" + "1" * 24,
        "branch_artifact_id": "branch-art-" + "2" * 24,
        "parent_bundle_digest": "3" * 64,
        "extension": {"preserved": True},
    }
    before = deepcopy(source)
    view = adapt_v041_branch(source)
    assert source == before
    assert view.preserved_original == before
    assert view.native_content_addressed_authority_binding is False
    assert view.semantic_reconstruction_status == "compatibility_only"


def test_current_branch_contract_rejects_unknown_field(content_addressed_branch):
    value = content_addressed_branch.model_dump(mode="json")
    value["unknown_claim"] = "not allowed"
    with pytest.raises(ValidationError):
        type(content_addressed_branch).model_validate(value)

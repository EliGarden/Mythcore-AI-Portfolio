from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


CAPABILITY = "architecture.canonical.promote"
EXECUTOR = "sys.federation_os"
HANDLER = "handler:orchestrator:canonical-promotion:v1"

TERMINAL_STATES = {
    "completed",
    "failed_terminal",
    "expired",
    "revoked",
    "cancelled",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class NativePromotionAuthorizationExtension:
    """Authorization-Kernel-owned local permit state and signing boundary."""

    schema_version = 1

    def __init__(self, database_path: str | Path, *, clock=None, permit_ttl_seconds: int = 30) -> None:
        self.database_path = str(database_path)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.permit_ttl_seconds = permit_ttl_seconds
        self._lock = threading.RLock()
        self._signing_key = Ed25519PrivateKey.generate()
        self.key_id = "key:authorization-kernel:native-promotion:local-test:v1"
        self.connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS native_capabilities(
              capability_id TEXT PRIMARY KEY, profile_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS native_promotion_permits(
              permit_id TEXT PRIMARY KEY, authorization_id TEXT NOT NULL,
              decision_digest TEXT NOT NULL, permit_json TEXT NOT NULL,
              state TEXT NOT NULL, reservation_id TEXT, execution_id TEXT,
              promotion_request_id TEXT, lease_expires_at TEXT,
              durable_event_id TEXT, durable_receipt_json TEXT,
              terminal_outcome_json TEXT, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS native_permit_transitions(
              sequence INTEGER PRIMARY KEY AUTOINCREMENT, permit_id TEXT NOT NULL,
              execution_id TEXT, from_state TEXT, to_state TEXT NOT NULL,
              evidence_json TEXT NOT NULL, occurred_at TEXT NOT NULL);
            """
        )
        profile = {
            "capability": CAPABILITY,
            "operation": CAPABILITY,
            "executor": EXECUTOR,
            "handler": HANDLER,
            "required_authorization_class": "verified_governance_decision",
            "allowed_decision_classes": ["local_institutional_test_ratification"],
            "candidate_binding": "exact",
            "parameters": "exact_hash",
            "expected_current_version_binding": True,
            "reversibility": "compensable_append_only",
            "single_use": True,
            "reservation": "atomic_lease",
            "retry_policy": "same_execution_identity_until_terminal",
            "completion_evidence": "flower_garden_durable_receipt",
            "replay": "reject_after_completion",
            "production_readiness": False,
        }
        self.connection.execute(
            "INSERT OR REPLACE INTO native_capabilities VALUES (?,?)",
            (CAPABILITY, canonical_bytes(profile).decode()),
        )

    def close(self) -> None:
        self.connection.close()

    def public_key_bytes(self) -> bytes:
        return self._signing_key.public_key().public_bytes_raw()

    def _now(self) -> datetime:
        return self.clock()

    def _iso(self, value: datetime | None = None) -> str:
        return (value or self._now()).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _unsigned(value: dict[str, Any]) -> dict[str, Any]:
        return {key: item for key, item in value.items() if key != "signature"}

    def _sign(self, value: dict[str, Any]) -> dict[str, Any]:
        result = dict(value)
        result["signature"] = base64.b64encode(
            self._signing_key.sign(canonical_bytes(result))
        ).decode()
        return result

    def verify(self, permit: dict[str, Any]) -> None:
        try:
            self._signing_key.public_key().verify(
                base64.b64decode(str(permit["signature"])),
                canonical_bytes(self._unsigned(permit)),
            )
        except (InvalidSignature, ValueError, KeyError) as exc:
            raise ValueError("native promotion permit signature is invalid") from exc

    def issue(
        self,
        *,
        candidate: dict[str, Any],
        decision: dict[str, Any],
        verified_decision_digest: str,
        expected_current_graph_id: str | None,
        parameters: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        suffix = digest(
            {
                "candidate": candidate["content_hash"],
                "decision": verified_decision_digest,
                "parameters": parameters,
                "expected": expected_current_graph_id,
            }
        )[:24]
        authorization_id = f"authorization:native-promotion:{suffix}"
        permit_id = f"permit:native-promotion:{suffix}"
        authorization = self._sign(
            {
                "authorization_id": authorization_id,
                "authorization_class": "verified_governance_decision",
                "decision_id": decision["decision_id"],
                "verified_governance_decision_digest": verified_decision_digest,
                "executor_system_id": EXECUTOR,
                "handler_id": HANDLER,
                "capability": CAPABILITY,
                "operation": CAPABILITY,
                "candidate_registration_id": candidate["registration_id"],
                "candidate_graph_id": candidate["graph_id"],
                "candidate_content_hash": candidate["content_hash"],
                "expected_current_ratified_graph_id": expected_current_graph_id,
                "parameters_hash": digest(parameters),
                "status": "active",
                "issued_at": self._iso(),
                "producer_system_id": "sys.luxian_governance_authorization_kernel",
                "key_id": self.key_id,
                "production_readiness": False,
            }
        )
        issued_at = self._now()
        permit = self._sign(
            {
                "protocol_id": "PRT-ORCH-NATIVE-PROMOTION-PERMIT-1",
                "protocol_version": "1.0.0",
                "permit_id": permit_id,
                "authorization_id": authorization_id,
                "decision_id": decision["decision_id"],
                "verified_governance_decision_digest": verified_decision_digest,
                "executor_system_id": EXECUTOR,
                "handler_id": HANDLER,
                "capability": CAPABILITY,
                "operation": CAPABILITY,
                "candidate_registration_id": candidate["registration_id"],
                "candidate_graph_id": candidate["graph_id"],
                "candidate_content_hash": candidate["content_hash"],
                "expected_current_ratified_graph_id": expected_current_graph_id,
                "parameters": parameters,
                "parameters_hash": digest(parameters),
                "reversibility_classification": "compensable_append_only",
                "issued_at": self._iso(issued_at),
                "expires_at": self._iso(issued_at + timedelta(seconds=self.permit_ttl_seconds)),
                "single_use": True,
                "reservation_required": True,
                "failure_retry_policy": "same_execution_identity_until_terminal",
                "state": "issued",
                "producer_system_id": "sys.luxian_governance_authorization_kernel",
                "key_id": self.key_id,
                "production_readiness": False,
            }
        )
        now = self._iso()
        with self._lock:
            self.connection.execute(
                """INSERT OR IGNORE INTO native_promotion_permits(
                   permit_id,authorization_id,decision_digest,permit_json,state,updated_at
                   ) VALUES (?,?,?,?,?,?)""",
                (
                    permit_id,
                    authorization_id,
                    verified_decision_digest,
                    canonical_bytes(permit).decode(),
                    "issued",
                    now,
                ),
            )
            self._transition(permit_id, None, None, "issued", {"authorization_id": authorization_id})
        return authorization, permit

    def _transition(
        self,
        permit_id: str,
        execution_id: str | None,
        from_state: str | None,
        to_state: str,
        evidence: dict[str, Any],
    ) -> None:
        self.connection.execute(
            "INSERT INTO native_permit_transitions(permit_id,execution_id,from_state,to_state,evidence_json,occurred_at) VALUES (?,?,?,?,?,?)",
            (
                permit_id,
                execution_id,
                from_state,
                to_state,
                canonical_bytes(evidence).decode(),
                self._iso(),
            ),
        )

    def status(self, permit_id: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM native_promotion_permits WHERE permit_id=?",
            (permit_id,),
        ).fetchone()
        if row is None:
            raise KeyError(permit_id)
        return dict(row)

    def reserve(
        self,
        permit: dict[str, Any],
        *,
        execution_id: str,
        promotion_request_id: str,
        candidate_graph_id: str,
        candidate_content_hash: str,
        expected_current_graph_id: str | None,
        parameters_hash: str,
        handler_id: str,
        lease_seconds: int = 30,
    ) -> dict[str, Any]:
        self.verify(permit)
        exact = {
            "candidate_graph_id": candidate_graph_id,
            "candidate_content_hash": candidate_content_hash,
            "expected_current_ratified_graph_id": expected_current_graph_id,
            "parameters_hash": parameters_hash,
            "handler_id": handler_id,
            "executor_system_id": EXECUTOR,
            "operation": CAPABILITY,
        }
        for field, expected in exact.items():
            if permit.get(field) != expected:
                raise ValueError(f"permit {field} mismatch")
        if self._now() >= datetime.fromisoformat(permit["expires_at"].replace("Z", "+00:00")):
            self._set_state(permit["permit_id"], execution_id, "expired", {"reason": "permit_expired"})
            raise TimeoutError("permit expired")
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                row = self.connection.execute(
                    "SELECT * FROM native_promotion_permits WHERE permit_id=?",
                    (permit["permit_id"],),
                ).fetchone()
                if row is None:
                    raise KeyError(permit["permit_id"])
                if row["state"] == "reserved" and row["execution_id"] == execution_id:
                    self.connection.commit()
                    return dict(row)
                if row["state"] != "issued":
                    raise RuntimeError(f"permit cannot be reserved from {row['state']}")
                reservation_id = f"reservation:{uuid.uuid4()}"
                lease = self._iso(self._now() + timedelta(seconds=lease_seconds))
                updated = self.connection.execute(
                    """UPDATE native_promotion_permits
                       SET state='reserved',reservation_id=?,execution_id=?,
                           promotion_request_id=?,lease_expires_at=?,updated_at=?
                       WHERE permit_id=? AND state='issued'""",
                    (
                        reservation_id,
                        execution_id,
                        promotion_request_id,
                        lease,
                        self._iso(),
                        permit["permit_id"],
                    ),
                )
                if updated.rowcount != 1:
                    raise RuntimeError("permit reservation conflict")
                self._transition(
                    permit["permit_id"],
                    execution_id,
                    "issued",
                    "reserved",
                    {
                        "reservation_id": reservation_id,
                        "promotion_request_id": promotion_request_id,
                        "lease_expires_at": lease,
                    },
                )
                result = self.connection.execute(
                    "SELECT * FROM native_promotion_permits WHERE permit_id=?",
                    (permit["permit_id"],),
                ).fetchone()
                self.connection.commit()
                return dict(result)
            except Exception:
                self.connection.rollback()
                raise

    def _set_state(
        self,
        permit_id: str,
        execution_id: str,
        to_state: str,
        evidence: dict[str, Any],
        *,
        allowed: set[str] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                row = self.connection.execute(
                    "SELECT * FROM native_promotion_permits WHERE permit_id=?",
                    (permit_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(permit_id)
                if row["execution_id"] not in {None, execution_id}:
                    raise RuntimeError("execution identity mismatch")
                if allowed is not None and row["state"] not in allowed:
                    raise RuntimeError(f"invalid transition {row['state']} -> {to_state}")
                self.connection.execute(
                    "UPDATE native_promotion_permits SET state=?,updated_at=? WHERE permit_id=?",
                    (to_state, self._iso(), permit_id),
                )
                self._transition(permit_id, execution_id, row["state"], to_state, evidence)
                updated = self.connection.execute(
                    "SELECT * FROM native_promotion_permits WHERE permit_id=?",
                    (permit_id,),
                ).fetchone()
                self.connection.commit()
                return dict(updated)
            except Exception:
                self.connection.rollback()
                raise

    def records_constructed(self, permit_id: str, execution_id: str, bundle_digest: str) -> dict[str, Any]:
        return self._set_state(
            permit_id,
            execution_id,
            "promotion_records_constructed",
            {"bundle_digest": bundle_digest},
            allowed={"reserved", "failed_retryable"},
        )

    def start_execution(self, permit_id: str, execution_id: str) -> dict[str, Any]:
        return self._set_state(
            permit_id,
            execution_id,
            "execution_started",
            {},
            allowed={"promotion_records_constructed"},
        )

    def durable_commit_pending(self, permit_id: str, execution_id: str, event_id: str) -> dict[str, Any]:
        return self._set_state(
            permit_id,
            execution_id,
            "durable_commit_pending",
            {"event_id": event_id},
            allowed={"execution_started"},
        )

    def confirm_durable_commit(
        self,
        permit_id: str,
        execution_id: str,
        *,
        event_id: str,
        receipt: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            self.connection.execute(
                "UPDATE native_promotion_permits SET durable_event_id=?,durable_receipt_json=? WHERE permit_id=?",
                (event_id, canonical_bytes(receipt).decode(), permit_id),
            )
        return self._set_state(
            permit_id,
            execution_id,
            "durable_commit_confirmed",
            {"event_id": event_id, "receipt_digest": digest(receipt)},
            allowed={"durable_commit_pending", "execution_started"},
        )

    def complete(self, permit_id: str, execution_id: str, outcome: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.connection.execute(
                "UPDATE native_promotion_permits SET terminal_outcome_json=? WHERE permit_id=?",
                (canonical_bytes(outcome).decode(), permit_id),
            )
        return self._set_state(
            permit_id,
            execution_id,
            "completed",
            outcome,
            allowed={"durable_commit_confirmed"},
        )

    def fail(
        self,
        permit_id: str,
        execution_id: str,
        *,
        classification: str,
        code: str,
        retryable: bool,
    ) -> dict[str, Any]:
        if classification not in {"failed_retryable", "failed_compensable", "failed_terminal"}:
            raise ValueError("invalid failure classification")
        return self._set_state(
            permit_id,
            execution_id,
            classification,
            {"code": code, "retryable": retryable},
            allowed={
                "reserved",
                "promotion_records_constructed",
                "execution_started",
                "durable_commit_pending",
            },
        )

    def recover_expired_lease(
        self,
        permit_id: str,
        *,
        execution_id: str,
        operator_identity: str,
    ) -> dict[str, Any]:
        row = self.status(permit_id)
        lease = row.get("lease_expires_at")
        if row["state"] != "reserved" or not lease:
            raise RuntimeError("permit has no recoverable reservation")
        if self._now() < datetime.fromisoformat(lease.replace("Z", "+00:00")):
            raise RuntimeError("reservation lease is still active")
        if row["execution_id"] != execution_id:
            raise RuntimeError("recovery must preserve execution identity")
        return self._set_state(
            permit_id,
            execution_id,
            "failed_retryable",
            {"operator_identity": operator_identity, "reason": "expired_lease"},
            allowed={"reserved"},
        )

    def revoke(self, permit_id: str, reason: str) -> dict[str, Any]:
        row = self.status(permit_id)
        if row["state"] == "completed":
            return {**row, "post_execution_revocation_recorded": True, "history_erased": False}
        return self._set_state(
            permit_id,
            row["execution_id"] or "revocation",
            "revoked",
            {"reason": reason},
            allowed={row["state"]},
        )

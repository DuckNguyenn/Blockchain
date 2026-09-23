from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def verify_sha256(payload: dict[str, Any]) -> bool:
    stored_hash = payload.get("log_sha256")
    if not isinstance(stored_hash, str):
        return False
    unsigned_payload = {
        key: value for key, value in payload.items() if key != "log_sha256"
    }
    return stored_hash == sha256_hex(unsigned_payload)


def write_incident(
    incident: dict[str, Any],
    output_dir: Path,
    evidence: bytes | None = None,
) -> tuple[Path, Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    incident_path = output_dir / f"{incident['incident_id']}.json"
    incident_path.write_text(
        json.dumps(incident, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    evidence_path = None
    if evidence is not None:
        evidence_dir = output_dir / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / f"{incident['incident_id']}.jpg"
        evidence_path.write_bytes(evidence)

    return incident_path, evidence_path

"""Send the samples of an approved NMDC submission sample set to EMSL's LIMS.

EMSL tracks every physical sample it receives in a LIMS (an L7|ESP instance). EMSL's own sample
submission portal registers samples there by POSTing them, one at a time, to EMSL's LIMS interface
API. This module does the same for NMDC submissions headed to EMSL, so those samples show up in
EMSL's sample tracking without being re-entered by hand.

Wire contract of the LIMS interface API (``POST {settings.lims_gateway_url}/sample``):
  * one request per sample, JSON body as built by ``build_payload``;
  * the body must contain ``esp_username``, ``esp_token`` (the LIMS service-account credentials),
    ``sample_type``, ``project_id``, ``project_uuid``, ``shipment_uuid``,
    ``shipment_tracking_number`` and ``sample_data``; a missing key is rejected with HTTP 400;
  * the LIMS upserts samples (matched by sample name + project), so re-sending the same sample
    updates it rather than creating a duplicate. Retrying is therefore safe;
  * a successful response is ``{"entity_id": ..., "entity_url": ...}``.

How each field is filled from NMDC data:
  * ``project_id`` -- ``multi_omics_form.studyNumber``, the 5-digit EMSL proposal number.
  * ``project_uuid`` -- looked up from ``project_id`` via ``emsl.project_directory``.
  * ``shipment_uuid`` / ``shipment_name`` -- the sample set's id and name.
  * ``shipment_tracking_number`` -- NMDC does not collect one, so it is sent as an empty string.
  * ``sample_type`` -- derived from the environmental-package slot the sample lives in, via
    ``SLOT_TO_SAMPLE_TYPE``.
  * ``sample_data`` -- the sample row itself, with ``samp_name`` renamed to ``sample_name``.

See docs/lims_export.md for the full description.
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from nmdc_server import models
from nmdc_server.config import settings
from nmdc_server.emsl.project_directory import get_project_directory
from nmdc_server.logger import get_logger
from nmdc_server.models import ENVIRONMENTAL_DATA_SLOTS

logger = get_logger(__name__)

# Only environmental-package slots hold physical samples. Submissions also carry companion tabs in
# sample_data["data"] -- notably `emsl_data` (analysis_type, shipping, storage temperature) and
# `jgi_mg_data` -- whose rows are keyed by samp_name but describe an existing sample rather than
# being samples themselves. Sending them would create bogus LIMS samples, so restrict to the same
# slot list SubmissionSampleSet.sample_count uses.
_ENV_SLOTS = set(ENVIRONMENTAL_DATA_SLOTS)

# ---------------------------------------------------------------------------
# Environmental-package slot -> LIMS sample type.
#
# NMDC stores samples under `sample_data["data"][<slot>]`, where <slot> is an environmental-package
# key (see models.ENVIRONMENTAL_DATA_SLOTS). The LIMS requires every sample to have a `sample_type`
# that is already defined in the LIMS; each type has its own set of metadata fields.
#
# A sample whose type is not defined in the LIMS cannot be created: the LIMS answers with an HTTP
# 500 after several internal retries. EMSL's own portal therefore never sends samples of an unknown
# type, and neither do we -- slots without a mapping below are skipped and logged.
# ---------------------------------------------------------------------------

# Sample types currently defined in EMSL's LIMS. Adding a type here does not create it in the LIMS;
# EMSL must define it first.
LIMS_SAMPLE_TYPES: set[str] = {
    "aerosol-arm",
    "aerosol",
    "soil",
    "monet-soil",
    "sediment",
    "plant",
    "culture-environmental",
    "terraform",
    "field-deployed-terraform",
    "pure-culture",
    "mixed-culture",
    "commercially-purchased",
    "synthesized-material",
    "water",
    "other-undescribed",
    "misc-envs",
}

# NMDC environmental packages are generic MIxS packages, so each maps to EMSL's generic sample type
# rather than to EMSL's program-specific variants (`monet-soil` is for EMSL's MONet soil program and
# `aerosol-arm` for the ARM atmospheric program; both require fields NMDC does not collect).
# `misc-envs` is a sample type EMSL added specifically for NMDC's misc_envs_data package.
# Packages not listed here (e.g. host_associated_data, built_env_data) have no matching EMSL sample
# type and are skipped.
SLOT_TO_SAMPLE_TYPE: dict[str, str] = {
    "soil_data": "soil",
    "water_data": "water",
    "sediment_data": "sediment",
    "plant_associated_data": "plant",
    "air_data": "aerosol",
    "misc_envs_data": "misc-envs",
}


def slot_to_sample_type(slot: str) -> str | None:
    """Resolve an NMDC environmental-package slot to a LIMS sample type, or None.

    Returns None (and logs) when the slot has no mapping, or maps to a type not defined in the
    LIMS, so the caller skips the slot instead of sending samples the LIMS would reject.
    """
    slug = SLOT_TO_SAMPLE_TYPE.get(slot)
    if slug is None:
        logger.warning("No LIMS sample-type mapping for slot %r; skipping", slot)
        return None
    if slug not in LIMS_SAMPLE_TYPES:
        logger.warning(
            "Mapped sample type %r for slot %r is not defined in the LIMS; skipping", slug, slot
        )
        return None
    return slug


class LimsExportError(Exception):
    """Raised when a sample set cannot be exported (e.g. its project UUID cannot be resolved)."""


def _resolve_project_uuid(project_id: str) -> str:
    """Resolve the EMSL proposal UUID for a proposal number via the configured project directory.

    If a real directory (nexus/pv2) cannot resolve the id, we ABORT rather than invent a UUID:
    proceeding with a fabricated UUID would associate the samples with a project that does not
    exist in EMSL, turning a transient lookup failure into incorrect LIMS data. Only the offline
    `synthesize` backend (local testing) deliberately returns a deterministic placeholder.
    """
    project_uuid = get_project_directory().get_project_uuid(project_id)
    if project_uuid:
        return project_uuid
    if settings.project_directory_backend == "synthesize":
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"nmdc-emsl-project:{project_id}"))
    raise LimsExportError(
        f"Could not resolve an EMSL project UUID for project_id {project_id!r} "
        f"via the {settings.project_directory_backend!r} project directory; aborting export."
    )


def _tracking_number(sample_set: models.SubmissionSampleSet) -> str:
    """shipment_tracking_number. NMDC does not collect a tracking number.

    EMSL asked that no placeholder value be invented. The key is still required by the LIMS
    interface API (a missing key is rejected with HTTP 400), so it is sent as an empty string.
    """
    return ""


def build_payload(
    sample_set: models.SubmissionSampleSet,
    slot: str,
    row: dict[str, Any],
    *,
    project_id: str,
    project_uuid: str,
    sample_type: str,
) -> dict[str, Any] | None:
    """Build a single-sample wire payload from one NMDC sample row.

    ``project_id`` / ``project_uuid`` / ``sample_type`` are resolved once per sample set/slot by
    the caller. Returns None (and logs) if the row has no ``samp_name``: the LIMS uses the sample
    name to identify (and de-duplicate) samples, so a sample without one cannot be sent.
    """
    # The LIMS calls this field `sample_name`; the submission schema calls it `samp_name`.
    raw_name = row.get("samp_name")
    if raw_name is None or str(raw_name).strip() == "":
        logger.warning("Skipping sample in set %s slot %s: no samp_name", sample_set.id, slot)
        return None
    sample_name = str(raw_name).strip().lstrip("_")

    # Copy the row's metadata as-is (MIxS snake_case slots), swap samp_name -> sample_name.
    sample_data: dict[str, Any] = {k: v for k, v in row.items() if k != "samp_name"}
    sample_data["sample_name"] = sample_name

    return {
        "esp_token": settings.lims_esp_token,
        "esp_username": settings.lims_esp_username,
        "project_id": project_id,
        "project_uuid": project_uuid,
        "shipment_uuid": str(sample_set.id),
        "shipment_tracking_number": _tracking_number(sample_set),
        "sample_type": sample_type,
        "shipment_name": sample_set.name,
        "sample_data": sample_data,
    }


def _companion_metadata_by_name(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index non-environmental companion-tab rows (e.g. emsl_data, jgi_mg_data) by samp_name.

    These tabs carry per-sample metadata (EMSL: analysis_type, sample_shipped, emsl_store_temp;
    JGI: sequencing details) that belongs on the LIMS sample. They are keyed to the environmental
    samples by samp_name.
    """
    by_name: dict[str, dict[str, Any]] = {}
    for slot, rows in data.items():
        if slot in _ENV_SLOTS or not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("samp_name")
            if not name:
                continue
            merged = by_name.setdefault(str(name).strip().lstrip("_"), {})
            for k, v in row.items():
                if k == "samp_name":
                    continue
                merged.setdefault(k, v)  # first companion tab wins; env row still wins later
    return by_name


def build_lims_payloads(sample_set: models.SubmissionSampleSet) -> list[dict[str, Any]]:
    """Flatten a sample set into one wire payload per environmental sample.

    Only ENVIRONMENTAL_DATA_SLOTS produce samples; companion metadata tabs (emsl_data, jgi_mg_data,
    ...) are merged into each sample by samp_name rather than sent as their own (bogus) samples.
    """
    data = (
        sample_set.sample_data.get("data", {}) if isinstance(sample_set.sample_data, dict) else {}
    )
    # Resolve the proposal number/UUID once per sample set; it is the same for every sample.
    multi_omics = (
        sample_set.multi_omics_form if isinstance(sample_set.multi_omics_form, dict) else {}
    )
    project_id = str(multi_omics.get("studyNumber") or "").strip()

    # An EMSL-bound submission carries a 5-digit EMSL Proposal Number as studyNumber. Without one,
    # the sample set is not headed to EMSL — sending would produce empty-project_id payloads that
    # the receiver rejects per sample. Skip entirely (log) rather than send junk.
    if not re.fullmatch(r"\d{5}", project_id):
        logger.warning(
            "Sample set %s has no valid EMSL project number (studyNumber=%r); not exporting to LIMS",
            sample_set.id,
            project_id,
        )
        return []

    project_uuid = _resolve_project_uuid(project_id)

    companions = _companion_metadata_by_name(data)
    payloads: list[dict[str, Any]] = []
    for slot, rows in data.items():
        if slot not in _ENV_SLOTS or not isinstance(rows, list):
            continue
        # Skip the whole slot if the LIMS has no matching sample type.
        sample_type = slot_to_sample_type(slot)
        if sample_type is None:
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("samp_name")
            # Overlay companion metadata under the env row (env row wins on key conflicts).
            enriched = row
            if name:
                extra = companions.get(str(name).strip().lstrip("_"))
                if extra:
                    enriched = {**extra, **row}
            payload = build_payload(
                sample_set,
                slot,
                enriched,
                project_id=project_id,
                project_uuid=project_uuid,
                sample_type=sample_type,
            )
            if payload is not None:
                payloads.append(payload)
    return payloads


def _sample_url() -> str:
    return f"{settings.lims_gateway_url.rstrip('/')}/sample"


def _send_one_sample(
    client: httpx.Client,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None,
    max_retries: int,
) -> dict[str, Any]:
    """POST one sample payload to the LIMS, retrying on network/5xx errors.

    Returns a per-sample result dict with keys: sample_name, sample_type, status, and either
    entity_id/entity_url (on success) or error (on failure).
    """
    sample_name = payload["sample_data"]["sample_name"]
    last_error: str | None = None
    outcome: dict[str, Any] | None = None

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            # Bounded exponential backoff between retries (0.5s, 1s, 2s, ... capped 5s).
            time.sleep(min(0.5 * 2 ** (attempt - 2), 5.0))
        try:
            resp = client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as e:
            last_error = f"network error: {e}"
            logger.warning(
                "LIMS send %s attempt %d/%d failed: %s",
                sample_name,
                attempt,
                max_retries,
                last_error,
            )
            continue

        if resp.status_code == 200:
            try:
                body = resp.json()
            except ValueError:
                # 200 with a non-JSON body: treat as a failed, retryable attempt rather
                # than letting json() raise and abort the whole export.
                last_error = f"HTTP 200 with non-JSON body: {resp.text[:200]}"
                logger.warning(
                    "LIMS send %s attempt %d/%d: %s",
                    sample_name,
                    attempt,
                    max_retries,
                    last_error,
                )
                continue
            outcome = {
                "sample_name": sample_name,
                "sample_type": payload["sample_type"],
                "status": "ok",
                "entity_id": body.get("entity_id"),
                "entity_url": body.get("entity_url"),
                "attempts": attempt,
            }
            break

        # 4xx are deterministic (bad contract) — do not retry; 5xx retry.
        try:
            detail = resp.json().get("error")
        except Exception:
            detail = resp.text
        last_error = f"HTTP {resp.status_code}: {detail}"
        if 400 <= resp.status_code < 500:
            logger.warning("LIMS send %s rejected (no retry): %s", sample_name, last_error)
            break
        logger.warning(
            "LIMS send %s attempt %d/%d server error: %s",
            sample_name,
            attempt,
            max_retries,
            last_error,
        )

    if outcome is None:
        outcome = {
            "sample_name": sample_name,
            "sample_type": payload["sample_type"],
            "status": "error",
            "error": last_error or "unknown error",
        }
    return outcome


def send_sample_set_to_lims(
    sample_set: models.SubmissionSampleSet,
    *,
    max_retries: int = 5,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Send every sample in the set to the LIMS, one POST per sample.

    Awaits and checks each response; retries idempotently on network/5xx errors (the receiver
    upserts, so retry is safe). Returns a summary dict with per-sample results. Does NOT commit;
    the caller persists `sample_set.lims_export_results` / `lims_exported_at`.

    This is deliberately synchronous (blocking the request) rather than fire-and-forget so that
    per-sample failures are reported back to the caller and persisted.
    """
    url = _sample_url()
    payloads = build_lims_payloads(sample_set)
    results: list[dict[str, Any]] = []
    sent = 0
    failed = 0

    # By default the LIMS token is sent in the request body (the interface API's current contract).
    # With lims_auth_in_header enabled it is sent as an `Authorization: Bearer` header instead and
    # removed from the body. esp_username stays in the body either way.
    headers: dict[str, str] | None = None
    if settings.lims_auth_in_header:
        headers = {"Authorization": f"Bearer {settings.lims_esp_token}"}
        for payload in payloads:
            payload.pop("esp_token", None)

    with httpx.Client(timeout=timeout) as client:
        for payload in payloads:
            outcome = _send_one_sample(client, url, payload, headers, max_retries)
            if outcome["status"] == "ok":
                sent += 1
            else:
                failed += 1
            results.append(outcome)

    summary = {
        "sample_set_id": str(sample_set.id),
        "gateway_url": url,
        "total": len(payloads),
        "sent": sent,
        "failed": failed,
        "results": results,
        "exported_at": datetime.now(UTC).isoformat(),
    }
    logger.info(
        "LIMS export for sample set %s: %d/%d sent, %d failed",
        sample_set.id,
        sent,
        len(payloads),
        failed,
    )
    return summary

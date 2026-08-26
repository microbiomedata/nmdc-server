"""Export NMDC submission sample sets to the EMSL L7|ESP LIMS.

This is the NMDC-side reimplementation of "Hop 1" of the EMSL SMS portal's send-to-LIMS
flow (see the companion analysis doc `SMS-to-LIMS-metadata-flow.md`). It builds one wire
payload per sample and POSTs each to the L7 LIMS interface API (`{gateway}/lims/sample`),
which is unchanged from the SMS integration. Locally, the target is the bundled mock
receiver; in real environments it is the shared EMSL API gateway.

Design mirrors the observed receiver contract (`l7-interface-api/api.py`, `l7esp/info.py`):
  * one POST per sample, JSON body per `build_payload`;
  * the receiver upserts (dedup by `lims_id`, else `sample:{name}`+`project:{id}` tags), so
    re-sending is idempotent and safe to retry;
  * required-by-receiver fields: esp_username, esp_token, sample_type, project_id, sample_data;
    project_uuid / shipment_uuid / shipment_tracking_number are read positionally by the
    receiver and 400 if missing -> we always send them.

Field resolution (see docs/lims_export.md for the full writeup):
  * project_uuid           -- resolved from the EMSL project id (multi_omics_form.studyNumber) via the
                              configured project directory (Nexus today, PV2-swappable). Falls back to
                              a deterministic synthesized UUID only if the directory can't resolve it.
  * shipment_tracking_number -- NMDC captures none; sent empty (the receiver still reads the field, so
                              it must be present). Left off deliberately, not synthesized.
  * sample_type slug       -- NMDC environmental-package slot -> ESP sample-type key via
                              SLOT_TO_SAMPLE_TYPE; slots with no known ESP type are skipped, not sent.
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
from nmdc_server.logger import get_logger
from nmdc_server.models import ENVIRONMENTAL_DATA_SLOTS
from nmdc_server.project_directory import get_project_directory

logger = get_logger(__name__)

# Only environmental-package slots hold shippable samples. Real submissions also carry companion
# tabs in sample_data["data"] — notably `emsl_data` (EMSL logistics: analysis_type, shipping,
# store temp) and `jgi_mg_data` (JGI) — which ARE keyed by samp_name but are per-sample metadata,
# NOT separate samples. Sending them would create bogus, wrong-typed LIMS samples. Restrict to the
# model's canonical environmental-sample slot list (same set SubmissionSampleSet.sample_count uses).
_ENV_SLOTS = set(ENVIRONMENTAL_DATA_SLOTS)

# ---------------------------------------------------------------------------
# Environmental-package slot -> ESP sample-type slug.
#
# NMDC stores samples under `sample_data["data"][<slot>]`, where <slot> is a MIxS
# environmental-package key (see models.ENVIRONMENTAL_DATA_SLOTS). The LIMS `sample_type` must be
# an existing ESP sample-type key (a slug registered in
# lims-dev/content/monet/inventory/emsl_sample_types.yml).
#
# IMPORTANT (confirmed with the SMS author, 2026-08-24): the original SMS portal DELIBERATELY
# filters out any sample type that has no corresponding L7/ESP type — otherwise the receiver's
# Sample.create throws "sample can't be created", retries 5x, and finally returns a 500, spamming
# the logs. We mirror that: a slot only produces samples if it maps to a KNOWN ESP slug; unmapped
# slots are skipped (logged), never sent with an invented slug.
# ---------------------------------------------------------------------------

# ESP sample-type slugs that actually exist in the LIMS (from emsl_sample_types.yml).
VALID_ESP_SAMPLE_TYPES: set[str] = {
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
    "misc-envs",  # dedicated schema authored 2026-08-24 (analysisapi data/misc-envs) — deploy + reseed lims
}

# NMDC environmental-package slot -> ESP sample-type slug.
#
# Evidence-based (2026-08-24; confirm with EMSL): NMDC submits GENERIC MIxS packages, so each maps to
# EMSL's GENERIC AnalysisAPI schema, NOT the MONet/ARM-specific variants. Verified by comparing real
# NMDC sample fields against each SC Data schema's `required` list (sc-data-dev/schema/manifest):
#   soil_data  -> soil     (NMDC soil satisfies soil 9/11 required vs monet-soil only 11/26 — NMDC data
#                           lacks the MONet-experiment fields: infiltration, ecoregion, soil_type_meth,
#                           bulk_elect_conductivity, water_content, ...). NOTE: `soil` (not monet-soil)
#                           also means the interface-api's monet-soil-only analysis-API mirror does not
#                           fire — which is what was returning 500 on the monet-soil path.
#   water_data -> water    (8/15 required; gaps are shipment-logistics fields supplied later)
#   sediment_data -> sediment (8/11)
#   plant_associated_data -> plant (9/13)
#   air_data   -> aerosol  (generic; `aerosol-arm` is the ARM-program-specific schema)
#   misc_envs_data -> misc-envs (dedicated flat schema authored 2026-08-24; EMSL chose a real type over
#                     the other-undescribed catch-all. Requires deploy of analysisapi data/misc-envs +
#                     regen of the ESP type + reseed lims — until then this slug won't exist in LIMS.)
SLOT_TO_SAMPLE_TYPE: dict[str, str] = {
    "soil_data": "soil",
    "water_data": "water",
    "sediment_data": "sediment",
    "plant_associated_data": "plant",
    "air_data": "aerosol",
    "misc_envs_data": "misc-envs",  # dedicated schema (was other-undescribed catch-all) — EMSL chose B
}


def slot_to_sample_type(slot: str) -> str | None:
    """Resolve an NMDC environmental-package slot to a KNOWN ESP sample-type slug, or None.

    Returns None (and logs) when the slot has no mapping, or maps to a slug that does not exist in
    the LIMS — so the caller skips it rather than triggering a 500-storm (see module note).
    """
    slug = SLOT_TO_SAMPLE_TYPE.get(slot)
    if slug is None:
        logger.warning("No ESP sample-type mapping for slot %r; skipping (needs EMSL rule)", slot)
        return None
    if slug not in VALID_ESP_SAMPLE_TYPES:
        logger.warning("Mapped slug %r for slot %r is not a known ESP type; skipping", slug, slot)
        return None
    return slug


class LimsExportError(Exception):
    """Raised when a sample set cannot be exported (e.g. its project UUID cannot be resolved)."""


def _resolve_project_uuid(project_id: str) -> str:
    """Resolve the EMSL project UUID for a project id via the configured project directory.

    Today this hits the EMSL Nexus service (`/projects/lookup?q={id}` -> `[0].uuid`), the same
    registry the SMS portal and l7-interface-api receiver use. Swappable to PV2 later via config.

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
    """shipment_tracking_number. NMDC captures no tracking number.

    Per Makena (2026-08-24): "leave it off" — do NOT synthesize a fake value. We send an empty
    string because the receiver still reads the field positionally (missing -> 400). If/when the
    receiver is updated to make it optional, this can be omitted from the payload entirely.
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
    the caller. Returns None (and logs) if the row has no sample name — that sample is unshippable
    because ``sample_name`` is the receiver's description + dedup key.
    """
    # NMDC sample rows use the MIxS slot key `samp_name`; the LIMS wire/ESP field is `sample_name`.
    raw_name = row.get("samp_name") or row.get("sample_name")
    if raw_name is None or str(raw_name).strip() == "":
        logger.warning(
            "Skipping sample in set %s slot %s: no samp_name/sample_name", sample_set.id, slot
        )
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
            name = row.get("samp_name") or row.get("sample_name")
            if not name:
                continue
            merged = by_name.setdefault(str(name).strip().lstrip("_"), {})
            for k, v in row.items():
                if k in ("samp_name", "sample_name"):
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
    # Resolve project id/uuid ONCE per sample set (constant across all samples; avoids a project
    # directory / Nexus call per sample).
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
        # Skip whole slot if its ESP sample-type is unknown (mirrors SMS; avoids 500-storm).
        sample_type = slot_to_sample_type(slot)
        if sample_type is None:
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("samp_name") or row.get("sample_name")
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

    This is deliberately synchronous (blocking the request) rather than fire-and-forget: the
    original SMS portal fire-and-forgot and never surfaced failures — we fix that here.
    """
    url = _sample_url()
    payloads = build_lims_payloads(sample_set)
    results: list[dict[str, Any]] = []
    sent = 0
    failed = 0

    # Auth transport: by default the ESP token rides in the body (current contract). When
    # lims_auth_in_header is enabled (after the upstream header change lands), send it as an
    # Authorization: ****** instead and drop it from the body. esp_username stays in the body.
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

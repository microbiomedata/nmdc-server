# EMSL LIMS export (SMS → LIMS reimplementation)

NMDC-side reimplementation of the EMSL SMS portal's "send samples to the L7|ESP LIMS" step. When an
NMDC submission's sample set is approved for the user facility, its samples are pushed into the EMSL
LIMS via the unchanged `l7-interface-api` (`POST {gateway}/lims/sample`, one request per sample).

## Components

- `nmdc_server/lims_export.py` — `build_lims_payloads(sample_set)` and
  `send_sample_set_to_lims(sample_set)`. Flattens `sample_data["data"][slot]` rows into one wire
  payload each, POSTs via httpx, retries idempotently, returns a per-sample result summary.
- `POST /metadata_submission/sample_set/{id}/send-to-lims` (`nmdc_server/api.py`) — the manual
  "send to LIMS" button. Requires the sample set to be in `ApprovedHeld` status and the caller to be
  an owner/reviewer of the submission (or a site admin). Persists results to
  `submission_sample_set.lims_export_results` / `lims_exported_at`.
- Config (`nmdc_server/config.py`): `lims_gateway_url`, `lims_esp_username`, `lims_esp_token`,
  `lims_export_enabled` (env-prefixed `NMDC_`).

## Wire contract

Body per sample (mirrors the SMS portal / `l7-interface-api`):

```json
{
  "esp_token": "...", "esp_username": "nmdc-portal",
  "project_id": "61258", "project_uuid": "<uuid>",
  "shipment_uuid": "<sample_set id>", "shipment_tracking_number": "<...>",
  "sample_type": "monet-soil", "shipment_name": "<sample set name>",
  "sample_data": { "sample_name": "61258_2_C4", "...": "MIxS snake_case slots" }
}
```

The receiver upserts (dedup by `lims_id`, else `sample:{name}`+`project:{id}` tags), so re-sending is
idempotent — safe to retry. Response: `{"entity_id": "...", "entity_url": "..."}`.

## Field mapping

NMDC sample rows already use MIxS snake_case slot names that, after the receiver's
`field.replace('_',' ').title()`, match the ESP sample-type field names. The only rename needed is
`samp_name` → `sample_name`.

## Trigger / delivery

- Manual button (this endpoint), gated on `ApprovedHeld`.
- Automatic fire on the status transition is a documented follow-up (gate on a date cutoff +
  `is_test_submission is False`); the hook point is `update_submission_sample_set_status`. Not wired.

## Open gaps (confirm with EMSL before non-local use)

- `project_uuid` — NMDC has no EMSL project UUID; currently a deterministic UUID5 placeholder.
- `shipment_tracking_number` — NMDC captures none; currently `nmdc-sampleset:{id}` placeholder.
- `sample_type` slug — `SLOT_TO_SAMPLE_TYPE` is an assumption; verify each NMDC env package maps to the
  right ESP slug in `lims-dev/content/monet/inventory/emsl_sample_types.yml`.
- `project_id` — assumed to be `multi_omics_form.studyNumber` (the "EMSL ID"); confirm it resolves in
  Nexus as the numeric EMSL project id.

## Local end-to-end testing

A zero-dependency mock receiver and seed script live outside this repo at
`~/Dev/NMDC SMS to Lims Connection/local-ete/` (`mock_lims_receiver.py`, `seed_ete.py`). See
`FINDINGS-and-local-ETE.md` there for the full runbook and results.

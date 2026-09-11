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
- Config (`nmdc_server/config.py`, env-prefixed `NMDC_`): `lims_gateway_url`, `lims_esp_username`,
  `lims_esp_token`, `lims_export_enabled`, `lims_auth_in_header` (token in `Authorization` header vs
  body), `project_directory_backend` (`nexus` | `pv2` | `synthesize`), `nexus_base_url`.

## Wire contract

Body per sample (mirrors the SMS portal / `l7-interface-api`):

```json
{
  "esp_token": "...", "esp_username": "svcnmdcuser",
  "project_id": "61258", "project_uuid": "<uuid from Nexus>",
  "shipment_uuid": "<sample_set id>", "shipment_tracking_number": "",
  "sample_type": "soil", "shipment_name": "<sample set name>",
  "sample_data": { "sample_name": "61258_2_C4", "...": "MIxS snake_case slots" }
}
```

The receiver upserts (dedup by `lims_id`, else `sample:{name}`+`project:{id}` tags), so re-sending is
idempotent — safe to retry. Response: `{"entity_id": "...", "entity_url": "..."}`.

## Field mapping

NMDC sample rows already use MIxS snake_case slot names that, after the receiver's
`field.replace('_',' ').title()`, match the ESP sample-type field names. The only rename needed is
`samp_name` → `sample_name`.

- **Slot → sample type** (`SLOT_TO_SAMPLE_TYPE`): `soil_data`→`soil`, `water_data`→`water`,
  `sediment_data`→`sediment`, `plant_associated_data`→`plant`, `air_data`→`aerosol`,
  `misc_envs_data`→`misc-envs`. Slots with no known ESP type (or non-environmental companion tabs like
  `emsl_data`/`jgi_mg_data`) are **skipped**, not sent — mirrors EMSL SMS and avoids receiver 500-storms.
- **Companion metadata**: `emsl_data` (and other non-env tabs) are merged into each environmental
  sample by `samp_name` (EMSL logistics fields like `analysis_type` ride along), not sent as samples.
- **project_uuid**: resolved from `studyNumber` (the 5-digit EMSL Proposal Number) via the project
  directory (`nexus` backend today). Sample sets without a valid 5-digit `studyNumber` are not
  EMSL-bound and are skipped.

## Trigger / delivery

- Manual button (this endpoint), gated on `ApprovedHeld`.
- Automatic fire on the status transition is a documented follow-up (gate on a date cutoff +
  `is_test_submission is False`); the hook point is `update_submission_sample_set_status`. Not wired.

## Resolved decisions / open confirmations

- `project_id` = `multi_omics_form.studyNumber` — confirmed: it's the 5-digit EMSL Proposal Number,
  resolves in Nexus. Sample sets without one are treated as not EMSL-bound and skipped.
- `project_uuid` — resolved from `project_id` via the project directory (`nexus` backend;
  `/projects/lookup?q={id}` → `[0].uuid`). Falls back to a deterministic synthesized UUID only if the
  directory can't resolve it. Switchable to PV2 later via `project_directory_backend`.
- `shipment_tracking_number` — NMDC captures none; sent empty (the receiver requires the field to be
  present). Not synthesized.
- `sample_type` slug mapping — evidence-based (NMDC generic MIxS → generic ESP type); confirm with EMSL,
  esp. `soil`→`soil` (not `monet-soil`) and `misc_envs`→`misc-envs` (a dedicated schema was authored).

## Local end-to-end testing

A zero-dependency mock receiver and seed script live outside this repo at
`~/Dev/NMDC SMS to Lims Connection/local-ete/` (`mock_lims_receiver.py`, `seed_ete.py`). See
`FINDINGS-and-local-ETE.md` there for the full runbook and results.

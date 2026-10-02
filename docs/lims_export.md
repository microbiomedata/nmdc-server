# EMSL LIMS export

EMSL (the Environmental Molecular Sciences Laboratory user facility) tracks every physical sample it
receives in a LIMS. When an NMDC submission's sample set is approved for EMSL, its samples can be
sent to that LIMS so EMSL does not have to re-enter them by hand. Samples are sent through EMSL's
LIMS interface API (`POST {lims_gateway_url}/sample`), one request per sample.

All EMSL-specific code lives in the `nmdc_server/emsl/` package.

## Components

- `nmdc_server/emsl/lims_export.py` — `build_lims_payloads(sample_set)` and
  `send_sample_set_to_lims(sample_set)`. Flattens `sample_data["data"][slot]` rows into one request
  body per sample, POSTs each with httpx, retries on network errors and 5xx responses, and returns a
  per-sample result summary.
- `nmdc_server/emsl/project_directory.py` — looks up the EMSL proposal UUID for the 5-digit EMSL
  proposal number the submitter entered (`multi_omics_form.studyNumber`). The LIMS requires the
  UUID; NMDC does not store it.
- `POST /metadata_submission/sample_set/{id}/send-to-lims` (`nmdc_server/api.py`) — the manual
  "send to LIMS" action. Requires the sample set to be in `ApprovedHeld` status, to carry the `emsl`
  template, and not to belong to a test submission; the caller must be an owner/reviewer of the
  submission or a site admin. Persists results to `submission_sample_set.lims_export_results` and
  `lims_exported_at`.
- Config (`nmdc_server/config.py`, env-prefixed `NMDC_`):
  - `lims_gateway_url`, `lims_esp_username`, `lims_esp_token` — LIMS interface API base URL and the
    LIMS service-account credentials EMSL provisions for NMDC. The endpoint returns 503 until all
    three are set.
  - `lims_export_enabled` — master switch (503 when False).
  - `lims_auth_in_header` — send the token as an `Authorization: Bearer` header instead of in the
    request body. Leave False until EMSL's LIMS interface API accepts the header.
  - `project_directory_backend` (`nexus` | `pv2` | `synthesize`) and `nexus_base_url` — where proposal
    UUIDs are looked up. `synthesize` returns a placeholder UUID and is for offline local
    development only.

## Request body

One request per sample:

```json
{
  "esp_token": "<service-account token>", "esp_username": "<service-account username>",
  "project_id": "61258", "project_uuid": "<proposal UUID>",
  "shipment_uuid": "<sample set id>", "shipment_tracking_number": "",
  "sample_type": "soil", "shipment_name": "<sample set name>",
  "sample_data": { "sample_name": "61258_2_C4", "...": "the sample row's other slots" }
}
```

Every key above must be present; the API rejects a request with a missing key (HTTP 400). The LIMS
upserts samples (matched by sample name and project), so re-sending a sample updates it instead of
creating a duplicate, which makes retries safe. A successful response is
`{"entity_id": "...", "entity_url": "..."}`.

## Field mapping

- **`sample_data`** — the sample row as stored in the submission, with `samp_name` renamed to
  `sample_name` (the LIMS field name). Slot names are otherwise passed through unchanged; the LIMS
  sample types use the same MIxS slot names.
- **`sample_type`** — derived from the environmental-package slot the sample lives in
  (`SLOT_TO_SAMPLE_TYPE`): `soil_data`→`soil`, `water_data`→`water`, `sediment_data`→`sediment`,
  `plant_associated_data`→`plant`, `air_data`→`aerosol`, `misc_envs_data`→`misc-envs`. NMDC packages
  are generic MIxS packages, so they map to EMSL's generic sample types rather than EMSL's
  program-specific variants (e.g. `monet-soil`). Slots with no matching LIMS sample type are
  skipped: the LIMS cannot create a sample of an undefined type.
- **Companion tabs** — rows in non-environmental tabs such as `emsl_data` and `jgi_mg_data` describe
  existing samples (e.g. `analysis_type`). They are merged into the matching environmental sample by
  `samp_name`, not sent as samples of their own.
- **`project_id` / `project_uuid`** — `project_id` is `multi_omics_form.studyNumber`, the 5-digit EMSL
  proposal number. `project_uuid` is looked up from it; if the lookup cannot find an exact match,
  the export is aborted (HTTP 502) rather than sending samples with a wrong or invented UUID. Sample
  sets without a valid 5-digit `studyNumber` are not EMSL-bound and send nothing.
- **`shipment_tracking_number`** — NMDC does not collect one; sent as an empty string.

## Trigger

- Manual: the endpoint above.
- Automatic sending on the transition to `ApprovedHeld` is not implemented. If added, the hook point
  is `update_submission_sample_set_status`, and it should skip test submissions.

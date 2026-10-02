"""Integrations with EMSL (the Environmental Molecular Sciences Laboratory user facility).

Code in this package talks to EMSL-operated systems on behalf of NMDC submissions that are bound
for EMSL. It is isolated here because it depends on EMSL services and conventions that most NMDC
developers will not otherwise need to know about:

  * ``project_directory`` -- looks up EMSL proposal metadata (e.g. the proposal UUID) from EMSL's
    project registry, given the 5-digit EMSL proposal number a submitter enters as
    ``multi_omics_form.studyNumber``.
  * ``lims_export`` -- sends the samples of an approved submission sample set to EMSL's sample
    tracking system (an L7|ESP LIMS), one HTTP request per sample.

See ``docs/lims_export.md`` for the end-to-end description.
"""

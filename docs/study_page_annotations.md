# Study Page

This document describes how the study page is populated in the data portal by describing which slots are used, and how they are interpreted by the data portal.

## __Full Study Page__

![Full study page](./images/study_page_1_annotated.png)

### __Explanations__

1. This comes directly from the `title` slot of `study` class instances
2. `description` slot of `study` class instances
3.  `profile_image_url` slot of the `principal_investigator` slot (type `PersonValue`) of `study` class instances OR the first entry in the `study_image` slot of `study` class instances. During ingest, the image is downloaded from the specified URI and stored as a `BLOB` in Postgres.
4. `name` slot of `principal_investigator`
5. `orcid` slot of `principal_investigator`, URL prefix added or expanded by `nmdc-server` in `web/src/components/InvestigatorBio.vue::getOrcid`
6. `websites` slot of `principal_investigator`
7. `name` slot of `applies_to_person` slot of all entries in `has_credit_associations`
8. `has_raw_value` of `doi` slot of `study`. Modified during ingest in `nmdc_server/ingest/study.py::transform_doi` to only include to DOI, not the full URL.
9. `id` of `study`
10. `funding_sources` of `study`
11. Computed at search time by `nmdc-server`
12. `gold_study_identifiers` and `id`, if the study has a gold-prefixed `id`
13. `doi` of `study` (see number 8 for more details) in conjunction with [citation-js](https://github.com/citation-js/citation-js).
14. `publications` slot of `study`, in conjunction with `citation-js`. As with DOIs, we pass strings fount in the `publications` slot through `nmdc_server/ingest/study.py::transform_doi`.
15. Computed at search time by `nmdc-server`

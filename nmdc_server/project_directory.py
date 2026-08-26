"""Resolve an EMSL project id to its project UUID (and type) for LIMS export.

NMDC submissions carry the EMSL Proposal Number as ``multi_omics_form.studyNumber`` (a 5-digit
id). The LIMS wire contract needs the corresponding project **UUID** (and, for the receiver's
workgroup naming, the project **type** + PI). NMDC does not store these — they live in EMSL's
project registry. This module fetches them.

Backends (selected by ``settings.project_directory_backend``):
  * ``nexus``      -- the current EMSL Nexus service. ``GET /nexus/projects/lookup?q={id}`` returns
                      a list whose first element has ``uuid`` and ``project_type``. This is the same
                      registry the SMS portal and the l7-interface-api receiver use today.
  * ``pv2``        -- the Nexus replacement (sc-project ``project_tracking.projects``, which pairs
                      ``project_id`` <-> ``project_uuid``). NOT YET IMPLEMENTED — no production PV2
                      exists yet. When PV2 is production-ready, implement ``Pv2ProjectDirectory`` and
                      flip the config; call sites do not change.
  * ``synthesize`` -- offline fallback for local testing with no network: a deterministic UUID5.

Nexus is being deprecated (~1 year). The abstraction here is deliberate so the eventual Nexus->PV2
switch is a config change plus one new class, not a change to lims_export.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any, Optional, Protocol

import httpx

from nmdc_server.config import settings
from nmdc_server.logger import get_logger

logger = get_logger(__name__)


class ProjectDirectory(Protocol):
    """Resolves an EMSL project id to project metadata."""

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """Return a normalized project dict ({"uuid", "project_type", "id", ...}) or None."""

    def get_project_uuid(self, project_id: str) -> Optional[str]:
        """Return the project UUID for the given EMSL project id, or None if not resolvable."""


class NexusProjectDirectory:
    """EMSL Nexus service backend."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        if not project_id:
            return None
        url = f"{self.base_url}/projects/lookup"
        try:
            resp = httpx.get(url, params={"q": project_id}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.warning("Nexus project lookup failed for %s: %s", project_id, e)
            return None
        if not isinstance(data, list) or not data:
            logger.warning("Nexus project lookup for %s returned no matches", project_id)
            return None
        # The lookup is a fuzzy search; prefer an exact id match, else take the first result.
        match = next((p for p in data if str(p.get("id")) == str(project_id)), data[0])
        return {
            "id": str(match.get("id", project_id)),
            "uuid": match.get("uuid"),
            "project_type": match.get("project_type"),
            "title": match.get("title"),
            "raw": match,
        }

    def get_project_uuid(self, project_id: str) -> Optional[str]:
        project = self.get_project(project_id)
        return project.get("uuid") if project else None


class SynthesizeProjectDirectory:
    """Offline fallback: deterministic placeholder UUID (no real registry)."""

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        return {"id": project_id, "uuid": self.get_project_uuid(project_id), "project_type": None}

    def get_project_uuid(self, project_id: str) -> Optional[str]:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"nmdc-emsl-project:{project_id}"))


@lru_cache(maxsize=1)
def get_project_directory() -> ProjectDirectory:
    """Return the configured project-directory backend (cached singleton)."""
    backend = settings.project_directory_backend
    if backend == "nexus":
        return NexusProjectDirectory(settings.nexus_base_url)
    if backend == "synthesize":
        return SynthesizeProjectDirectory()
    if backend == "pv2":
        raise NotImplementedError(
            "PV2 project directory backend is not implemented yet (no production PV2). "
            "Set project_directory_backend to 'nexus' for now."
        )
    raise ValueError(f"Unknown project_directory_backend: {backend!r}")

"""Look up EMSL proposal metadata from an EMSL proposal number.

Submitters enter their 5-digit EMSL proposal number as ``multi_omics_form.studyNumber``. EMSL's
LIMS additionally requires the proposal's UUID, which NMDC does not store; it lives in EMSL's
project registry. This module fetches it.

Backends (selected by ``settings.project_directory_backend``):
  * ``nexus``      -- Nexus, EMSL's current user/proposal system. ``GET {nexus_base_url}/projects/
                      lookup?q={id}`` returns a list of matching proposals with ``id`` and ``uuid``.
  * ``pv2``        -- placeholder for the system EMSL is building to replace Nexus. Not implemented;
                      when it exists, add a class here and change the setting. Callers do not change.
  * ``synthesize`` -- offline fallback for local development with no network access: returns a
                      deterministic placeholder UUID. Never use in a deployed environment.
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
        ...

    def get_project_uuid(self, project_id: str) -> Optional[str]:
        """Return the project UUID for the given EMSL project id, or None if not resolvable."""
        ...


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
        # The lookup is a fuzzy search and may return other proposals; only accept an exact id
        # match, otherwise the samples could be attached to the wrong proposal.
        match = next((p for p in data if str(p.get("id")) == str(project_id)), None)
        if match is None:
            logger.warning("Nexus project lookup for %s returned no exact match", project_id)
            return None
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

from datetime import datetime
from typing import List
from uuid import UUID

from nmdc_server.data_object_filters import DataObjectFilter
from nmdc_server.query import ConditionSchema
from nmdc_server.schemas import FileDownloadMetadata
from pydantic import ConfigDict


# schemas related to bulk download endpoints extracted
# into a standalone module to prevent circular imports
class BulkDownloadBase(FileDownloadMetadata):
    conditions: List[ConditionSchema] = []
    filter: List[DataObjectFilter] = []


class BulkDownload(BulkDownloadBase):
    id: UUID
    created: datetime
    model_config = ConfigDict(from_attributes=True)


class BulkDownloadCreate(BulkDownloadBase):
    pass

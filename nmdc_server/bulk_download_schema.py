from datetime import datetime
from typing import List
from uuid import UUID

from nmdc_server.data_object_filters import DataObjectFilter
from nmdc_server.query import ConditionSchema
from nmdc_server.schemas import FileDownloadMetadata


# schemas related to bulk download endpoints extracted
# into a standalone module to prevent circular imports
class BulkDownloadBase(FileDownloadMetadata):
    conditions: List[ConditionSchema] = []
    filter: List[DataObjectFilter] = []


class BulkDownload(BulkDownloadBase):
    id: UUID
    created: datetime

    class Config:
        orm_mode = True


class BulkDownloadCreate(BulkDownloadBase):
    pass

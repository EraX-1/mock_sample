import datetime

from pydantic import BaseModel, ConfigDict


class IndexedFile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    original_blob_name: str
    indexed_blob_name: str
    file_type: str
    index_type: str
    indexed_at: datetime.datetime


class SearchIndexType(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    folder_name: str
    display_order: int
    created_at: datetime.datetime

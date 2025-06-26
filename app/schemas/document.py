from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class DocumentCreate(BaseModel):
    content: str
    source: str
    category: str
    tool_name: Optional[str] = ""
    section: Optional[str] = ""
    chunk_index: Optional[int] = 0
    tool_rank: Optional[int] = 0

class DocumentResponse(BaseModel):
    id: str
    content: str
    source: str
    category: str
    tool_name: str
    section: str
    chunk_index: int
    tool_rank: int
    timestamp: datetime

class RefreshDataRequest(BaseModel):
    force_refresh: Optional[bool] = False

class RefreshDataResponse(BaseModel):
    status: str
    message: str
    documents_processed: int
    processing_time: float

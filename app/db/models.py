from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class DocumentModel(BaseModel):
    content: str
    source: str
    category: str
    tool_name: Optional[str] = ""
    section: Optional[str] = ""
    chunk_index: Optional[int] = 0
    tool_rank: Optional[int] = 0
    timestamp: Optional[datetime] = None
    vector: Optional[List[float]] = None

class SearchResult(BaseModel):
    content: str
    source: str
    category: str
    tool_name: str
    section: str
    chunk_index: int
    tool_rank: int
    certainty: float
    distance: float
    
class VectorSearchRequest(BaseModel):
    query_vector: List[float]
    limit: int = 5
    where_filter: Optional[Dict[str, Any]] = None

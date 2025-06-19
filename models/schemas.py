from typing import Any, Dict, List, Union
from pydantic import BaseModel

class SearchRequest(BaseModel):
    question: str

class SearchResponse(BaseModel):
    generated_query: str
    result_count: int
    results: Union[List[Dict[str, Any]], int]

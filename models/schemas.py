from typing import Any, Dict, List, Union
from pydantic import BaseModel

class SearchRequest(BaseModel):
    question: str

class SearchResponse(BaseModel):
    results: Union[List[Dict[str, Any]], int]

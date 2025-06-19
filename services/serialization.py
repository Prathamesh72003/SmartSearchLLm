# services/serialization.py
from bson import ObjectId
from typing import Any, Union

def serialize_bson(obj: Any) -> Any:
    """
    Recursively convert BSON types (ObjectId, etc.) into
    JSON-safe Python primitives.
    """
    # 1. ObjectId → str
    if isinstance(obj, ObjectId):
        return str(obj)
    # 2. dict → recurse on values
    if isinstance(obj, dict):
        return {k: serialize_bson(v) for k, v in obj.items()}
    # 3. list or tuple → recurse on elements
    if isinstance(obj, (list, tuple)):
        return [serialize_bson(v) for v in obj]
    # 4. everything else pass through
    return obj

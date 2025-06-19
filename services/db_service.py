import os
import re
import json
import pymongo
from .validation import validate_query_structure
from bson import ObjectId

client = pymongo.MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
collection = client.test.candidateprofiles

def execute_mongo_query(query_str: str):
    if "find(" in query_str:
        op, start = "find", query_str.find("find(") + 5
    elif "countDocuments(" in query_str:
        op, start = "countDocuments", query_str.find("countDocuments(") + 15
    else:
        raise ValueError("Unsupported query type")

    end = query_str.rfind(")")
    raw = query_str[start:(end if end != -1 else None)].strip()
    raw = raw.replace("'", '"')
    raw = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', raw)
    
    filt = json.loads(raw)
    validate_query_structure(filt)
    
    if op == "find":
        docs = list(collection.find(filt))
        for d in docs:
            if "_id" in d and isinstance(d["_id"], ObjectId):
                d["_id"] = str(d["_id"])
        return docs
    else:
        return collection.count_documents(filt)

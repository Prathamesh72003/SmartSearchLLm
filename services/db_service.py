import os
import re
import ast
import pymongo
from bson import ObjectId
from .validation import validate_query_structure

client = pymongo.MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
collection = client.test.candidateprofiles

def quote_mongo_operators(s: str) -> str:
    return re.sub(r'(\$[a-zA-Z_][a-zA-Z0-9_]*)', r'"\1"', s)

def quote_unquoted_keys(s: str) -> str:
    return re.sub(r'([{,]\s*)([A-Za-z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', s)

def safe_eval_dict(raw: str) -> dict:
    quoted_ops = quote_mongo_operators(raw)
    quoted_keys = quote_unquoted_keys(quoted_ops)
    return ast.literal_eval(quoted_keys)

def contains_negative_numbers(obj):
    if isinstance(obj, dict):
        return any(contains_negative_numbers(v) for v in obj.values())
    elif isinstance(obj, list):
        return any(contains_negative_numbers(i) for i in obj)
    elif isinstance(obj, (int, float)):
        return obj < 0
    return False

def execute_mongo_query(query_str: str):
    if "find(" in query_str:
        op, start = "find", query_str.find("find(") + 5
    elif "countDocuments(" in query_str:
        op, start = "countDocuments", query_str.find("countDocuments(") + 15
    else:
        raise ValueError("Unsupported query type")

    # --- Parse .sort(...) ---
    user_sort_clause = None
    sort_match = re.search(r'\.sort\((\{.*?\})\)', query_str)
    if sort_match:
        sort_str = sort_match.group(1)
        try:
            sort_dict = safe_eval_dict(sort_str)
            user_sort_clause = [(k, sort_dict[k]) for k in sort_dict]
        except Exception as e:
            raise ValueError(f"Invalid sort clause: {e}")

    # --- Parse .limit(n) ---
    limit = None
    limit_match = re.search(r'\.limit\((\d+)\)', query_str)
    if limit_match:
        try:
            limit = int(limit_match.group(1))
        except Exception as e:
            raise ValueError(f"Invalid limit value: {e}")

    # --- Parse filter ---
    end = query_str.find(").sort(") if ".sort(" in query_str else query_str.find(").limit(") if ".limit(" in query_str else query_str.rfind(")")
    raw = query_str[start:end].strip()
    try:
        filt = safe_eval_dict(raw)
        validate_query_structure(filt)
    except Exception as e:
        raise ValueError(f"Invalid filter query: {e}")

    if op == "countDocuments":
        return collection.count_documents(filt)

    # --- Build aggregation pipeline ---
    pipeline = [
        {"$match": filt},
        {
            "$addFields": {
                "_rank_priority": {
                    "$cond": [{ "$lt": ["$cub_rank", 0] }, 1, 0]  
                }
            }
        }
    ]

    sort_stage = {"$sort": {"_rank_priority": 1}}  

    if user_sort_clause:
        for field, order in user_sort_clause:
            sort_stage["$sort"][field] = order
    else:
        sort_stage["$sort"]["cub_rank"] = 1  

    pipeline.append(sort_stage)

    if limit is not None:
        pipeline.append({"$limit": limit})

    docs = list(collection.aggregate(pipeline))

    for doc in docs:
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        doc.pop("_rank_priority", None)

    return docs

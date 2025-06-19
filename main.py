import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models.schemas import SearchRequest, SearchResponse
from services.ai_service import get_gemini_response
from services.db_service import execute_mongo_query
from fastapi.encoders import jsonable_encoder

load_dotenv()
app = FastAPI(title="AI-Powered Candidate Search")

@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    # 1. Generate Mongo query
    try:
        mongo_q = get_gemini_response(req.question)
    except Exception as e:
        raise HTTPException(500, f"AI generation failed: {e}")

    # 2. Execute it
    try:
        result = execute_mongo_query(mongo_q)
    except Exception as e:
        raise HTTPException(400, f"Query execution error: {e}")
    
    safe_result = jsonable_encoder(result)

    # 3. Package response
    count = len(safe_result) if isinstance(safe_result, list) else safe_result
    return SearchResponse(
        generated_query=mongo_q,
        result_count=count,
        results=safe_result
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

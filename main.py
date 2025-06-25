import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models.schemas import SearchRequest, SearchResponse
from services.ai_service import get_gemini_response
from services.db_service import execute_mongo_query
from services.serialization import serialize_bson

load_dotenv()
app = FastAPI(title="AI-Powered Candidate Search")

@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    try:
        mongo_q = get_gemini_response(req.question)

        if not isinstance(mongo_q, str):
            raise HTTPException(400, detail="Invalid query generated. Please rephrase your question.")
        
    except Exception as e:
        raise HTTPException(500, detail=f"AI generation failed: {e}")

    try:
        print(mongo_q)
        result = execute_mongo_query(mongo_q)
        safe_result = serialize_bson(result)
        return SearchResponse(results=safe_result)
    except Exception:
        if "db.candidateprofiles.find" in mongo_q:
            return SearchResponse(results=[{"fallback_query": "No candidates found matching the specified requirements."}])
        else:
            return SearchResponse(results=[{"fallback_query": mongo_q}])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

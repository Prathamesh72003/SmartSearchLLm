from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import json
import re
import pymongo
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt[0], question])
    return response.text

def execute_mongo_query(query_str, connection_string):
    """Execute MongoDB query with advanced validation"""
    client = pymongo.MongoClient(connection_string)
    collection = client.test.candidateprofiles
    
    try:
        query_str = query_str.replace("'", '"')  
        
        if "find(" in query_str:
            match = re.search(r'find\(({.*?})\)', query_str, re.DOTALL)
            if match:
                filter_str = match.group(1).strip()
                filter_dict = json.loads(filter_str)
                _validate_query_structure(filter_dict)
                return list(collection.find(filter_dict))
        
        elif "countDocuments(" in query_str:
            match = re.search(r'countDocuments\(({.*?})\)', query_str, re.DOTALL)
            if match:
                filter_str = match.group(1).strip()
                filter_dict = json.loads(filter_str)
                _validate_query_structure(filter_dict)
                return collection.count_documents(filter_dict)
        
        else:
            return "Unsupported query type"
    
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {str(e)}")
        return []
    except ValueError as ve:
        st.error(f"Validation error: {str(ve)}")
        return []
    except Exception as e:
        st.error(f"Execution error: {str(e)}")
        return []

def _validate_query_structure(query_dict):
    """Validate query against known document structure"""
    valid_fields = {
        "user", "full_name", "bio", "profilePicture", "skills",
        "expected_salary", "experience_level", "desired_role",
        "work_preference", "overall_vetting_score", "badges",
        "cub_rank", "resume_link", "certifications", 
        "vetting_performance", "location", "mobile_number"
    }
    
    for key in query_dict.keys():
        if key not in valid_fields:
            raise ValueError(f"Invalid field detected: {key}. Valid fields are: {', '.join(valid_fields)}")

prompt = [
    """
    You are an expert in converting English questions to MongoDB queries for candidate profiles.
    Document Structure:
    - skills (array of strings): ["Network Security", "Cloud Security", "SOC", .....]
    - certifications (array of objects): {type: string, link: string}
    - desired_role (string): "Full-Time", "Part-Time", "Contract"
    - experience_level (string): "Entry-Level (0-2 years)", "Mid-Level (3-5 years)", etc.
    - work_preference: "REMOTE", "HYBRID", "ONSITE"
    
    Query Conversion Rules:
    1. Field Mappings:
       - "role" → "desired_role"
       - "position type" → "desired_role"
       - "certification" → certifications.type using $elemMatch
       - "skill" → skills array
       - "experience" → experience_level
       - "location" → exact match on location field
    
    2. Special Cases:
       - For multiple skills: Use $all operator
       - For certification types: Always use $elemMatch
       - For experience ranges: Use $regex with pattern matching
       - For salary ranges: Use $gte/$lte operators
       - For full-time/part-time: Match exact strings in desired_role
    
    3. Prohibited:
       - No regex on array fields
       - No text search operators
       - No unknown fields
    
    Examples:
    1. "Candidates with SOC skills and SQLINJECTION certification for Full-Time roles"
       db.candidateprofiles.find({ 
           "skills": "SOC", 
           "certifications": { "$elemMatch": { "type": "SQLINJECTION" } }, 
           "desired_role": "Full-Time" 
       })
    
    2. "Mid-Level candidates with Cloud Security and Network Security skills available for Hybrid work"
       db.candidateprofiles.find({
           "experience_level": { "$regex": "Mid-Level" },
           "skills": { "$all": ["Cloud Security", "Network Security"] },
           "work_preference": "HYBRID"
       })
    
    3. "Count of Entry-Level candidates in New York looking for Part-Time roles"
       db.candidateprofiles.countDocuments({
           "experience_level": "Entry-Level (0-2 years)",
           "location": "New York",
           "desired_role": "Part-Time"
       })
    
    Output only the MongoDB query without any formatting like ``` in beginning or end or explanations.
    """
]

st.set_page_config(page_title="Candidate Query Engine")
st.header("AI-Powered Candidate Search")

question = st.text_input("Search candidates by requirements:", key="input")
submit = st.button("Generate Search")

if submit:
    try:
        response = get_gemini_response(question, prompt).strip()
        st.subheader("Generated Query")
        st.code(response, language="json")
        
        if "MONGO_CONNECTION_STRING" in os.environ:
            result = execute_mongo_query(response, os.getenv("MONGO_CONNECTION_STRING"))
            st.subheader(f"Found {len(result) if isinstance(result, list) else result} results")
            st.json(result)
        else:
            st.error("Database connection not configured")
            
    except Exception as e:
        st.error(f"Search failed: {str(e)}")

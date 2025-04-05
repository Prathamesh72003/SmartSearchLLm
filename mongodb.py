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
        if "find(" in query_str:
            operation = "find"
            start_idx = query_str.find("find(") + 5
            end_idx = query_str.rfind(")")
            if end_idx == -1:
                end_idx = len(query_str)
        elif "countDocuments(" in query_str:
            operation = "countDocuments"
            start_idx = query_str.find("countDocuments(") + 15
            end_idx = query_str.rfind(")")
            if end_idx == -1:
                end_idx = len(query_str)
        else:
            return "Unsupported query type"
            
        filter_str = query_str[start_idx:end_idx].strip()
        
        try:
            for op in ['$gt', '$lt', '$gte', '$lte', '$eq', '$ne', '$in', '$nin', '$all', '$elemMatch', '$regex']:
                filter_str = filter_str.replace(f'"{op}":', f'"{op}":')
                filter_str = filter_str.replace(f'{op}:', f'"{op}":')
            
            filter_str = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', filter_str)
            
            filter_str = filter_str.replace("'", '"')
            
            filter_dict = json.loads(filter_str)
            _validate_query_structure(filter_dict)
            
            if operation == "find":
                return list(collection.find(filter_dict))
            elif operation == "countDocuments":
                return collection.count_documents(filter_dict)
                
        except (json.JSONDecodeError, SyntaxError) as e:
            st.warning(f"Using fallback parser due to: {str(e)}")
            
            if '$gt' in filter_str:
                match = re.search(r'"([^"]+)":\s*{\s*"\$gt":\s*(\d+)\s*}', filter_str)
                if match:
                    field = match.group(1)
                    value = int(match.group(2))
                    filter_dict = {field: {"$gt": value}}
                    _validate_query_structure(filter_dict)
                    
                    if operation == "find":
                        return list(collection.find(filter_dict))
                    elif operation == "countDocuments":
                        return collection.count_documents(filter_dict)
            
            st.error(f"Failed to parse query: {filter_str}")
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
    - cub_rank (number): Integer rank value
    - overall_vetting_score (number): Float score value
    
    Query Conversion Rules:
    1. Field Mappings:
       - "role" → "desired_role"
       - "position type" → "desired_role"
       - "certification" → certifications.type using $elemMatch
       - "skill" → skills array
       - "experience" → experience_level
       - "location" → exact match on location field
       - "rank" -> cub_rank
       - "vetting score" -> overall_vetting_score
       - "score" -> overall_vetting_score
       - "job type" → "desired_role"
       - "employment type" → "desired_role"
       - "cert" → certifications.type using $elemMatch
       - "certs" → certifications.type using $elemMatch
       - "skill set" → skills array
       - "abilities" → skills array
       - "years of experience" → experience_level
       - "exp" → experience_level
       - "city" → location
       - "area" → location
       - "seniority" → experience_level
       - "ranking" → cub_rank
       - "candidate score" → overall_vetting_score
    
    2. Special Cases:
       - For multiple skills: Use $all operator
       - For certification types: Always use $elemMatch
       - For experience ranges: Use $regex with pattern matching
       - For salary ranges: Use $gte/$lte operators
       - For full-time/part-time: Match exact strings in desired_role
       - For numeric comparisons: Use $gt, $lt, $gte, $lte operators

    3. Skill Input Mapping:
        - All skills in the database should be matched regardless of case or partial inputs.
        - For example, user input "soc" should map to "SOC" and "prenitration testing" should map to "Web Penetration Testing".
        - The complete list of skills to be normalized includes:
            • SOC
            • Web Penetration Testing
            • Network Security
            • Cloud Security
            • Incident Response & Forensics
            • Threat Hunting & Intelligence
            • Endpoint Security
            • Mobile Security
            • Identity & Access Management
            • Governance, Risk & Compliance
        - Ensure that any variations in case or partial input for these skills are correctly mapped to the exact skill names as stored in the database.

    
    4. Prohibited:
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
       
    4. "Give me all candidates whose rank is greater than 100"
       db.candidateprofiles.find({
           "cub_rank": { "$gt": 100 }
       })
       
    5. "Find candidates with vetting score greater than 6"
       db.candidateprofiles.find({
           "overall_vetting_score": { "$gt": 6 }
       })
    
    6. "Give me all the candidates who are skilled in SOC , cloud security and network security and has an entry level experice and rank between 200-300"
        db.candidateprofiles.find({ 
            "skills": { "$all": ["SOC", "Cloud Security", "Network Security"] }, 
            "experience_level": { "$regex": "Entry-Level" }, 
            "cub_rank": { "$gte": 200, "$lte": 300 } })
    (see how in this example it mapped the skills properly)


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

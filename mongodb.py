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

prompt=["ill write this la"]

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

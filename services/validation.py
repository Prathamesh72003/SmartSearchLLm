def validate_query_structure(query_dict: dict) -> None:
    valid_fields = {
        "user", "full_name", "bio", "profilePicture", "skills",
        "expected_salary", "experience_level", "desired_role",
        "work_preference", "overall_vetting_score", "badges",
        "cub_rank", "resume_link", "certifications",
        "vetting_performance", "location", "mobile_number"
    }
    
    for key in query_dict:
        if key not in valid_fields:
            raise ValueError(
                f"Invalid field detected: {key}. "
                f"Valid fields are: {', '.join(sorted(valid_fields))}"
            )

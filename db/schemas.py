# db/schemas.py

TABLE_SCHEMAS = {
    "tables": {
        "dim_industry": {
            "primary_key": "industry_code",
            "columns": {
                "industry_code": "INT4",
                "industry_name": "VARCHAR(500)",
                "sector": "VARCHAR(500)"
            }
        },
        "dim_local_authority": {
            "primary_key": "local_authority_code",
            "columns": {
                "local_authority_code": "VARCHAR(500)",
                "local_authority_name": "VARCHAR(500)"
            }
        },
        "dim_occupation": {
            "primary_key": "soc_code",
            "columns": {
                "soc_code": "INT4",
                "job_title": "VARCHAR(500)",
                "industry_code": "INT4"
            },
            "foreign_keys": {
                "industry_code": "dim_industry_rows.industry_code"
            }
        },
        "employee_profile": {
            "primary_key": "employee_id",
            "columns": {
                "employee_id": "INT8",
                "soc_code": "INT8",
                "sex": "TEXT",
                "qualification": "TEXT",
                "local_authority_code": "TEXT",
                "age_band": "TEXT",
                "industry_code": "INT8"
            },
            "foreign_keys": {
                "soc_code": "dim_occupation_rows.soc_code",
                "industry_code": "dim_industry_rows.industry_code",
                "local_authority_code": "dim_local_authority.local_authority_code"
            }
        },
        "fact_demographic_automation_rows": {
            "columns": {
                "year": "INT8",
                "sex": "TEXT",
                "age_band": "TEXT",
                "qualification": "TEXT",
                "low_risk": "FLOAT8",
                "medium_risk": "FLOAT8",
                "high_risk": "FLOAT8",
                "total": "INT8"
            }
        },
        "fact_geographic_automation_rows": {
            "columns": {
                "year": "INT8",
                "local_authority_code": "TEXT",
                "probability_of_automation": "FLOAT8",
                "low_risk": "INT8",
                "medium_risk": "INT8",
                "high_risk": "INT8"
            },
            "foreign_keys": {
                "local_authority_code": "dim_local_authority.local_authority_code"
            }
        },
        "fact_industry_automation_rows": {
            "columns": {
                "year": "INT8",
                "industry_code": "INT8",
                "probability_of_automation": "FLOAT8",
                "low_risk": "INT8",
                "medium_risk": "INT8",
                "high_risk": "INT8"
            },
            "foreign_keys": {
                "industry_code": "dim_industry_rows.industry_code"
            }
        },
        "soc_code_skill_training_map": {
            "columns": {
                "soc_code": "INT8",
                "skill_category": "VARCHAR(100)",
                "training_program": "VARCHAR(255)"
            }
        },
        "workforce_reskilling_cases": {
            "primary_key": "case_id",
            "columns": {
                "employee_id": "INT8",
                "training_program": "TEXT",
                "certification_earned": "BOOLEAN",
                "case_id": "INT8",
                "start_date": "DATE",
                "completion_date": "DATE",
                "soc_code": "INT8",
                "skill_category": "VARCHAR(100)"
            },
            "foreign_keys": {
                "employee_id": "employee_profile.employee_id",
                "soc_code": "dim_occupation_rows.soc_code"
            }
        },
        "workforce_reskilling_events": {
            "primary_key": "event_id",
            "columns": {
                "case_id": "INT8",
                "activity": "TEXT",
                "actor": "TEXT",
                "skill_category": "TEXT",
                "score": "NUMERIC",
                "completion_status": "TEXT",
                "event_id": "INT8",
                "timestamp": "TIMESTAMP"
            },
            "foreign_keys": {
                "case_id": "workforce_reskilling_cases.case_id"
            }
        }
    },
    "relationships": [
        {
            "left_table": "dim_occupation_rows",
            "left_column": "industry_code",
            "right_table": "dim_industry_rows",
            "right_column": "industry_code"
        },
        {
            "left_table": "employee_profile",
            "left_column": "soc_code",
            "right_table": "dim_occupation_rows",
            "right_column": "soc_code"
        },
        {
            "left_table": "employee_profile",
            "left_column": "industry_code",
            "right_table": "dim_industry_rows",
            "right_column": "industry_code"
        },
        {
            "left_table": "employee_profile",
            "left_column": "local_authority_code",
            "right_table": "dim_local_authority",
            "right_column": "local_authority_code"
        },
        {
            "left_table": "fact_geographic_automation_rows",
            "left_column": "local_authority_code",
            "right_table": "dim_local_authority",
            "right_column": "local_authority_code"
        },
        {
            "left_table": "fact_industry_automation_rows",
            "left_column": "industry_code",
            "right_table": "dim_industry_rows",
            "right_column": "industry_code"
        },
        {
            "left_table": "workforce_reskilling_cases",
            "left_column": "employee_id",
            "right_table": "employee_profile",
            "right_column": "employee_id"
        },
        {
            "left_table": "workforce_reskilling_cases",
            "left_column": "soc_code",
            "right_table": "dim_occupation_rows",
            "right_column": "soc_code"
        },
        {
            "left_table": "workforce_reskilling_events",
            "left_column": "case_id",
            "right_table": "workforce_reskilling_cases",
            "right_column": "case_id"
        }
    ]
}



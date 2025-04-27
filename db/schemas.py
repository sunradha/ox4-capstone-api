# db/schemas.py

WORKFORCE_RESKILLING_SCHEMAS = {
    "tables": {
        "dim_age_band_rows": {
            "primary_key": "age_band",
            "columns": {
                "age_band": "TEXT"
            }
        },
        "dim_geography_rows": {
            "primary_key": "local_authority_code",
            "columns": {
                "local_authority_code": "TEXT",
                "local_authority_name": "TEXT"
            }
        },
        "dim_industry_rows": {
            "primary_key": "industry_code",
            "columns": {
                "industry_code": "BIGINT",
                "industry_name": "TEXT",
                "notes": "TEXT"
            }
        },
        "dim_occupation_rows": {
            "primary_key": "soc_code",
            "columns": {
                "soc_code": "TEXT",
                "job_title": "TEXT"
            }
        },
        "dim_qualification_rows": {
            "primary_key": "qualification",
            "columns": {
                "qualification": "TEXT"
            }
        },
        "dim_sex_rows": {
            "primary_key": "sex",
            "columns": {
                "sex": "TEXT"
            }
        },
        "dim_time_rows": {
            "primary_key": "year",
            "columns": {
                "year": "BIGINT"
            }
        },
        "ess_iit_11_22_rows": {
            "primary_key": "iit_code",
            "columns": {
                "country_name": "TEXT",
                "country_code": "TEXT",
                "region_name": "TEXT",
                "region_code": "TEXT",
                "estab_size": "TEXT",
                "sector": "TEXT",
                "time_period": "BIGINT",
                "time_identifier": "TEXT",
                "geographic_level": "TEXT",
                "iit_sample_size": "TEXT",
                "employees": "TEXT",
                "trainees": "TEXT",
                "total_per_employee": "TEXT",
                "total_per_trainee": "TEXT",
                "sum_off_job_mn": "TEXT",
                "sum_on_job_mn": "TEXT",
                "sum_total_mn": "TEXT",
                "twentytwo_prices_total_per_employee": "TEXT",
                "twentytwo_prices_total_per_trainee": "TEXT",
                "twentytwo_inflaton_sum_off_job_mn": "TEXT",
                "twentytwo_inflaton_sum_on_job_mn": "TEXT",
                "twentytwo_prices_sum_total_mn": "TEXT",
                "iit_code": "TEXT"
            }
        },
        "employee_profile": {
            "primary_key": "employee_id",
            "columns": {
                "employee_id": "BIGINT",
                "soc_code": "BIGINT",
                "sex": "TEXT",
                "qualification": "TEXT",
                "local_authority_code": "TEXT",
                "age_band": "TEXT"
            },
            "foreign_keys": {
                "soc_code": "job_risk.soc_code"
            }
        },
        "fact_demographic_automation_rows": {
            "columns": {
                "year": "BIGINT",
                "sex": "TEXT",
                "age_band": "TEXT",
                "qualification": "TEXT",
                "low_risk": "FLOAT8",
                "medium_risk": "FLOAT8",
                "high_risk": "FLOAT8",
                "total": "BIGINT"
            },
            "foreign_keys": {
                "qualification": "dim_qualification_rows.qualification",
                "year": "dim_time_rows.year"
            }
        },
        "fact_geographic_automation_rows": {
            "columns": {
                "year": "BIGINT",
                "local_authority_code": "TEXT",
                "probability_of_automation": "FLOAT8",
                "low_risk": "BIGINT",
                "medium_risk": "BIGINT",
                "high_risk": "BIGINT"
            }
        },
        "fact_industry_automation_rows": {
            "columns": {
                "year": "BIGINT",
                "industry_code": "BIGINT",
                "probability_of_automation": "FLOAT8",
                "low_risk": "BIGINT",
                "medium_risk": "BIGINT",
                "high_risk": "BIGINT"
            }
        },
        "fact_skill_requirements_rows": {
            "columns": {
                "year": "BIGINT",
                "soc_code": "BIGINT",
                "population_meeting_requirements": "BIGINT",
                "proportion": "FLOAT8",
                "standard_error": "FLOAT8"
            }
        },
        "job_risk": {
            "primary_key": "soc_code",
            "columns": {
                "soc_code": "BIGINT",
                "job_title": "TEXT",
                "automation_probability": "FLOAT8"
            }
        },
        "workforce_reskilling_cases": {
            "primary_key": "case_id",
            "columns": {
                "employee_id": "BIGINT",
                "training_program": "TEXT",
                "start_date": "DATE",
                "completion_date": "DATE",
                "certification_earned": "BOOLEAN",
                "case_id": "BIGINT"
            },
            "foreign_keys": {
                "employee_id": "employee_profile.employee_id"
            }
        },
        "workforce_reskilling_events": {
            "primary_key": "event_id",
            "columns": {
                "case_id": "BIGINT",
                "activity": "TEXT",
                "timestamp": "TEXT",
                "actor": "TEXT",
                "skill_category": "TEXT",
                "score": "TEXT",
                "completion_status": "TEXT",
                "event_id": "BIGINT"
            },
            "foreign_keys": {
                "case_id": "workforce_reskilling_cases.case_id"
            }
        }
    },
    "relationships": [
        {
            "left_table": "employee_profile",
            "left_column": "soc_code",
            "right_table": "job_risk",
            "right_column": "soc_code"
        },
        {
            "left_table": "fact_demographic_automation_rows",
            "left_column": "qualification",
            "right_table": "dim_qualification_rows",
            "right_column": "qualification"
        },
        {
            "left_table": "fact_demographic_automation_rows",
            "left_column": "year",
            "right_table": "dim_time_rows",
            "right_column": "year"
        },
        {
            "left_table": "workforce_reskilling_cases",
            "left_column": "employee_id",
            "right_table": "employee_profile",
            "right_column": "employee_id"
        },
        {
            "left_table": "workforce_reskilling_events",
            "left_column": "case_id",
            "right_table": "workforce_reskilling_cases",
            "right_column": "case_id"
        },
        {
            "description": "Training program in cases matches skill category in events",
            "left_table": "workforce_reskilling_cases",
            "left_column": "training_program",
            "right_table": "workforce_reskilling_events",
            "right_column": "skill_category"
        }
    ]
}

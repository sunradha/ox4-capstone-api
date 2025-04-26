# db/schemas.py

WORKFORCE_RESKILLING_SCHEMAS = """
Here are the PostgreSQL DDL statements for the relevant tables. Sample data has been omitted for clarity.

-- Dimension Tables

CREATE TABLE public.dim_age_band_rows (
    age_band TEXT NOT NULL,
    CONSTRAINT dim_age_band_rows_pkey PRIMARY KEY (age_band)
);

CREATE TABLE public.dim_geography_rows (
    local_authority_code TEXT NOT NULL,
    local_authority_name TEXT NULL,
    CONSTRAINT dim_geography_rows_pkey PRIMARY KEY (local_authority_code)
);

CREATE TABLE public.dim_industry_rows (
    industry_code BIGINT NOT NULL,
    industry_name TEXT NULL,
    notes TEXT NULL,
    CONSTRAINT dim_industry_rows_pkey PRIMARY KEY (industry_code)
);

CREATE TABLE public.dim_occupation_rows (
    soc_code TEXT NOT NULL,
    job_title TEXT NULL,
    CONSTRAINT dim_occupation_rows_pkey PRIMARY KEY (soc_code)
);

CREATE TABLE public.dim_qualification_rows (
    qualification TEXT NOT NULL,
    CONSTRAINT dim_qualification_rows_pkey PRIMARY KEY (qualification)
);

CREATE TABLE public.dim_sex_rows (
    sex TEXT NOT NULL,
    CONSTRAINT dim_sex_rows_pkey PRIMARY KEY (sex)
);

CREATE TABLE public.dim_time_rows (
    year BIGINT NOT NULL,
    CONSTRAINT dim_time_rows_pkey PRIMARY KEY (year)
);

-- Fact Tables

CREATE TABLE public.ess_iit_11_22_rows (
    country_name TEXT NULL,
    country_code TEXT NOT NULL,
    region_name TEXT NULL,
    region_code TEXT NULL,
    estab_size TEXT NULL,
    sector TEXT NULL,
    time_period BIGINT NULL,
    time_identifier TEXT NULL,
    geographic_level TEXT NULL,
    iit_sample_size TEXT NULL,
    employees TEXT NULL,
    trainees TEXT NULL,
    total_per_employee TEXT NULL,
    total_per_trainee TEXT NULL,
    sum_off_job_mn TEXT NULL,
    sum_on_job_mn TEXT NULL,
    sum_total_mn TEXT NULL,
    twentytwo_prices_total_per_employee TEXT NULL,
    twentytwo_prices_total_per_trainee TEXT NULL,
    twentytwo_inflaton_sum_off_job_mn TEXT NULL,
    twentytwo_inflaton_sum_on_job_mn TEXT NULL,
    twentytwo_prices_sum_total_mn TEXT NULL,
    iit_code TEXT NOT NULL,
    CONSTRAINT ess_iit_11_22_rows_pkey PRIMARY KEY (iit_code)
);

CREATE TABLE public.employee_profile (
    employee_id BIGINT NOT NULL,
    soc_code BIGINT NULL,
    sex TEXT NULL,
    qualification TEXT NULL,
    local_authority_code TEXT NULL,
    age_band TEXT NULL,
    CONSTRAINT employee_profile_pkey PRIMARY KEY (employee_id),
    CONSTRAINT employee_profile_soc_code_fkey FOREIGN KEY (soc_code) REFERENCES public.job_risk(soc_code)
);

CREATE TABLE public.fact_demographic_automation_rows (
    year BIGINT NULL,
    sex TEXT NULL,
    age_band TEXT NOT NULL,
    qualification TEXT NULL,
    low_risk FLOAT8 NULL,
    medium_risk FLOAT8 NULL,
    high_risk FLOAT8 NULL,
    total BIGINT NULL,
    CONSTRAINT fact_demographic_automation_rows_qualification_fkey FOREIGN KEY (qualification) REFERENCES public.dim_qualification_rows(qualification),
    CONSTRAINT fact_demographic_automation_rows_year_fkey FOREIGN KEY (year) REFERENCES public.dim_time_rows(year)
);

CREATE TABLE public.fact_geographic_automation_rows (
    year BIGINT NULL,
    local_authority_code TEXT NOT NULL,
    probability_of_automation FLOAT8 NULL,
    low_risk BIGINT NULL,
    medium_risk BIGINT NULL,
    high_risk BIGINT NULL
);

CREATE TABLE public.fact_industry_automation_rows (
    year BIGINT NULL,
    industry_code BIGINT NOT NULL,
    probability_of_automation FLOAT8 NULL,
    low_risk BIGINT NULL,
    medium_risk BIGINT NULL,
    high_risk BIGINT NULL
);

CREATE TABLE public.fact_skill_requirements_rows (
    year BIGINT NULL,
    soc_code BIGINT NOT NULL,
    population_meeting_requirements BIGINT NULL,
    proportion FLOAT8 NULL,
    standard_error FLOAT8 NULL
);

CREATE TABLE public.job_risk (
    soc_code BIGINT NOT NULL,
    job_title TEXT NULL,
    automation_probability FLOAT8 NULL,
    CONSTRAINT job_risk_pkey PRIMARY KEY (soc_code)
);

-- Process Mining Tables

CREATE TABLE public.workforce_reskilling_cases (
    employee_id BIGINT NULL,
    training_program TEXT NULL,
    start_date DATE NULL,
    completion_date DATE NULL,
    certification_earned BOOLEAN NULL,
    case_id BIGINT NOT NULL,
    CONSTRAINT workforce_reskilling_cases_pkey PRIMARY KEY (case_id),
    CONSTRAINT workforce_reskilling_cases_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee_profile(employee_id)
);

CREATE TABLE public.workforce_reskilling_events (
    case_id BIGINT NULL,
    activity TEXT NULL,
    timestamp TEXT NULL,
    actor TEXT NULL,
    skill_category TEXT NULL,
    score TEXT NULL,
    completion_status TEXT NULL,
    event_id BIGINT NOT NULL,
    CONSTRAINT workforce_reskilling_events_pkey PRIMARY KEY (event_id),
    CONSTRAINT workforce_reskilling_events_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.workforce_reskilling_cases(case_id)
);
"""

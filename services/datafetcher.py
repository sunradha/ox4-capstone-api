import os
import psycopg2
from fastapi import HTTPException  # For handling HTTP exceptions
import pandas as pd  # For creating and manipulating dataframes
import logging  # For logging functionality
from utils.openai_client import client  # For OpenAI API client
from services.sampledatagenerator import (
    generate_sample_data_based_on_query,
    generate_sample_event_data,
    generate_sample_knowledge_graph_data,
    generate_sample_causal_data
)  # For generating sample data
from db.client import supabase  # For Supabase client

from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger.setLevel(logging.DEBUG)


def fetch_data_from_supabase_psycopg2(query):
    """
    Execute raw SQL query on Supabase Postgres and return results as a pandas DataFrame.
    """
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        records = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(records)

        cursor.close()
        connection.close()

        return df

    except Exception as e:
        print(f"Error executing query: {e}")
        raise e


# def fetch_data_from_supabase(query):
#     """
#     Execute SQL query on Supabase and return results as a pandas DataFrame
#     """
#     try:
#         if 'FROM workforce_reskilling_events' in query:
#             table_name = 'workforce_reskilling_events'
#         elif 'FROM employee_profile' in query:
#             table_name = 'employee_profile'
#         elif 'FROM workforce_reskilling_cases' in query:
#             table_name = 'workforce_reskilling_cases'
#         else:
#             logger.warning(f"Unable to determine table name from query: {query[:100]}...")
#             print(f"Unable to determine table name from query: {query[:100]}...")
#             # Fall back to sample data
#             return generate_sample_data_based_on_query(query)
#
#         print(f"Querying table: {table_name}...")
#         logger.debug(f"Querying table: {table_name}...")
#         response = supabase.table(table_name).select('*').execute()
#         logger.debug(f"fetch_data_from_supabase(query) Response from Supabase: {response}")
#         # Convert response to DataFrame
#         data = pd.DataFrame(response.data)
#
#         if data.empty:
#             logger.warning(f"No data found in table {table_name}, using sample data instead")
#             print(f"No data found in table {table_name}, using sample data instead")
#             return generate_sample_data_based_on_query(query)
#
#         return data
#     except Exception as e:
#         print(f"Error fetching data: {e}")
#         # Fall back to sample data
#         return generate_sample_data_based_on_query(query)


def fetch_data_from_supabase(table_name: str, filters: dict = None):
    logger.debug(f"fetch_data_from_supabase = {table_name}, filters= {filters})")
    query = supabase.table(table_name).select("*")
    logger.debug(f"Initial query: {query}")
    logger.debug(f"Filters: {filters}")

    if filters:
        for key, value in filters.items():
            if key == "skill_category":
                query = query.eq("skill_category", value)
                logger.debug(
                    f"fetch_data_from_supabase filter by skill_category: {query}"
                )
            elif key == "outcome":
                query = query.eq("certification_earned", value.lower() == "success")
            else:
                query = query.eq(key, value)

    logger.debug(f"Query after applying filters: {query}")
    try:
        result = query.execute()
        # logger.debug(f"Query result: {result}")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=f"Supabase error: {str(e)}")

    if not result.data:
        logger.warning(f"No data found for table {table_name} with filters {filters}")
        raise HTTPException(status_code=404, detail="No data found")

    return result.data


def fetch_data_from_supabase2(query):
    """
    Execute SQL query on Supabase and return results as a pandas DataFrame
    """
    try:
        response = supabase.table('query').select('*').execute()
        # Note: In a real implementation, you would use the actual query parameter
        # This is a placeholder since we don't have actual Supabase access

        # For demonstration, let's generate some sample data instead
        print(f"Executing query: {query[:100]}...")

        # Simulate data based on query type
        if 'workforce_reskilling_events' in query:
            return generate_sample_event_data()
        elif 'employee_profile' in query and 'job_risk' in query:
            return generate_sample_knowledge_graph_data()
        elif 'training_duration' in query:
            return generate_sample_causal_data()
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()


def query_openai_o3(data_json, reasoning_query):
    """
    Send a reasoning query to OpenAI O3 API with the provided dataset

    Args:
        data_json: JSON string containing the dataset
        reasoning_query: String containing the reasoning query

    Returns:
        String containing the OpenAI response
    """
    try:
        prompt = f"""
        You are an AI expert in workforce analytics, process mining, and reskilling strategies.

        Analyze the following dataset related to workforce reskilling and automation risk:

        {data_json[:3000]}... [truncated for brevity]

        Based on this dataset, please address the following reasoning query:

        {reasoning_query}

        Provide detailed analysis with specific insights and actionable recommendations.
        """

        response = client.chat.completions.create(
            model="gpt-4o",  # Use the most capable model available
            messages=[
                {"role": "system",
                 "content": "You are an expert in data analysis, process mining, and workforce analytics with advanced reasoning capabilities."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temperature for more focused analysis
            max_tokens=2500
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return f"Error: {e}"

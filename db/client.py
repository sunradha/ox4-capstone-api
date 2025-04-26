import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd


def run_sql_query_postgres(query):
    connection = None  # Initialize connection as None
    cursor = None

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
        return df

    except Exception as e:
        print(f"Error executing query: {e}")
        raise e

    finally:
        # Safely close cursor and connection if they were opened
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

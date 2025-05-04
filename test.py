import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import openai

app = FastAPI()


class QueryRequest(BaseModel):
    question: str


# Assume you have LLM setup
openai.api_key = 'YOUR_OPENAI_API_KEY'

# Supabase DB connection setup
DATABASE_URL = {
    'dbname': 'dbname',
    'user': 'username',
    'password': 'password',
    'host': 'host',
    'port': 'port'
}


@app.post("/generate-graph")
def generate_graph(request: QueryRequest):
    # Step 1: Use LLM to identify reasoning type
    reasoning_type = identify_reasoning_type(request.question)

    # Step 2: Use LLM to generate SQL
    sql_query = generate_sql_from_question(request.question, reasoning_type)

    # Step 3: Query Supabase (Postgres)
    conn = psycopg2.connect(**DATABASE_URL)
    df = pd.read_sql_query(sql_query, conn)
    conn.close()

    # Step 4: Convert to JSON chart data
    chart_type, chart_data = prepare_chart_data(df, reasoning_type)

    return {"chartType": chart_type, "chartData": chart_data}


def identify_reasoning_type(question: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Identify the reasoning type."},
                  {"role": "user", "content": question}]
    )
    return response['choices'][0]['message']['content'].strip()


def generate_sql_from_question(question: str, reasoning_type: str) -> str:
    schema_description = "Describe your table schemas here"
    prompt = f"""Based on the following schema: {schema_description}\nGenerate a SQL query for the question: {question}\nReasoning type: {reasoning_type}"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Generate SQL."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()


def prepare_chart_data(df, reasoning_type):
    if reasoning_type == "Deductive":
        chart_type = "network"
        chart_data = {"nodes": df["premise"].tolist(), "edges": df["conclusion"].tolist()}
    elif reasoning_type == "Inductive":
        chart_type = "scatter"
        chart_data = df.to_dict(orient="records")
    elif reasoning_type == "Temporal":
        chart_type = "line"
        chart_data = df.to_dict(orient="records")
    elif reasoning_type == "Causal":
        chart_type = "network"
        chart_data = {"nodes": df["cause"].tolist(), "edges": df["effect"].tolist()}
    else:
        chart_type = "table"
        chart_data = df.to_dict(orient="records")
    return chart_type, chart_data

import logging
from llm.prompts import *
from utils.utils import parsed_reasoning_output, parsed_graph_output, parsed_sql
from services.visualizer import prepare_chart_data
from services.graph import *

logger = logging.getLogger(__name__)


def classify_reasoning_type(question):
    reasoning_prompt = get_reasoning_prompt(question)
    reasoning_response = call_llm(reasoning_prompt)
    return reasoning_response


def build_response(reasoning_type=None, reasoning_answer=None, reasoning_path=None, sql=None,
                   chart=None, error=None):
    return {
        "reasoning_type": reasoning_type,
        "reasoning_answer": reasoning_answer,
        "reasoning_path": reasoning_path,
        "sql": sql,
        "chart": chart,
        "error": error
    }


def run_reasoning_pipeline(question):
    try:
        # Step 1 → Get reasoning type + visualization type
        reasoning_llm_output = classify_reasoning_type(question)
        reasoning_result = parsed_reasoning_output(reasoning_llm_output)

        reasoning_cat = reasoning_result.get("reasoning_type", "Unknown").strip().capitalize()
        reasoning_justification = reasoning_result.get("reasoning_justification")
        reasoning_type = f'{reasoning_justification} So this reasoning is of type "{reasoning_cat}"'
        reasoning_path = reasoning_result.get("reasoning_path")
        visualization_type = reasoning_result.get("visualization_type", "").strip()
        print("====================================")
        print(reasoning_type)
        print(reasoning_path)
        print(visualization_type)
        print("====================================")

        sql_prompt = get_sql_prompt(question, reasoning_type, visualization_type)
        llm_sql_response = call_llm(sql_prompt)
        sql = parsed_sql(llm_sql_response)
        print("Generated SQL:\n", sql)
        df = run_sql_query_postgres(sql)
        if df.empty:
            raise ValueError("No data returned from database.")
        else:
            df = clean_dataframe_columns(df)

        db_data_json = df.to_json(orient='records')

        # STEP 2 → Select appropriate logic
        if visualization_type == "Knowledge Graph":
            graph_schema = process_knowledge_graph(question, reasoning_type, db_data_json)
        elif visualization_type == "Causal Graph":
            graph_schema = process_causal_graph(question, reasoning_type, db_data_json)
        elif visualization_type == "Process Flow":
            graph_schema = process_process_flow(question, reasoning_type, db_data_json)
        else:
            graph_schema = process_charts(question, reasoning_type, visualization_type, db_data_json)

        print("Final Chart Schema :\n ", graph_schema)
        # STEP 3 → Format frontend JSON
        chart_json = prepare_chart_data(df, visualization_type, graph_schema)

        return build_response(
            reasoning_type,
            graph_schema.get("reasoning_answer"),
            reasoning_path,
            sql,
            chart_json,
            None
        )

    except Exception as e:
        return build_response(
            reasoning_type=None,
            reasoning_answer=None,
            reasoning_path=None,
            sql=None,
            chart=None,
            error=str(e)
        )

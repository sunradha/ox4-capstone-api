import logging
import pandas as pd
from llm.prompts import *
from utils.utils import parsed_reasoning_output, parsed_graph_output, parsed_sql, parsed_2sqls
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
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("Reasoning Type : \n", reasoning_type)
        print("Reasoning Path : \n", reasoning_path)
        print("Visualization Type : \n", visualization_type)

        df = pd.DataFrame()
        sql = None

        if visualization_type == "Knowledge Graph":
            sql_prompt = get_kg_sql_prompt(question, reasoning_type, visualization_type)
            llm_sql_response = call_llm(sql_prompt)
            sql = parsed_2sqls(llm_sql_response)
            nodes_sql = sql.get('nodes_sql')
            edges_sql = sql.get('edges_sql')
            nodes_df = run_sql_query_postgres(nodes_sql) if nodes_sql else None
            edges_df = run_sql_query_postgres(edges_sql) if edges_sql else None

            if nodes_df is not None and edges_df is not None:
                source_nodes_df = nodes_df.rename(columns={'node_id': 'source', 'node_label': 'source_label', 'node_type': 'source_type'})
                target_nodes_df = nodes_df.rename(columns={'node_id': 'target', 'node_label': 'target_label', 'node_type': 'target_type'})
                edges_enriched = edges_df.merge(source_nodes_df, on='source', how='left')
                edges_enriched = edges_enriched.merge(target_nodes_df, on='target', how='left')
                df = edges_enriched.drop_duplicates().reset_index(drop=True)
            elif nodes_df is not None:
                df = nodes_df.copy()
            elif edges_df is not None:
                df = edges_df.copy()

            df = df.head(20)
            db_data_json = df.to_json(orient='records')
            graph_schema = process_knowledge_graph(question, reasoning_type, db_data_json)

        elif visualization_type == "Causal Graph":
            sql_prompt = get_cg_sql_prompt(question, reasoning_type, visualization_type)
            llm_sql_response = call_llm(sql_prompt)
            sql = parsed_2sqls(llm_sql_response)
            nodes_sql = sql.get('nodes_sql')
            edges_sql = sql.get('edges_sql')
            nodes_df = run_sql_query_postgres(nodes_sql) if nodes_sql else None
            edges_df = run_sql_query_postgres(edges_sql) if edges_sql else None

            if nodes_df is not None and edges_df is not None:
                source_nodes_df = nodes_df.rename(
                    columns={'node_id': 'source', 'node_label': 'source_label', 'node_type': 'source_type'})
                target_nodes_df = nodes_df.rename(
                    columns={'node_id': 'target', 'node_label': 'target_label', 'node_type': 'target_type'})
                edges_enriched = edges_df.merge(source_nodes_df, on='source', how='left')
                edges_enriched = edges_enriched.merge(target_nodes_df, on='target', how='left')
                df = edges_enriched.drop_duplicates().reset_index(drop=True)
            elif nodes_df is not None:
                df = nodes_df.copy()
            elif edges_df is not None:
                df = edges_df.copy()

            df = df.head(20)
            db_data_json = df.to_json(orient='records')
            graph_schema = process_causal_graph(question, reasoning_type, db_data_json)

        elif visualization_type == "Process Flow":
            sql_prompt = get_pf_sql_prompt(question, reasoning_type, visualization_type)
            llm_sql_response = call_llm(sql_prompt)
            sql = parsed_2sqls(llm_sql_response)
            nodes_sql = sql.get('nodes_sql')
            edges_sql = sql.get('edges_sql')
            print("Nodes SQL : \n", nodes_sql)
            print("Edges SQL : \n", edges_sql)
            nodes_df = run_sql_query_postgres(nodes_sql) if nodes_sql else None
            edges_df = run_sql_query_postgres(edges_sql) if edges_sql else None

            if nodes_df is not None and edges_df is not None:
                source_nodes_df = nodes_df.rename(
                    columns={'node_id': 'source', 'node_label': 'source_label', 'node_type': 'source_type'})
                target_nodes_df = nodes_df.rename(
                    columns={'node_id': 'target', 'node_label': 'target_label', 'node_type': 'target_type'})
                edges_enriched = edges_df.merge(source_nodes_df, on='source', how='left')
                edges_enriched = edges_enriched.merge(target_nodes_df, on='target', how='left')
                df = edges_enriched.drop_duplicates().reset_index(drop=True)
            elif nodes_df is not None:
                df = nodes_df.copy()
            elif edges_df is not None:
                df = edges_df.copy()

            df = df.head(20)
            db_data_json = df.to_json(orient='records')
            graph_schema = process_process_flow(question, reasoning_type, db_data_json)

        else:
            sql_prompt = get_sql_prompt(question, reasoning_type, visualization_type)
            llm_sql_response = call_llm(sql_prompt)
            sql = parsed_sql(llm_sql_response)
            df = run_sql_query_postgres(sql)

            if df.empty:
                raise ValueError("No data returned from database.")
            df = clean_dataframe_columns(df)
            db_data_json = df.to_json(orient='records')
            graph_schema = process_charts(question, reasoning_type, visualization_type, db_data_json)

        chart_json = prepare_chart_data(df, visualization_type, graph_schema)
        print("Graph : \n", graph_schema)
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
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


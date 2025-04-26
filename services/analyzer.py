import pandas as pd
from utils.openai_client import generate_sql_and_plot_code, regenerate_plot_code_from_columns, parse_llm_response
from db.schemas import WORKFORCE_RESKILLING_SCHEMAS
from db.client import run_sql_query_postgres
from utils.visualizer import validate_generated_code, safe_exec_plotting_code
from services.reasoning import get_reasoning_category_and_intent
from services.graph import convert_to_causal_graph, render_knowledge_graph


def run_reasoning_pipeline(question):
    print(f"\nUser question: {question}")

    # Get both reasoning category and intent
    reasoning_result = get_reasoning_category_and_intent(question)
    reasoning_type = reasoning_result.get("reasoning_type")
    reasoning_justification = reasoning_result.get("reasoning_justification")
    intent = "process_flow"
    # intent = reasoning_result.get("intent")
    intent_justification = reasoning_result.get("intent_justification")

    print(f"Reasoning Type: {reasoning_result}")
    print(f"Reasoning Justification: {reasoning_justification}")
    print(f"Intent: {intent}")
    print(f"Intent Justification: {intent_justification}")

    # Generate SQL and plot code using reasoning type
    llm_response = generate_sql_and_plot_code(WORKFORCE_RESKILLING_SCHEMAS, question, reasoning_type, intent)
    parsed_output = parse_llm_response(llm_response, reasoning_type, intent)

    generated_sql = parsed_output.get("generated_sql")
    generated_plot_code = parsed_output.get("generated_plot_code")

    print("Generated SQL:\n", generated_sql)
    print("Generated Code:\n", generated_plot_code)

    data = None
    if generated_sql:
        try:
            data = run_sql_query_postgres(generated_sql)
            print("\nQuery Result (Top 5 Rows):\n", data.head())
        except Exception as e:
            print("\nSQL Error:", e)
            return {"status": "error", "message": f"SQL execution failed: {str(e)}"}

    if isinstance(data, pd.DataFrame) and not data.empty:
        # Intent-based graph rendering logic
        if intent == "knowledge_graph":
            nodes_info = parsed_output['graph_schema']['nodes']
            edges_info = parsed_output['graph_schema']['edges']

            try:
                graph_image_base64 = render_knowledge_graph(data, nodes_info, edges_info)
                return {
                    "status": "success",
                    "reasoning_type": reasoning_type,
                    "reasoning_justification": reasoning_justification,
                    "intent": intent,
                    "intent_justification": intent_justification,
                    "sql_query": generated_sql,
                    "graph_image_base64": graph_image_base64
                }
            except Exception as e:
                return {"status": "error", "message": f"Knowledge Graph generation failed: {str(e)}"}

        elif intent == "causal_graph":
            graph_data = convert_to_causal_graph(data)
            return {
                "status": "success",
                "reasoning_type": reasoning_type,
                "reasoning_justification": reasoning_justification,
                "intent": intent,
                "intent_justification": intent_justification,
                "sql_query": generated_sql,
                "graph_data": graph_data
            }

        # Default: Plot-based rendering for other intents
        if validate_generated_code(generated_plot_code, data):
            print("\nRunning generated plot code...")
            plot_result = safe_exec_plotting_code(generated_plot_code, data)
        else:
            print("\nColumn mismatch detected. Regenerating plot code...")
            regenerated_plot_code = regenerate_plot_code_from_columns(data.columns.tolist(), question)
            print("\nRegenerated Plot Code:\n", regenerated_plot_code)

            if validate_generated_code(regenerated_plot_code, data):
                print("\nRunning regenerated plot code...")
                plot_result = safe_exec_plotting_code(regenerated_plot_code, data)
            else:
                return {"status": "error", "message": "Column mismatch even after regeneration."}
    else:
        return {"status": "error", "message": "No data returned from SQL query."}

    if "error" in plot_result:
        return {"status": "error", "message": plot_result["error"]}

    # Final response for plot-based intents
    return {
        "status": "success",
        "reasoning_type": reasoning_type,
        "reasoning_justification": reasoning_justification,
        "intent": intent,
        "intent_justification": intent_justification,
        "sql_query": generated_sql,
        "plot_image_base64": plot_result["image_base64"]
    }

from utils.openai_client import generate_sql_and_plot_code, regenerate_plot_code_from_columns, parse_llm_response
from db.client import run_sql_query_postgres
from utils.visualizer import validate_generated_code, safe_exec_plotting_code
from services.reasoning import get_reasoning_category_and_intent
from services.graph import convert_to_knowledge_graph, convert_to_causal_graph


def run_reasoning_pipeline(schemas, question):
    print(f"\nUser question: {question}")

    # Get both reasoning category and intent
    reasoning_type, reasoning_justification, intent, intent_justification = get_reasoning_category_and_intent(question)

    print(f"Reasoning Type: {reasoning_type}")
    print(f"Reasoning Justification: {reasoning_justification}")
    print(f"Intent: {intent}")
    print(f"Intent Justification: {intent_justification}")

    # Generate SQL and plot code using reasoning type
    llm_response = generate_sql_and_plot_code(schemas, question, reasoning_type)
    parsed_output = parse_llm_response(llm_response, reasoning_type)

    reasoning_explanation = parsed_output.get("reasoning_explanation")
    generated_sql = parsed_output.get("generated_sql")
    generated_plot_code = parsed_output.get("generated_plot_code")

    print("Reasoning Explanation:", reasoning_explanation)
    print("Generated SQL:", generated_sql)
    print("Generated Code:", generated_plot_code)

    data = None
    if generated_sql:
        try:
            data = run_sql_query_postgres(generated_sql)
            print("\nQuery Result (Top 5 Rows):\n", data.head())
        except Exception as e:
            print("\nSQL Error:", e)
            return {"status": "error", "message": f"SQL execution failed: {str(e)}"}

    if data is not None and not data.empty:
        # Intent-based graph rendering logic
        if intent == "knowledge_graph":
            graph_data = convert_to_knowledge_graph(data)
            return {
                "status": "success",
                "reasoning_type": reasoning_type,
                "reasoning_justification": reasoning_justification,
                "intent": intent,
                "intent_justification": intent_justification,
                "reasoning_explanation": reasoning_explanation,
                "sql_query": generated_sql,
                "graph_data": graph_data
            }

        elif intent == "causal_graph":
            graph_data = convert_to_causal_graph(data)
            return {
                "status": "success",
                "reasoning_type": reasoning_type,
                "reasoning_justification": reasoning_justification,
                "intent": intent,
                "intent_justification": intent_justification,
                "reasoning_explanation": reasoning_explanation,
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
        "reasoning_explanation": reasoning_explanation,
        "sql_query": generated_sql,
        "plot_image_base64": plot_result["image_base64"]
    }

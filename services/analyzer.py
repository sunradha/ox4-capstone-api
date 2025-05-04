import logging
from llm.prompts import *
from utils.utils import parsed_reasoning_output, parsed_graph_output
from services.visualizer import prepare_chart_data
from services.graph import *

logger = logging.getLogger(__name__)


def classify_reasoning_type(question):
    reasoning_prompt = get_reasoning_prompt(question)
    reasoning_response = call_llm(reasoning_prompt)
    return reasoning_response


def build_response(reasoning_type, reasoning_justification, reasoning_path,
                   visualization_type, reasoning_answer=None, chart=None, error=None):
    """
    Builds a structured response dictionary for the API.
    """
    return {
        "reasoning_type": reasoning_type,
        "reasoning_justification": reasoning_justification,
        "reasoning_path": reasoning_path,
        "visualization_type": visualization_type,
        "reasoning_answer": reasoning_answer,
        "chart": chart,
        "error": error
    }


def run_reasoning_pipeline(question):
    try:
        # Step 1 → Get reasoning type + visualization type
        reasoning_llm_output = classify_reasoning_type(question)
        reasoning_result = parsed_reasoning_output(reasoning_llm_output)
        reasoning_type = reasoning_result.get("reasoning_type", "Unknown").strip()
        visualization_type = reasoning_result.get("visualization_type", "").strip()

        graph_schema = {}
        df = None

        # STEP 2 → Select appropriate logic
        if visualization_type == "Knowledge Graph":
            graph_schema = process_knowledge_graph(question, reasoning_type, visualization_type)
        elif visualization_type == "Causal Graph":
            graph_schema, df = process_causal_graph(question, reasoning_type, visualization_type)
        elif visualization_type == "Process Flow":
            graph_schema, df = process_process_flow(question, reasoning_type)
        else:
            # fallback for other chart types
            graph_schema, df = process_charts(question, reasoning_type, visualization_type)
        print("Final G Schema :\n ", graph_schema)
        # STEP 3 → Format frontend JSON
        chart_json = prepare_chart_data(df, visualization_type, graph_schema)

        return build_response(
            reasoning_type,
            reasoning_result.get("reasoning_justification"),
            reasoning_result.get("reasoning_path"),
            visualization_type,
            graph_schema.get('reasoning_answer'),
            chart_json,
            None
        )

    except Exception as e:
        return build_response(
            reasoning_type=None,
            reasoning_justification=None,
            reasoning_path=None,
            visualization_type=None,
            reasoning_answer=None,
            chart=None,
            error=str(e)
        )

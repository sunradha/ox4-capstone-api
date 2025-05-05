import logging
import os
import io
import re
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import builtins
import base64
import seaborn as sns
from datetime import datetime

# Generate current timestamp string
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def validate_generated_code(code, dataframe):
    columns_in_code = re.findall(r"data\[['\"](.*?)['\"]]", code)
    return all(col in dataframe.columns for col in columns_in_code)


def safe_exec_plotting_code(code, dataframe):
    safe_builtins = {
        'range': builtins.range,
        'len': builtins.len,
        'sum': builtins.sum,
        'min': builtins.min,
        'max': builtins.max,
        'abs': builtins.abs,
        'float': builtins.float,
        'int': builtins.int,
        'str': builtins.str,
        'print': builtins.print,
        '__import__': builtins.__import__,
    }

    safe_globals = {
        '__builtins__': safe_builtins,
        'plt': plt,
        'pd': pd,
        'data': dataframe
    }

    plt.clf()

    try:
        exec(code, safe_globals)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        # Save the image to 'output' folder
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        output_dir = os.path.join(parent_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f'graph_{timestamp}.png')
        logging.info("Saving the Graph to Output Folder")
        with open(output_path, 'wb') as f:
            f.write(buf.getvalue())

        # 🔥 Encode the image as Base64 string
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return {"image_base64": img_base64}

    except Exception as e:
        print("Error executing generated code:", e)
        return {"error": str(e)}


def prepare_chart_data(df, visualization_type, graph_schema=None):
    def safe_get(col_name):
        return df[col_name].tolist() if col_name in df.columns else []

    if visualization_type == "Ranking Chart":
        return {
            "type": "ranking",
            "data": {
                "x": safe_get('x'),
                "y": safe_get('y'),
                "labels": safe_get('label')
            }
        }
    elif visualization_type == "Pie Chart":
        return {
            "type": "pie",
            "data": {
                "labels": safe_get('label'),
                "values": safe_get('value')
            }
        }
    elif visualization_type == "Time Series Chart":
        return {
            "type": "time_series",
            "data": {
                "x": [str(val) for val in safe_get('x')],
                "y": safe_get('y')
            }
        }
    elif visualization_type == "Comparative Bar Chart":
        categories = safe_get('x')
        series = [
            {"name": col, "data": df[col].tolist()}
            for col in df.columns if col != 'x'
        ] if not df.empty else []
        return {
            "type": "comparative_bar",
            "data": {
                "categories": categories,
                "series": series
            }
        }
    elif visualization_type == "Histogram":
        return {
            "type": "histogram",
            "data": {
                "values": safe_get('value')
            }
        }
    elif visualization_type in ["Knowledge Graph", "Causal Graph", "Process Flow"]:
        return {
            "type": visualization_type.lower().replace(' ', '_'),
            "data": {
                "nodes": graph_schema.get("data_nodes") if graph_schema else [],
                "edges": graph_schema.get("data_edges") if graph_schema else []
            }
        }
    else:
        return {
            "type": "table",
            "data": df.to_dict(orient="records") if not df.empty else []
        }

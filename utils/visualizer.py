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
        with open(output_path, 'wb') as f:
            f.write(buf.getvalue())

        # 🔥 Encode the image as Base64 string
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return {"image_base64": img_base64}

    except Exception as e:
        print("Error executing generated code:", e)
        return {"error": str(e)}

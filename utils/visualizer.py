import io
import re
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import builtins
import base64


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

        # 🔥 Encode the image as Base64 string
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return {"image_base64": img_base64}

    except Exception as e:
        print("Error executing generated code:", e)
        return {"error": str(e)}

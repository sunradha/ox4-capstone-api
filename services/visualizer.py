import numpy as np


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
    elif visualization_type == "Multi-Series Time Series Chart":
        if not df.empty:
            # Step 1: Identify top 5 categories based on total 'y' value
            top_categories = (
                df.groupby("series")["y"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
                .index.tolist()
            )

            # Step 2: Filter only those top 5 categories
            df = df[df["series"].isin(top_categories)]

            # Step 3: Pivot to wide format for multi-series chart
            pivot_df = df.pivot(index="x", columns="series", values="y").reset_index()
            pivot_df.columns.name = None  # Remove column grouping label

            # Step 4: Clean non-finite values
            pivot_df.replace([np.inf, -np.inf], np.nan, inplace=True)
            pivot_df = pivot_df.where(pivot_df.notnull(), None)

            return {
                "type": visualization_type.lower().replace(' ', '_'),
                "data": pivot_df.to_dict(orient="records")
            }
    else:
        return {
            "type": "table",
            "data": df.to_dict(orient="records") if not df.empty else []
        }

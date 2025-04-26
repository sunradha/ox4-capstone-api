import datetime
import json


class DataFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp) or isinstance(obj, datetime):
            return obj.isoformat()
        if pd.isna(obj):  # Handles NaN, None, NaT
            return None
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)
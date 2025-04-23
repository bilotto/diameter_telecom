import datetime

def convert_timestamp(timestamp: float) -> str:
    return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
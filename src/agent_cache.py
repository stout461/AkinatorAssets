import os
import json
from datetime import datetime, timedelta

CACHE_FILE = "agent_output_cache.json"
CACHE_TTL_HOURS = 24

def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_cached_agent_output(ticker):
    cache = _load_cache()
    record = cache.get(ticker)
    if record:
        timestamp = datetime.fromisoformat(record['timestamp'])
        if datetime.now() - timestamp < timedelta(hours=CACHE_TTL_HOURS):
            return record['output']
    return None

def cache_agent_output(ticker, output):
    cache = _load_cache()
    cache[ticker] = {
        "timestamp": datetime.now().isoformat(),
        "output": output
    }
    _save_cache(cache)
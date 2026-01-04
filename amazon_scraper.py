import requests, time, pandas as pd
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from scraper_utils import save_jobs

BASE_URL = "https://www.amazon.jobs/en/search.json"
SLEEP = 0.25
USER_AGENT = "Mozilla/5.0"

# --- Houston center point (Downtown Houston) ---
HOUSTON_LAT = 29.7604
HOUSTON_LON = -95.3698

def build_url(base_query="data engineer", offset=0, result_limit=50, radius="80km"):
    """
    Build a clean search.json URL.
    You can add/remove filters here anytime.
    """
    params = {
        "base_query": base_query, 
        "offset": str(offset),
        "result_limit": str(result_limit),
        "sort": "recent", # changed to recent to get latest jobs
        "country": "USA",
        "loc_query": "United States",
        
        # Facets that might help
        "normalized_country_code[]": "USA",
        "schedule_type_id[]": "Full-Time",
    }

    # facets[] are optional; they mostly control what the UI shows
    facets = [
        "normalized_country_code",
        "normalized_state_name",
        "normalized_city_name",
        "location",
        "business_category",
        "category",
        "schedule_type_id",
        "employee_class",
        "normalized_location",
        "job_function_id",
        "is_manager",
        "is_intern",
    ]
    # add as repeated params
    query_parts = list(params.items()) + [("facets[]", f) for f in facets]
    full_url = BASE_URL + "?" + urlencode(query_parts, doseq=True)
    print("Requesting:", full_url)
    return full_url

def fetch_json(url):
    # Add Accept-Encoding to explicitly request gzip/deflate, excluding zstd
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json", "Accept-Encoding": "gzip, deflate"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def extract_jobs(payload):
    """
    Amazon's response structure can vary slightly.
    We'll try common keys.
    """
    for k in ["jobs", "search_results", "results", "jobResults"]:
        if k in payload and isinstance(payload[k], list):
            return payload[k]
    # sometimes nested
    if "data" in payload and isinstance(payload["data"], dict):
        return extract_jobs(payload["data"])
    return []

def total_count(payload):
    for k in ["total_hits", "totalHits", "total_results", "count", "total"]:
        if k in payload and isinstance(payload[k], int):
            return payload[k]
    if "data" in payload and isinstance(payload["data"], dict):
        return total_count(payload["data"])
    return None

all_jobs = []
offset = 0
limit = 50

# Pull until no more jobs
while True:
    # Removed explicit "Houston" from base_query to get nationwide
    url = build_url(base_query="data engineer", offset=offset, result_limit=limit, radius="80km")
    data = fetch_json(url)
    jobs = extract_jobs(data)

    if not jobs:
        break

    all_jobs.extend(jobs)
    offset += limit
    time.sleep(SLEEP)

    # optional stop condition if API provides total
    t = total_count(data)
    if isinstance(t, int) and len(all_jobs) >= t:
        break
    
    # Safety break to avoid pulling too many for now
    if len(all_jobs) > 500:
        print("Limit reached (500), stopping...")
        break

print("Total jobs pulled (raw):", len(all_jobs))

df = pd.json_normalize(all_jobs)
df.to_csv("amazon_jobs_raw.csv", index=False)
print("Saved: amazon_jobs_raw.csv")

# --- Filter last 7 days ---
from datetime import datetime, timedelta
import dateutil.parser

def is_recent(date_str):
    if not date_str: return False
    try:
        # Amazon date format ex: "December 30, 2025" or "posted_date"
        d = dateutil.parser.parse(str(date_str))
        # Check if within last 7 days
        return (datetime.now() - d).days <= 7
    except:
        return False

# Filter for recent jobs
# Amazon often puts date in 'posted_date' field
if 'posted_date' in df.columns:
    df_recent = df[df['posted_date'].apply(is_recent)].copy()
else:
    print("Warning: 'posted_date' column not found, skipping date filter.")
    df_recent = df.copy()

print(f"Filtered to {len(df_recent)} jobs posted in the last 7 days.")

# Save JSON for the UI
# Use shared util to handling saving and filtering
save_jobs(df_recent.to_dict(orient="records"))

df_recent.head(20)

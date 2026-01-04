import requests
import json

BASE_URL = "https://apply.careers.microsoft.com/api/pcsx/search"

params = {
    "domain": "microsoft.com",
    "query": "Data Engineer",
    "location": "United States",
    "sort_by": "timestamp",
    "start": "0"
}

try:
    r = requests.get(BASE_URL, params=params, timeout=10)
    data = r.json()
    jobs = data.get("data", {}).get("positions", [])
    
    if jobs:
        j = jobs[0]
        print("ID:", j.get("id"))
        print("Name:", j.get("name"))
        print("Position URL:", j.get("positionUrl"))
        print("Raw Job:", json.dumps(j, indent=2))
    else:
        print("No jobs found")

except Exception as e:
    print(e)

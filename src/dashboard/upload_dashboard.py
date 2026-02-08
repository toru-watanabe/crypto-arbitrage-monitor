import json
import requests
import time
import os

GRAFANA_URL = "http://localhost:3000"
AUTH = ("admin", "admin")
DASHBOARD_PATH = "grafana/dashboards/arbitrage_monitor.json"

def main():
    print("Waiting for Grafana to be ready...")
    for _ in range(30):
        try:
            r = requests.get(f"{GRAFANA_URL}/api/health", timeout=2)
            if r.status_code == 200:
                print("Grafana is UP!")
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
    else:
        print("Timeout waiting for Grafana")
        return

    # Load dashboard JSON
    with open(DASHBOARD_PATH, "r") as f:
        dashboard_data = json.load(f)

    # Prepare payload
    # Grafana API requires wrapper: { "dashboard": { ... }, "overwrite": true }
    payload = {
        "dashboard": dashboard_data,
        "overwrite": True,
        "folderId": 0  # General folder
    }

    # Set ID to null to force new creation (or let overwrite handle it)
    dashboard_data["id"] = None

    print(f"Uploading dashboard from {DASHBOARD_PATH}...")
    try:
        r = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=payload,
            auth=AUTH,
            headers={"Content-Type": "application/json"}
        )
        
        if r.status_code == 200:
            print("SUCCESS! Dashboard imported.")
            print(f"Response: {r.json()}")
        else:
            print(f"FAILED (Status {r.status_code}): {r.text}")
            
    except Exception as e:
        print(f"Error uploading: {e}")

if __name__ == "__main__":
    main()

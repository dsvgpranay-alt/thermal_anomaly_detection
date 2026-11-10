import json
import requests
from pathlib import Path
BASE_URL = "http://127.0.0.1:5000"
file_path = Path(__file__).parent / "sample_data.json"

with open(file_path, "r") as file:
    data = json.load(file)

print("\nLoading Assets...")

existing_response = requests.get(f"{BASE_URL}/assets")
existing_assets = existing_response.json()

existing_ids = [asset["asset_id"] for asset in existing_assets]

for asset in data["assets"]:

    if asset["asset_id"] in existing_ids:
        print(f'{asset["asset_id"]} already exists. Skipping.')
        continue

    response = requests.post(
        f"{BASE_URL}/assets",
        json=asset
    )

    print(asset["asset_id"], response.status_code, response.json())

print("\nLoading Inspections...")

for inspection in data["inspections"]:

    payload = inspection.copy()

    # Add a unique, repeatable idempotency key
    payload["idempotency_key"] = (
        f'{inspection["asset_id"]}-{inspection["timestamp"]}'
    )

    response = requests.post(
        f"{BASE_URL}/inspections",
        json=payload
    )

    print(
        inspection["asset_id"],
        response.status_code,
        response.json()
    )

print("\nGenerated Open Alerts:")

response = requests.get(f"{BASE_URL}/alerts")

print(json.dumps(response.json(), indent=4))

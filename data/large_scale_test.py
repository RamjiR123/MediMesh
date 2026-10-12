import json
import random
import sys
from datetime import datetime, timedelta
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8000"


def call_api(path, method="GET", data=None, params=None):
    url = BASE_URL.rstrip("/") + path
    if params:
        url = f"{url}?{urlencode(params)}"
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except HTTPError as exc:
        print(f"HTTP {exc.code} {method} {url}")
        try:
            print(exc.read().decode("utf-8"))
        except Exception:
            pass
        raise
    except URLError as exc:
        print(f"Connection error calling {url}: {exc}")
        raise


def generate_patient_records(count=1000, days=7):
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=days)
    records = []

    for patient_id in range(1, count + 1):
        offset_minutes = random.randint(0, days * 24 * 60 - 1)
        arrival_time = start + timedelta(minutes=offset_minutes)
        department = random.choices(["ER", "ICU", "General"], weights=[0.45, 0.15, 0.40], k=1)[0]
        acuity_level = random.choices([1, 2, 3, 4, 5], weights=[0.10, 0.20, 0.30, 0.25, 0.15], k=1)[0]

        records.append({
            "patient_id": patient_id,
            "arrival_time": arrival_time.isoformat(),
            "acuity_level": int(acuity_level),
            "department": department,
        })

    return records


def create_patients(records, batch_size=100):
    created = 0
    for index, record in enumerate(records, start=1):
        call_api("/patients", method="POST", data=record)
        created += 1
        if index % batch_size == 0:
            print(f"Created {index}/{len(records)} patients")
            sleep(0.05)
    return created


def run_large_scale_test():
    print("Large-scale test for MediMesh demo")
    print(f"Using API base URL: {BASE_URL}")

    print("\nStep 1: Generate 1000 synthetic patients")
    patients = generate_patient_records(count=1000, days=7)
    print(f"Generated {len(patients)} patients")

    print("\nStep 2: Create patient records in the API")
    created = create_patients(patients)
    print(f"Created {created} patients successfully")

    print("\nStep 3: Initialize predictive models")
    init_response = call_api("/predictive/init", method="POST", data={})
    print("Predictive init response:")
    print(json.dumps(init_response, indent=2))

    print("\nStep 4: Request 48-hour bed occupancy forecast")
    occupancy = call_api("/predictive/bed-occupancy", method="GET", params={"hours_ahead": 48})
    print(f"Forecast rows: {len(occupancy.get('predicted_occupancy', []))}")
    print(f"Sample values: {occupancy['predicted_occupancy'][:8]}")

    print("\nStep 5: Verify ER wait prediction on a new patient")
    sample_input = {
        "patient_id": 1001,
        "arrival_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "acuity_level": 4,
        "department": "ER",
    }
    prediction = call_api("/predictive/er-wait", method="POST", data=sample_input)
    print("ER wait prediction result:")
    print(json.dumps(prediction, indent=2))

    print("\nStep 6: Fetch health metrics for occupancy summary")
    metrics = call_api("/health/metrics", method="GET")
    print(json.dumps(metrics, indent=2))

    print("\nLarge-scale test completed successfully.")


if __name__ == "__main__":
    run_large_scale_test()

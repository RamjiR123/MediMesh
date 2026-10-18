from math import ceil

import pandas as pd


def forecast_staffing_demand(patient_rows, hours_ahead=24, patients_per_staff=4, department=None, now=None):
    if not 1 <= hours_ahead <= 72 or not 1 <= patients_per_staff <= 20:
        raise ValueError("hours_ahead must be 1-72 and patients_per_staff must be 1-20")
    history = pd.DataFrame(patient_rows)
    if history.empty:
        raise ValueError("No valid arrivals available for this forecast")
    if "arrival_time" not in history or (department and "department" not in history):
        raise ValueError("Patient arrival history is required for this forecast")
    if department:
        history = history[history["department"].astype(str).str.casefold() == department.casefold()]

    arrivals = pd.to_datetime(history["arrival_time"], errors="coerce", utc=True).dropna().dt.floor("h")
    if arrivals.empty:
        raise ValueError("No valid arrivals available for this forecast")
    latest = arrivals.max()
    start = max(arrivals.min(), latest - pd.Timedelta(days=27))
    arrivals = arrivals[arrivals >= start]
    hourly_index = pd.date_range(start=start, end=latest, freq="h")
    hourly_counts = arrivals.value_counts().reindex(hourly_index, fill_value=0)
    weekly_pattern = hourly_counts.groupby([hourly_index.dayofweek, hourly_index.hour]).mean()
    hourly_pattern = hourly_counts.groupby(hourly_index.hour).mean()

    current = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    current = current.tz_localize("UTC") if current.tzinfo is None else current.tz_convert("UTC")
    slots = pd.date_range(current.floor("h") + pd.Timedelta(hours=1), periods=hours_ahead, freq="h")
    volume = [round(float(weekly_pattern.get((slot.dayofweek, slot.hour), hourly_pattern.get(slot.hour, 0))), 2)
              for slot in slots]
    return {
        "timestamps": [slot.isoformat() for slot in slots],
        "predicted_patient_arrivals": volume,
        "recommended_staff": [ceil(value / patients_per_staff) for value in volume],
        "department": department,
        "patients_per_staff": patients_per_staff,
    }
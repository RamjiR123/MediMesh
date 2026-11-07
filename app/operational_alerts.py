BED_OCCUPANCY_ALERT_THRESHOLD = 90.0
DOCTOR_AVAILABILITY_ALERT_THRESHOLD = 10.0
RECENT_PATIENT_VOLUME_ALERT_THRESHOLD = 50
RECENT_PATIENT_VOLUME_CRITICAL_THRESHOLD = 100
UPCOMING_APPOINTMENT_ALERT_THRESHOLD = 30
UPCOMING_APPOINTMENT_CRITICAL_THRESHOLD = 60


def _safe_float(value, default=0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def normalize_alert_metrics(metrics: dict) -> dict:
    normalized = {}
    for key, default in {
        "bed_occupancy_rate": 0.0,
        "total_doctors": 0,
        "doctor_availability_rate": 100.0,
        "recent_patients_24h": 0,
        "upcoming_appointments_24h": 0,
    }.items():
        value = metrics.get(key, default)
        normalized[key] = _safe_float(value, default) if isinstance(default, float) else int(_safe_float(value, default))
    return normalized


def summarize_alerts(alerts: list[dict]) -> dict:
    summary = {"total": 0, "warning": 0, "critical": 0}
    for alert in alerts:
        summary["total"] += 1
        level = alert.get("level", "warning")
        if level in summary:
            summary[level] += 1
    return summary


def build_operational_alerts(metrics: dict) -> list[dict]:
    alerts = []
    normalized = normalize_alert_metrics(metrics)
    occupancy = normalized["bed_occupancy_rate"]
    if occupancy >= BED_OCCUPANCY_ALERT_THRESHOLD:
        alerts.append({
            "level": "critical",
            "metric": "bed_occupancy_rate",
            "value": occupancy,
            "message": f"Bed occupancy is {occupancy:.1f}%, at or above the 90% threshold.",
        })

    total_doctors = normalized["total_doctors"]
    availability = normalized["doctor_availability_rate"]
    if total_doctors and availability <= DOCTOR_AVAILABILITY_ALERT_THRESHOLD:
        alerts.append({
            "level": "warning",
            "metric": "doctor_availability_rate",
            "value": availability,
            "message": f"Doctor availability is {availability:.1f}%, at or below the 10% threshold.",
        })

    recent_patients = normalized["recent_patients_24h"]
    if recent_patients >= RECENT_PATIENT_VOLUME_ALERT_THRESHOLD:
        level = "critical" if recent_patients >= RECENT_PATIENT_VOLUME_CRITICAL_THRESHOLD else "warning"
        alerts.append({
            "level": level,
            "metric": "recent_patients_24h",
            "value": recent_patients,
            "message": f"Patient volume is {recent_patients} arrivals in the last 24 hours.",
        })

    upcoming_appointments = normalized["upcoming_appointments_24h"]
    if upcoming_appointments >= UPCOMING_APPOINTMENT_ALERT_THRESHOLD:
        level = "critical" if upcoming_appointments >= UPCOMING_APPOINTMENT_CRITICAL_THRESHOLD else "warning"
        alerts.append({
            "level": level,
            "metric": "upcoming_appointments_24h",
            "value": upcoming_appointments,
            "message": f"{upcoming_appointments} appointments are scheduled in the next 24 hours.",
        })
    return alerts
BED_OCCUPANCY_ALERT_THRESHOLD = 90.0
DOCTOR_AVAILABILITY_ALERT_THRESHOLD = 10.0


def build_operational_alerts(metrics: dict) -> list[dict]:
    alerts = []
    occupancy = metrics.get("bed_occupancy_rate", 0)
    if occupancy >= BED_OCCUPANCY_ALERT_THRESHOLD:
        alerts.append({
            "level": "critical",
            "metric": "bed_occupancy_rate",
            "value": occupancy,
            "message": f"Bed occupancy is {occupancy:.1f}%, at or above the 90% threshold.",
        })

    total_doctors = metrics.get("total_doctors", 0)
    availability = metrics.get("doctor_availability_rate", 100)
    if total_doctors and availability <= DOCTOR_AVAILABILITY_ALERT_THRESHOLD:
        alerts.append({
            "level": "warning",
            "metric": "doctor_availability_rate",
            "value": availability,
            "message": f"Doctor availability is {availability:.1f}%, at or below the 10% threshold.",
        })
    return alerts
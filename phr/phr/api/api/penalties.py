import frappe
from datetime import datetime, time, timedelta


def _normalize_time(value, base_date):
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        return (datetime.combine(base_date, time.min) + value).time()
    if isinstance(value, str):
        return datetime.strptime(value[:8], "%H:%M:%S").time()
    return time.min


@frappe.whitelist()
def process_attendance_penalty_simple(employee: str, checkin_time: str, log_type: str, shift_type: str):
    try:
        shift = frappe.get_doc("Shift Type", shift_type)
    except Exception:
        return {"penalty_created": False, "reason": "Shift type not found"}

    try:
        checkin_dt = datetime.fromisoformat(checkin_time.replace('Z', '+00:00'))
    except Exception:
        return {"penalty_created": False, "reason": "Invalid checkin_time"}

    start_t = _normalize_time(shift.start_time, checkin_dt.date())
    end_t = _normalize_time(shift.end_time, checkin_dt.date())

    checkin_t = checkin_dt.time()

    if log_type == "IN":
        checkin_dt_norm = datetime.combine(checkin_dt.date(), checkin_t)
        start_dt_norm = datetime.combine(checkin_dt.date(), start_t)
        if checkin_dt_norm <= start_dt_norm:
            return {"penalty_created": False, "penalty_type": None, "penalty_reason": "On time or early"}
        late_min = (checkin_dt_norm - start_dt_norm).total_seconds() / 60
        if 15 <= late_min < 30:
            return {"penalty_created": True, "penalty_type": "Late Arrival 15-30 Minutes", "penalty_reason": f"Late by {int(late_min)}m"}
        if 30 <= late_min < 45:
            return {"penalty_created": True, "penalty_type": "Late Arrival 30-45 Minutes", "penalty_reason": f"Late by {int(late_min)}m"}
        if 45 <= late_min < 75:
            return {"penalty_created": True, "penalty_type": "Late Arrival 45-75 Minutes", "penalty_reason": f"Late by {int(late_min)}m"}
        if late_min >= 75:
            return {"penalty_created": True, "penalty_type": "Late Arrival above 75 Minutes", "penalty_reason": f"Late by {int(late_min)}m"}
        return {"penalty_created": False, "penalty_type": None, "penalty_reason": "Grace (<15m)"}

    # OUT
    checkin_dt_norm = datetime.combine(checkin_dt.date(), checkin_t)
    end_dt_norm = datetime.combine(checkin_dt.date(), end_t)
    if checkin_dt_norm >= end_dt_norm:
        return {"penalty_created": False, "penalty_type": None, "penalty_reason": "On time or late"}
    early_min = (end_dt_norm - checkin_dt_norm).total_seconds() / 60
    if early_min > 15:
        return {"penalty_created": True, "penalty_type": "Early Left above 15 Minutes", "penalty_reason": f"Early by {int(early_min)}m"}
    return {"penalty_created": False, "penalty_type": None, "penalty_reason": "Grace (<=15m)"}



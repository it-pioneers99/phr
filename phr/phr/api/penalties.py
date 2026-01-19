import frappe
from frappe import _
from frappe.utils import getdate, add_days
from datetime import datetime, time, timedelta, date


def _normalize_time(value, base_date):
    """Return datetime.time from Frappe Time which may be datetime.timedelta, datetime.time or str."""
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        return (datetime.combine(base_date, time.min) + value).time()
    if isinstance(value, str):
        # 'HH:MM:SS' or 'HH:MM:SS.ffffff'
        return datetime.strptime(value[:8], "%H:%M:%S").time()
    return time.min


def _month_bounds(d: date) -> tuple[date, date]:
    start = date(d.year, d.month, 1)
    if d.month == 12:
        end = date(d.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(d.year, d.month + 1, 1) - timedelta(days=1)
    return start, end


def _classify(shift, checkin_dt: datetime, log_type: str):
    start_t = _normalize_time(shift.start_time, checkin_dt.date())
    end_t = _normalize_time(shift.end_time, checkin_dt.date())
    checkin_t = checkin_dt.time()
    if log_type == "IN":
        checkin_dt_norm = datetime.combine(checkin_dt.date(), checkin_t)
        start_dt_norm = datetime.combine(checkin_dt.date(), start_t)
        if checkin_dt_norm <= start_dt_norm:
            return None, "On time or early"
        late_min = (checkin_dt_norm - start_dt_norm).total_seconds() / 60
        if 15 <= late_min < 30:
            return "Late Arrival 15-30 Minutes", f"Late by {int(late_min)}m"
        if 30 <= late_min < 45:
            return "Late Arrival 30-45 Minutes", f"Late by {int(late_min)}m"
        if 45 <= late_min < 75:
            return "Late Arrival 45-75 Minutes", f"Late by {int(late_min)}m"
        if late_min >= 75:
            return "Late Arrival above 75 Minutes", f"Late by {int(late_min)}m"
        return None, "Grace (<15m)"
    else:
        checkin_dt_norm = datetime.combine(checkin_dt.date(), checkin_t)
        end_dt_norm = datetime.combine(checkin_dt.date(), end_t)
        if checkin_dt_norm >= end_dt_norm:
            return None, "On time or late"
        early_min = (end_dt_norm - checkin_dt_norm).total_seconds() / 60
        if early_min > 15:
            return "Early Left above 15 Minutes", f"Early by {int(early_min)}m"
        return None, "Grace (<=15m)"


def _compute_progressive_level(employee: str, penalty_type: str, penalty_date: date) -> int:
    """
    Progression based on penalty period (day 21 to day 20 of next month).
    Counts violations within the current penalty period (30 days).
    If employee reaches last level (4th), subsequent violations in same period use last level.
    """
    # Calculate penalty period (day 21 to day 20 of next month)
    if penalty_date.day >= 21:
        # Period starts on day 21 of current month
        period_start = penalty_date.replace(day=21)
        # Period ends on day 20 of next month
        if penalty_date.month == 12:
            period_end = penalty_date.replace(year=penalty_date.year + 1, month=1, day=20)
        else:
            period_end = penalty_date.replace(month=penalty_date.month + 1, day=20)
    else:
        # If before day 21, period is from day 21 of previous month to day 20 of current month
        if penalty_date.month == 1:
            period_start = penalty_date.replace(year=penalty_date.year - 1, month=12, day=21)
        else:
            period_start = penalty_date.replace(month=penalty_date.month - 1, day=21)
        period_end = penalty_date.replace(day=20)
    
    # Count previous violations of same type within current penalty period
    existing_count = frappe.db.count(
        "Penalty Record",
        filters={
            "employee": employee,
            "violation_type": penalty_type,
            "violation_date": [">=", period_start],
            "violation_date": ["<=", period_end],
            "violation_date": ["<", penalty_date],  # Exclude current violation
            "docstatus": 1  # Only count submitted/approved records
        },
    )
    
    # Get the maximum level defined for this penalty type
    max_level = _get_max_penalty_level(penalty_type)
    
    # Calculate occurrence number (1st, 2nd, 3rd, 4th+)
    occurrence_number = int(existing_count) + 1

    # If occurrence exceeds max level, use max level (don't go beyond)
    if occurrence_number > max_level:
        occurrence_number = max_level
    
    return occurrence_number

def _get_max_penalty_level(penalty_type: str) -> int:
    """Get the maximum penalty level (occurrence_number) defined for a penalty type"""
    try:
        penalty_type_doc = frappe.get_doc("Penalty Type", penalty_type)
        if penalty_type_doc.penalty_levels:
            max_level = max([level.occurrence_number or 0 for level in penalty_type_doc.penalty_levels])
            return max_level if max_level > 0 else 4  # Default to 4 if no levels found
        return 4  # Default maximum level
    except Exception:
        return 4  # Default maximum level


def _get_percentage_for_level(penalty_type_doc_name: str, level: int) -> float:
    """
    Get penalty percentage value for a specific level from Penalty Type.
    Returns the penalty_value_level for the matching occurrence_number.
    """
    try:
        # Get Penalty Type document
        penalty_type_doc = frappe.get_doc("Penalty Type", penalty_type_doc_name)
        
        if not penalty_type_doc.penalty_levels:
            return 0.0
        
        # Find matching level by occurrence_number
        for level_row in penalty_type_doc.penalty_levels:
            if level_row.occurrence_number == level:
                return float(level_row.penalty_value_level or 0)
        
        # If no exact match, use the highest defined level
        if penalty_type_doc.penalty_levels:
            highest_level = max(penalty_type_doc.penalty_levels, key=lambda x: x.occurrence_number or 0)
            return float(highest_level.penalty_value_level or 0)
        
        return 0.0
        
    except Exception as e:
        frappe.log_error(f"Error getting penalty percentage for level {level}: {str(e)}")
        return 0.0


@frappe.whitelist()
def process_attendance_penalty_simple(employee: str, checkin_time: str, log_type: str, shift_type: str):
    """Classify, seed if needed, and create Penalty Record with progressive levels.

    Returns dict with creation details. If no penalty, returns reason.
    """
    try:
        shift = frappe.get_doc("Shift Type", shift_type)
    except Exception:
        return {"penalty_created": False, "reason": "Shift type not found"}

    try:
        checkin_dt = datetime.fromisoformat(checkin_time.replace('Z', '+00:00'))
    except Exception:
        return {"penalty_created": False, "reason": "Invalid checkin_time"}

    # Use existing Penalty Types/Levels only (no auto-seeding)

    penalty_type, penalty_reason = _classify(shift, checkin_dt, log_type)
    if not penalty_type:
        return {"penalty_created": False, "penalty_type": None, "penalty_reason": penalty_reason}

    # Find Penalty Type document by penalty_type field value
    penalty_type_doc_name = frappe.db.exists("Penalty Type", {"penalty_type": penalty_type})
    if not penalty_type_doc_name:
        frappe.log_error(
            f"Penalty Type '{penalty_type}' not found in database",
            "Penalty Record Creation"
        )
        return {
            "penalty_created": False,
            "reason": f"Penalty Type '{penalty_type}' not found"
        }
    
    # progressive level per policy (penalty period: day 21 to day 20 of next month)
    occurrence_level = _compute_progressive_level(employee, penalty_type_doc_name, checkin_dt.date())
    penalty_percentage = _get_percentage_for_level(penalty_type_doc_name, occurrence_level)

    # Map to site's Penalty Record schema
    violation_date = checkin_dt.date()
    violation_type = penalty_type
    violation_description = penalty_reason
    lateness_minutes = 0
    early_minutes = 0
    if log_type == "IN":
        # compute minutes late
        start_t = _normalize_time(shift.start_time, checkin_dt.date())
        late_min = int((datetime.combine(checkin_dt.date(), checkin_dt.time()) - datetime.combine(checkin_dt.date(), start_t)).total_seconds() // 60)
        lateness_minutes = max(late_min, 0)
    else:
        end_t = _normalize_time(shift.end_time, checkin_dt.date())
        early_min = int((datetime.combine(checkin_dt.date(), end_t) - datetime.combine(checkin_dt.date(), checkin_dt.time())).total_seconds() // 60)
        early_minutes = max(early_min, 0)

    # The schema has total_penalty_value and penalty_amount (decimals). Use percentage as value for now.
    total_penalty_value = float(penalty_percentage)
    penalty_amount = float(penalty_percentage)

    created_name = None
    try:
        # Get Penalty Type document to access penalty levels
        penalty_type_doc = frappe.get_doc("Penalty Type", penalty_type_doc_name)
        
        rec = frappe.new_doc("Penalty Record")
        rec.employee = employee
        rec.violation_date = violation_date
        rec.violation_type = penalty_type_doc_name  # Use document name, not field value
        rec.violation_description = violation_description
        rec.occurrence_number = occurrence_level
        rec.lateness_minutes = lateness_minutes
        rec.early_minutes = early_minutes
        rec.total_penalty_value = total_penalty_value
        rec.penalty_amount = penalty_amount
        
        # Add penalty level to child table
        if penalty_type_doc.penalty_levels:
            # Find the penalty level matching the occurrence number
            matching_level = None
            for level in penalty_type_doc.penalty_levels:
                if level.occurrence_number == occurrence_level:
                    matching_level = level
                    break
            
            if matching_level:
                # Determine penalty type level based on value
                # If value is 0, it's a Warning; otherwise Percentage Deduction
                penalty_type_level = "Warning" if (matching_level.penalty_value_level or 0) == 0 else "Percentage Deduction"
                
                rec.append("penalty_levels", {
                    "occurrence_number": matching_level.occurrence_number,
                    "penalty_type_level": penalty_type_level,
                    "penalty_value_level": matching_level.penalty_value_level or penalty_percentage,
                    "is_percentage_level": matching_level.is_percentage_level or 1
                })
            else:
                # If no exact match, use the highest level or create default
                if penalty_type_doc.penalty_levels:
                    highest_level = max(penalty_type_doc.penalty_levels, key=lambda x: x.occurrence_number or 0)
                    penalty_type_level = "Warning" if (highest_level.penalty_value_level or 0) == 0 else "Percentage Deduction"
                    
                    rec.append("penalty_levels", {
                        "occurrence_number": occurrence_level,
                        "penalty_type_level": penalty_type_level,
                        "penalty_value_level": penalty_percentage,
                        "is_percentage_level": highest_level.is_percentage_level or 1
                    })
                else:
                    # Default fallback
                    rec.append("penalty_levels", {
                        "occurrence_number": occurrence_level,
                        "penalty_type_level": "Percentage Deduction",
                        "penalty_value_level": penalty_percentage,
                        "is_percentage_level": 1
                    })
        
        rec.insert(ignore_permissions=True)
        if getattr(rec, "is_submittable", 0) or getattr(rec.meta, "is_submittable", 0):
            try:
                rec.submit()
            except Exception:
                pass
        created_name = rec.name
    except Exception as e:
        # If doctype missing or fields differ, still return classification
        frappe.log_error(frappe.get_traceback(), _(f"Penalty creation failed: {e}"))

    return {
        "penalty_created": True if created_name else False,
        "penalty_docname": created_name,
        "penalty_type": penalty_type,
        "penalty_reason": penalty_reason,
        "penalty_level": occurrence_level,
        "penalty_percentage": penalty_percentage,
        "lateness_minutes": lateness_minutes,
        "early_minutes": early_minutes,
    }


@frappe.whitelist()
def seed_attendance_penalty_types(shift_type: str | None = None):
    """Public endpoint to seed the 5 attendance penalty types with levels in phr app."""
    # Import the function from the utils module
    from phr.phr.utils.attendance_penalty_detector import setup_attendance_penalty_types
    setup_attendance_penalty_types()
    return {"ok": True}



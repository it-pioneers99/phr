import frappe
from frappe import _

@frappe.whitelist()
def get_pending_checkins_count(from_date=None, to_date=None):
    """Get count of pending checkins that haven't been processed"""
    filters = {
        "attendance": ["is", "not set"],
        "skip_auto_attendance": 0
    }
    
    if from_date:
        filters["time"] = [">=", from_date]
    if to_date:
        if "time" in filters:
            filters["time"] = ["between", [from_date, to_date]]
        else:
            filters["time"] = ["<=", to_date]
    
    count = frappe.db.count("Employee Checkin", filters)
    return count

@frappe.whitelist()
def get_sync_statistics(from_date=None, to_date=None):
    """Get statistics about checkin and attendance sync"""
    filters = {}
    
    if from_date:
        filters["time"] = [">=", from_date]
    if to_date:
        if "time" in filters:
            filters["time"] = ["between", [from_date, to_date]]
        else:
            filters["time"] = ["<=", to_date]
    
    total_checkins = frappe.db.count("Employee Checkin", filters)
    
    filters["attendance"] = ["is", "set"]
    processed_checkins = frappe.db.count("Employee Checkin", filters)
    
    filters = {}
    if from_date:
        filters["attendance_date"] = [">=", from_date]
    if to_date:
        if "attendance_date" in filters:
            filters["attendance_date"] = ["between", [from_date, to_date]]
        else:
            filters["attendance_date"] = ["<=", to_date]
    
    total_attendance = frappe.db.count("Attendance", filters)
    
    return {
        "total_checkins": total_checkins,
        "processed_checkins": processed_checkins,
        "pending_checkins": total_checkins - processed_checkins,
        "total_attendance": total_attendance
    }


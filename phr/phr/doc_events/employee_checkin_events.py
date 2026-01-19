import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, getdate
import datetime

def after_insert(doc, method):
    """
    Automatically trigger attendance processing and penalty detection after Employee Checkin is created.
    This ensures attendance records are created immediately after biometric sync
    and penalties are automatically detected for late/early attendance.
    """
    # Only process if not skipping auto attendance
    if doc.skip_auto_attendance:
        return
    
    try:
        # Enqueue attendance processing to avoid blocking the checkin creation
        frappe.enqueue(
            process_attendance_for_checkin,
            queue='short',
            timeout=300,
            checkin_name=doc.name,
            employee=doc.employee,
            checkin_time=doc.time,
            is_async=True
        )
        
        # Also enqueue penalty detection for attendance violations
        frappe.enqueue(
            detect_attendance_penalties,
            queue='short',
            timeout=300,
            checkin_name=doc.name,
            is_async=True
        )
    except Exception as e:
        # Log error but don't block checkin creation
        frappe.log_error(
            f"Error enqueueing attendance processing for checkin {doc.name}: {str(e)}",
            "Employee Checkin Auto Attendance"
        )

def process_attendance_for_checkin(checkin_name, employee, checkin_time):
    """
    Process attendance for a specific checkin.
    Enhanced to check for leave, travel trips, shift requests, and create penalty records if needed.
    This function runs asynchronously after checkin is created.
    """
    try:
        # Get the checkin document
        checkin = frappe.get_doc("Employee Checkin", checkin_name)
        
        # Skip if already processed
        if checkin.attendance:
            return
        
        attendance_date = getdate(checkin_time)
        
        # Priority 1: Check for approved leave on this date
        approved_leave = check_approved_leave(employee, attendance_date)
        if approved_leave:
            # Get shift for leave marking
            shift = checkin.shift or get_employee_shift_for_date(employee, attendance_date)
            if shift:
                mark_attendance_as_leave(employee, attendance_date, approved_leave, shift)
                frappe.logger().info(
                    f"Marked attendance as On Leave for Employee: {employee}, "
                    f"Date: {attendance_date}, Leave Type: {approved_leave}"
                )
                return
        
        # Priority 2: Check for travel trip
        travel_trip = check_travel_trip(employee, attendance_date)
        if travel_trip:
            shift = checkin.shift or get_employee_shift_for_date(employee, attendance_date)
            if shift:
                mark_attendance_for_travel(employee, attendance_date, travel_trip, shift)
                frappe.logger().info(
                    f"Marked attendance for Travel Trip for Employee: {employee}, "
                    f"Date: {attendance_date}"
                )
                return
        
        # Priority 3: Check for shift request/permission
        shift_request = check_shift_request(employee, attendance_date)
        if shift_request:
            shift = checkin.shift or get_employee_shift_for_date(employee, attendance_date)
            if shift:
                mark_attendance_for_shift_request(employee, attendance_date, shift_request, shift)
                frappe.logger().info(
                    f"Marked attendance for Shift Request for Employee: {employee}, "
                    f"Date: {attendance_date}"
                )
                return
        
        # Priority 4: Check if there's checkin/checkout
        has_checkin = check_has_checkin_checkout(employee, attendance_date)
        if has_checkin:
            # Get the shift for this checkin
            shift = checkin.shift
            
            if not shift:
                # Try to fetch shift if not set
                checkin.fetch_shift()
                checkin.save()
                shift = checkin.shift
            
            if shift:
                # Get the shift type document
                shift_type = frappe.get_doc("Shift Type", shift)
                
                # Check if auto attendance is enabled
                if shift_type.enable_auto_attendance:
                    # Process auto attendance for this shift
                    shift_type.process_auto_attendance()
                    
                    frappe.logger().info(
                        f"Processed auto attendance for Employee: {employee}, "
                        f"Shift: {shift}, Checkin: {checkin_name}"
                    )
            else:
                frappe.logger().warning(
                    f"No shift found for Employee Checkin {checkin_name}. "
                    f"Attendance not automatically created."
                )
        else:
            # Priority 5: No checkin/checkout - create draft penalty record
            shift = checkin.shift or get_employee_shift_for_date(employee, attendance_date)
            if shift:
                create_draft_penalty_record(employee, attendance_date, shift, "No checkin/checkout recorded")
                frappe.logger().info(
                    f"Created draft penalty record for Employee: {employee}, "
                    f"Date: {attendance_date}, Reason: No checkin/checkout"
                )
            
    except Exception as e:
        frappe.log_error(
            f"Error processing attendance for checkin {checkin_name}: {str(e)}",
            "Employee Checkin Auto Attendance Processing"
        )

@frappe.whitelist()
def bulk_process_pending_checkins(from_date=None, to_date=None):
    """
    Manually trigger attendance processing for all pending checkins.
    Useful for processing checkins that were synced while auto-processing was disabled.
    
    Args:
        from_date: Start date for checkin filter (optional)
        to_date: End date for checkin filter (optional)
    """
    try:
        # Build filters
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
        
        # Get all pending checkins
        pending_checkins = frappe.get_all(
            "Employee Checkin",
            filters=filters,
            fields=["name", "employee", "time", "shift"],
            order_by="time asc"
        )
        
        if not pending_checkins:
            frappe.msgprint(_("No pending checkins found to process."))
            return
        
        # Process each checkin
        processed_count = 0
        error_count = 0
        
        for checkin in pending_checkins:
            try:
                process_attendance_for_checkin(
                    checkin.name,
                    checkin.employee,
                    checkin.time
                )
                processed_count += 1
            except Exception as e:
                error_count += 1
                frappe.log_error(
                    f"Error processing checkin {checkin.name}: {str(e)}",
                    "Bulk Checkin Processing"
                )
        
        frappe.db.commit()
        
        frappe.msgprint(
            _(f"Processed {processed_count} checkins successfully. {error_count} errors occurred."),
            title=_("Bulk Processing Complete"),
            indicator="green" if error_count == 0 else "orange"
        )
        
        return {
            "success": True,
            "processed": processed_count,
            "errors": error_count
        }
        
    except Exception as e:
        frappe.log_error(
            f"Error in bulk_process_pending_checkins: {str(e)}",
            "Bulk Checkin Processing"
        )
        frappe.throw(_("Error processing checkins. Please check error log."))


def detect_attendance_penalties(checkin_name):
    """
    Detect and create attendance penalties for a specific checkin.
    This function runs asynchronously after checkin is created.
    
    Args:
        checkin_name: Name of the Employee Checkin document
    """
    try:
        # Get the checkin document
        checkin = frappe.get_doc("Employee Checkin", checkin_name)
        employee = checkin.employee
        checkin_time = checkin.time.isoformat() if hasattr(checkin.time, 'isoformat') else str(checkin.time)
        log_type = (checkin.log_type or '').upper()  # 'IN' or 'OUT'
        shift_type = checkin.shift or 'الفترة الصباحية'

        # Call phr API to classify and create penalty record (mapped to site schema)
        res = frappe.call(
            'phr.phr.api.penalties.process_attendance_penalty_simple',
            employee=employee,
            checkin_time=checkin_time,
            log_type=log_type,
            shift_type=shift_type,
        )

        frappe.logger().info(
            f"Penalty detection for checkin {checkin_name}: {frappe.as_json(res)}"
        )

    except Exception as e:
        frappe.log_error(
            f"Error detecting attendance penalties for checkin {checkin_name}: {str(e)}",
            "Attendance Penalty Detection"
        )

def get_employee_shift_for_date(employee, attendance_date):
    """Get employee's shift for a given date"""
    try:
        from hrms.hr.utils import get_employee_shift
        shift = get_employee_shift(employee, attendance_date)
        return shift.shift_type.name if shift else None
    except:
        return None

def check_travel_trip(employee, attendance_date):
    """Check if employee has an active travel trip on the given date"""
    try:
        # Check if Travel Request doctype exists
        if not frappe.db.exists("DocType", "Travel Request"):
            return None
        
        travel_requests = frappe.get_all("Travel Request",
            filters={
                "employee": employee,
                "travel_from_date": ["<=", attendance_date],
                "travel_to_date": [">=", attendance_date],
                "status": "Approved",
                "docstatus": 1
            },
            fields=["name"],
            limit=1
        )
        
        if travel_requests:
            return travel_requests[0].name
        return None
    except:
        return None

def check_shift_request(employee, attendance_date):
    """Check if employee has an approved shift request/permission on the given date"""
    try:
        # Check Shift Permission Request
        shift_permissions = frappe.get_all("Shift Permission Request",
            filters={
                "employee": employee,
                "permission_date": attendance_date,
                "status": "Approved",
                "docstatus": 1
            },
            fields=["name"],
            limit=1
        )
        
        if shift_permissions:
            return shift_permissions[0].name
        
        # Check Attendance Request if exists
        if frappe.db.exists("DocType", "Attendance Request"):
            attendance_requests = frappe.get_all("Attendance Request",
                filters={
                    "employee": employee,
                    "from_date": ["<=", attendance_date],
                    "to_date": [">=", attendance_date],
                    "status": "Approved",
                    "docstatus": 1
                },
                fields=["name"],
                limit=1
            )
            
            if attendance_requests:
                return attendance_requests[0].name
        
        return None
    except:
        return None

def check_has_checkin_checkout(employee, attendance_date):
    """Check if employee has checkin or checkout on the given date"""
    try:
        checkins = frappe.get_all("Employee Checkin",
            filters={
                "employee": employee,
                "time": ["between", [f"{attendance_date} 00:00:00", f"{attendance_date} 23:59:59"]]
            },
            fields=["name"],
            limit=1
        )
        
        return len(checkins) > 0
    except:
        return False

def mark_attendance_for_travel(employee, attendance_date, travel_trip, shift):
    """Mark attendance for travel trip"""
    try:
        existing_attendance = frappe.db.exists("Attendance", {
            "employee": employee,
            "attendance_date": attendance_date,
            "shift": shift
        })
        
        if existing_attendance:
            attendance = frappe.get_doc("Attendance", existing_attendance)
            attendance.status = "On Leave"
            attendance.save()
            frappe.db.commit()
        else:
            attendance = frappe.new_doc("Attendance")
            attendance.employee = employee
            attendance.attendance_date = attendance_date
            attendance.status = "On Leave"
            attendance.shift = shift
            attendance.insert()
            attendance.submit()
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            f"Error marking attendance for travel for {employee} on {attendance_date}: {str(e)}",
            "Attendance Travel Marking"
        )

def mark_attendance_for_shift_request(employee, attendance_date, shift_request, shift):
    """Mark attendance for shift request/permission"""
    try:
        existing_attendance = frappe.db.exists("Attendance", {
            "employee": employee,
            "attendance_date": attendance_date,
            "shift": shift
        })
        
        if existing_attendance:
            attendance = frappe.get_doc("Attendance", existing_attendance)
            attendance.status = "Present"
            attendance.save()
            frappe.db.commit()
        else:
            attendance = frappe.new_doc("Attendance")
            attendance.employee = employee
            attendance.attendance_date = attendance_date
            attendance.status = "Present"
            attendance.shift = shift
            attendance.insert()
            attendance.submit()
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            f"Error marking attendance for shift request for {employee} on {attendance_date}: {str(e)}",
            "Attendance Shift Request Marking"
        )

def create_draft_penalty_record(employee, attendance_date, shift, reason):
    """Create a draft penalty record for absence"""
    try:
        # Check if penalty record already exists
        existing = frappe.db.exists("Penalty Record", {
            "employee": employee,
            "violation_date": attendance_date,
            "penalty_status": "Draft"
        })
        
        if existing:
            return
        
        # Get default penalty type for absence (if exists)
        penalty_type = frappe.db.get_value("Penalty Type", {"penalty_type": "Absent"}, "name")
        
        if not penalty_type:
            # Try to find any penalty type
            penalty_type = frappe.db.get_value("Penalty Type", {}, "name")
        
        if penalty_type:
            penalty_record = frappe.new_doc("Penalty Record")
            penalty_record.employee = employee
            penalty_record.violation_date = attendance_date
            penalty_record.violation_type = penalty_type
            penalty_record.violation_description = reason
            penalty_record.penalty_status = "Draft"
            penalty_record.insert()
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            f"Error creating draft penalty record for {employee} on {attendance_date}: {str(e)}",
            "Draft Penalty Record Creation"
        )

def check_approved_leave(employee, attendance_date):
    """
    Check if employee has approved leave on the given date
    
    Args:
        employee: Employee ID
        attendance_date: Date to check for leave
        
    Returns:
        str: Leave type name if approved leave exists, None otherwise
    """
    try:
        # Check for approved leave applications on this date
        leave_applications = frappe.get_all("Leave Application",
            filters={
                "employee": employee,
                "from_date": ["<=", attendance_date],
                "to_date": [">=", attendance_date],
                "status": "Approved",
                "docstatus": 1
            },
            fields=["leave_type"],
            limit=1
        )
        
        if leave_applications:
            return leave_applications[0].leave_type
        
        return None
        
    except Exception as e:
        frappe.log_error(
            f"Error checking approved leave for {employee} on {attendance_date}: {str(e)}",
            "Leave Check"
        )
        return None

def mark_attendance_as_leave(employee, attendance_date, leave_type, shift):
    """
    Mark attendance as On Leave for the given employee and date
    
    Args:
        employee: Employee ID
        attendance_date: Date of attendance
        leave_type: Leave type name
        shift: Shift name
    """
    try:
        # Check if attendance already exists
        existing_attendance = frappe.db.exists("Attendance", {
            "employee": employee,
            "attendance_date": attendance_date,
            "shift": shift
        })
        
        if existing_attendance:
            # Update existing attendance
            attendance = frappe.get_doc("Attendance", existing_attendance)
            attendance.status = "On Leave"
            attendance.leave_type = leave_type
            attendance.save()
            frappe.db.commit()
        else:
            # Create new attendance record
            attendance = frappe.new_doc("Attendance")
            attendance.employee = employee
            attendance.attendance_date = attendance_date
            attendance.status = "On Leave"
            attendance.leave_type = leave_type
            attendance.shift = shift
            attendance.insert()
            attendance.submit()
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error(
            f"Error marking attendance as leave for {employee} on {attendance_date}: {str(e)}",
            "Attendance Leave Marking"
        )

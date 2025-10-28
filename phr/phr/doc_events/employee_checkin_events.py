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
    This function runs asynchronously after checkin is created.
    """
    try:
        # Get the checkin document
        checkin = frappe.get_doc("Employee Checkin", checkin_name)
        
        # Skip if already processed
        if checkin.attendance:
            return
        
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
                # Check for approved leave on this date
                attendance_date = getdate(checkin_time)
                approved_leave = check_approved_leave(employee, attendance_date)
                
                if approved_leave:
                    # Mark attendance as On Leave instead of Absent
                    mark_attendance_as_leave(employee, attendance_date, approved_leave, shift)
                    frappe.logger().info(
                        f"Marked attendance as On Leave for Employee: {employee}, "
                        f"Date: {attendance_date}, Leave Type: {approved_leave}"
                    )
                else:
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

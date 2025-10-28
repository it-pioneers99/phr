"""
PHR Employee Summary Scheduled Tasks
Handles daily calculations and notifications
"""

import frappe
from frappe import _
from frappe.utils import getdate, today, add_days
from ..employee_summary_calculator import calculate_employee_summary


def daily_employee_summary_calculation():
    """Daily task to calculate employee summaries and send notifications"""
    try:
        # Get all active employees
        active_employees = frappe.get_all("Employee",
            filters={"status": "Active"},
            fields=["name", "employee_name", "date_of_joining"]
        )
        
        processed_count = 0
        error_count = 0
        
        for emp in active_employees:
            try:
                result = calculate_employee_summary(emp.name)
                if result['success']:
                    processed_count += 1
                else:
                    error_count += 1
                    frappe.log_error(f"Error processing employee {emp.name}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                error_count += 1
                frappe.log_error(f"Exception processing employee {emp.name}: {str(e)}")
        
        # Log summary
        frappe.logger().info(f"Daily employee summary calculation completed. Processed: {processed_count}, Errors: {error_count}")
        
        return {
            "success": True,
            "processed": processed_count,
            "errors": error_count
        }
        
    except Exception as e:
        frappe.log_error(f"Daily employee summary calculation failed: {str(e)}")
        return {"success": False, "error": str(e)}


def send_test_period_notifications():
    """Send notifications for employees whose test period is ending soon"""
    try:
        # Get employees with test period ending in 60 days (120 days from joining)
        employees_60_days = frappe.get_all("Employee",
            filters={
                "status": "Active",
                "remaining_testing_days": 120
            },
            fields=["name", "employee_name", "date_of_joining"]
        )
        
        # Get employees with test period ending in 30 days (150 days from joining)
        employees_30_days = frappe.get_all("Employee",
            filters={
                "status": "Active",
                "remaining_testing_days": 30
            },
            fields=["name", "employee_name", "date_of_joining"]
        )
        
        notifications_sent = 0
        
        # Send 60-day notifications
        for emp in employees_60_days:
            send_test_period_notification(emp, "60 days", "Test period will end in 60 days (120 days from today)")
            notifications_sent += 1
        
        # Send 30-day notifications
        for emp in employees_30_days:
            send_test_period_notification(emp, "30 days", "Test period will end in 1 month (30 days from today)")
            notifications_sent += 1
        
        frappe.logger().info(f"Test period notifications sent: {notifications_sent}")
        
        return {
            "success": True,
            "notifications_sent": notifications_sent
        }
        
    except Exception as e:
        frappe.log_error(f"Test period notifications failed: {str(e)}")
        return {"success": False, "error": str(e)}


def send_test_period_notification(employee, days_remaining, message):
    """Send individual test period notification"""
    try:
        # Create ToDo for HR team
        todo = frappe.new_doc("ToDo")
        todo.description = f"Employee {employee.employee_name} - {message}"
        todo.reference_type = "Employee"
        todo.reference_name = employee.name
        todo.assigned_by = "Administrator"
        todo.priority = "High"
        todo.insert()
        
        # Send email notification
        frappe.sendmail(
            recipients=["hr@pioneersholding.ae"],  # Update with actual HR email
            subject=f"Test Period Notification - {employee.employee_name} ({days_remaining} remaining)",
            message=f"""
            <h3>Test Period Notification</h3>
            <p><strong>Employee:</strong> {employee.employee_name}</p>
            <p><strong>Employee ID:</strong> {employee.name}</p>
            <p><strong>Joining Date:</strong> {employee.date_of_joining}</p>
            <p><strong>Message:</strong> {message}</p>
            <p>Please review the employee's performance and make necessary decisions regarding their employment status.</p>
            """,
            reference_doctype="Employee",
            reference_name=employee.name
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send notification for employee {employee.name}: {str(e)}")


def cleanup_old_notifications():
    """Clean up old notifications and logs"""
    try:
        # Delete ToDos older than 30 days
        frappe.db.sql("""
            DELETE FROM `tabToDo` 
            WHERE reference_type = 'Employee' 
            AND description LIKE '%Test period%'
            AND creation < DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        
        frappe.db.commit()
        
        return {"success": True, "message": "Old notifications cleaned up"}
        
    except Exception as e:
        frappe.log_error(f"Cleanup failed: {str(e)}")
        return {"success": False, "error": str(e)}


def generate_weekly_leave_report():
    """Generate weekly leave balance report for HR team"""
    try:
        from ..api.employee_summary import get_leave_balance_report
        
        report_data = get_leave_balance_report()
        
        if report_data['success']:
            # Create a report document
            report = frappe.new_doc("Report")
            report.report_name = f"Weekly Leave Balance Report - {today()}"
            report.module = "PHR"
            report.report_type = "Query Report"
            report.is_standard = "No"
            report.report_json = {
                "filters": [],
                "columns": [
                    {"fieldname": "employee_name", "label": "Employee Name"},
                    {"fieldname": "years_of_service", "label": "Years of Service"},
                    {"fieldname": "annual_leave_remaining", "label": "Annual Leave Remaining"},
                    {"fieldname": "sick_leave_remaining", "label": "Sick Leave Remaining"},
                    {"fieldname": "test_period_remaining", "label": "Test Period Remaining"}
                ],
                "data": report_data['data']
            }
            report.insert()
            
            # Send email with report
            frappe.sendmail(
                recipients=["hr@pioneersholding.ae"],
                subject=f"Weekly Leave Balance Report - {today()}",
                message=f"""
                <h3>Weekly Leave Balance Report</h3>
                <p>Please find attached the weekly leave balance report for all active employees.</p>
                <p>Report ID: {report.name}</p>
                """,
                attachments=[{
                    "fname": f"leave_report_{today()}.json",
                    "fcontent": str(report_data['data'])
                }]
            )
            
            return {"success": True, "report_id": report.name}
        
    except Exception as e:
        frappe.log_error(f"Weekly report generation failed: {str(e)}")
        return {"success": False, "error": str(e)}

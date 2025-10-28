import frappe
from frappe.utils import getdate, add_days, today, date_diff
from frappe import _

@frappe.whitelist()
def check_contract_end_notifications():
    """
    Check for employees whose contracts are ending in 90 days and send notifications
    This function is called daily by the scheduler
    """
    try:
        # Get employees with contracts ending in 90 days
        notification_date = add_days(today(), 90)
        
        employees = frappe.get_all("Employee",
            filters={
                "contract_end_date": ["<=", notification_date],
                "contract_end_date": [">=", today()],
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date", "user_id", "company_email"]
        )
        
        notifications_sent = 0
        errors = []
        
        for employee in employees:
            days_remaining = date_diff(employee.contract_end_date, today())
            
            if days_remaining <= 90 and days_remaining > 0:
                try:
                    # Create notification
                    create_contract_notification(employee, days_remaining)
                    notifications_sent += 1
                except Exception as e:
                    error_msg = f"Error creating notification for {employee.employee_name}: {str(e)}"
                    errors.append(error_msg)
                    frappe.log_error(error_msg)
        
        # Log summary
        if notifications_sent > 0:
            frappe.logger().info(f"Contract notifications sent to {notifications_sent} employees")
        
        return {
            "status": "success",
            "message": f"Contract notifications processed. Sent: {notifications_sent}, Errors: {len(errors)}",
            "notifications_sent": notifications_sent,
            "errors": errors
        }
        
    except Exception as e:
        error_msg = f"Error in contract notification check: {str(e)}"
        frappe.log_error(error_msg)
        return {"status": "error", "message": error_msg}

def create_contract_notification(employee, days_remaining):
    """
    Create a notification for contract ending
    """
    try:
        # Create a ToDo for HR team
        todo = frappe.get_doc({
            "doctype": "ToDo",
            "description": f"Employee {employee.employee_name} contract ends in {days_remaining} days on {employee.contract_end_date}",
            "reference_type": "Employee",
            "reference_name": employee.name,
            "assigned_by": "Administrator",
            "priority": "High" if days_remaining <= 30 else "Medium",
            "status": "Open"
        })
        todo.insert()
        
        # Send email notification if user exists or has company email
        if employee.user_id or employee.company_email:
            send_contract_email_notification(employee, days_remaining)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating contract notification: {str(e)}")
        raise

def send_contract_email_notification(employee, days_remaining):
    """
    Send email notification for contract ending
    """
    try:
        # Determine recipient
        recipient = employee.company_email if employee.company_email else None
        if not recipient and employee.user_id:
            user_doc = frappe.get_doc("User", employee.user_id)
            recipient = user_doc.email
        
        if not recipient:
            # Default to HR email if no employee email
            recipient = "hr@pioneersholding.ae"
        
        subject = f"Contract End Notification - {employee.employee_name}"
        
        # Create different messages based on days remaining
        if days_remaining <= 30:
            urgency = "URGENT"
            action_required = "immediate action"
        elif days_remaining <= 60:
            urgency = "HIGH PRIORITY"
            action_required = "prompt action"
        else:
            urgency = "NOTIFICATION"
            action_required = "planning"
        
        message = f"""
        <h2>{urgency}: Contract End Notification</h2>
        
        <p>Dear HR Team,</p>
        
        <p>This is to notify you that the contract of employee <strong>{employee.employee_name}</strong> 
        will end in <strong>{days_remaining} days</strong> on <strong>{employee.contract_end_date}</strong>.</p>
        
        <p><strong>Action Required:</strong> Please take {action_required} regarding contract renewal or termination procedures.</p>
        
        <h3>Employee Details:</h3>
        <ul>
            <li><strong>Name:</strong> {employee.employee_name}</li>
            <li><strong>Employee ID:</strong> {employee.name}</li>
            <li><strong>Contract End Date:</strong> {employee.contract_end_date}</li>
            <li><strong>Days Remaining:</strong> {days_remaining}</li>
        </ul>
        
        <h3>Recommended Actions:</h3>
        <ul>
            <li>Review employee performance</li>
            <li>Decide on contract renewal or termination</li>
            <li>Prepare necessary documentation</li>
            <li>Schedule exit interview if terminating</li>
            <li>Update HR records accordingly</li>
        </ul>
        
        <p>Please ensure all necessary procedures are completed before the contract end date.</p>
        
        <p>Best regards,<br>
        PHR System - Pioneer HR Management</p>
        """
        
        frappe.sendmail(
            recipients=[recipient],
            subject=subject,
            message=message,
            reference_doctype="Employee",
            reference_name=employee.name,
            send_priority=1 if days_remaining <= 30 else 0
        )
        
    except Exception as e:
        frappe.log_error(f"Error sending contract email: {str(e)}")
        # Don't raise the exception to avoid breaking the main process

@frappe.whitelist()
def get_contract_summary():
    """
    Get summary of contracts ending soon
    """
    try:
        # Get contracts ending in next 90 days
        contracts_ending = frappe.get_all("Employee",
            filters={
                "contract_end_date": ["<=", add_days(today(), 90)],
                "contract_end_date": [">=", today()],
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date", "department", "designation"],
            order_by="contract_end_date"
        )
        
        # Categorize by time remaining
        summary = {
            "total_ending": len(contracts_ending),
            "within_30_days": 0,
            "within_60_days": 0,
            "within_90_days": 0,
            "contracts": []
        }
        
        for contract in contracts_ending:
            days_remaining = date_diff(contract.contract_end_date, today())
            contract["days_remaining"] = days_remaining
            
            if days_remaining <= 30:
                summary["within_30_days"] += 1
                contract["priority"] = "High"
            elif days_remaining <= 60:
                summary["within_60_days"] += 1
                contract["priority"] = "Medium"
            elif days_remaining <= 90:
                summary["within_90_days"] += 1
                contract["priority"] = "Low"
            
            summary["contracts"].append(contract)
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Error getting contract summary: {str(e)}")
        return {"status": "error", "message": str(e)}

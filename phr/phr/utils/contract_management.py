import frappe
from frappe.utils import getdate, add_days, today, date_diff
from frappe import _

@frappe.whitelist()
def check_contract_end_notifications():
    """
    Check for employees whose contracts are ending in 60 days and 150 days and send notifications
    This function is called daily by the scheduler
    Requirements:
    - Send notification 60 days before contract end date
    - Send reminder notification 150 days before contract end date
    """
    try:
        today_date = today()
        notifications_sent_60 = 0
        notifications_sent_150 = 0
        errors = []
        
        # Get all active employees with contract end dates
        employees = frappe.get_all("Employee",
            filters={
                "contract_end_date": ["is", "set"],
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date", "user_id", "company_email", 
                   "notification_sent_60_days", "notification_sent_150_days"]
        )
        
        for employee in employees:
            if not employee.contract_end_date:
                continue
                
            days_remaining = date_diff(employee.contract_end_date, today_date)
            
            # Check for 60 days notification
            if 58 <= days_remaining <= 62:  # Allow 2-day window
                # Check if notification already sent
                notification_sent_60 = frappe.db.get_value("Employee", employee.name, "notification_sent_60_days") or 0
                if not notification_sent_60:
                    try:
                        create_contract_notification(employee, 60, days_remaining)
                        frappe.db.set_value("Employee", employee.name, "notification_sent_60_days", 1)
                        frappe.db.set_value("Employee", employee.name, "last_notification_60_days_date", today_date)
                        notifications_sent_60 += 1
                    except Exception as e:
                        error_msg = f"Error creating 60-day notification for {employee.employee_name}: {str(e)}"
                        errors.append(error_msg)
                        frappe.log_error(error_msg)
            
            # Check for 150 days notification
            elif 148 <= days_remaining <= 152:  # Allow 2-day window
                # Check if notification already sent
                notification_sent_150 = frappe.db.get_value("Employee", employee.name, "notification_sent_150_days") or 0
                if not notification_sent_150:
                    try:
                        create_contract_notification(employee, 150, days_remaining)
                        frappe.db.set_value("Employee", employee.name, "notification_sent_150_days", 1)
                        frappe.db.set_value("Employee", employee.name, "last_notification_150_days_date", today_date)
                        notifications_sent_150 += 1
                    except Exception as e:
                        error_msg = f"Error creating 150-day notification for {employee.employee_name}: {str(e)}"
                        errors.append(error_msg)
                        frappe.log_error(error_msg)
        
        frappe.db.commit()
        
        # Log summary
        total_sent = notifications_sent_60 + notifications_sent_150
        if total_sent > 0:
            frappe.logger().info(
                f"Contract notifications sent: {notifications_sent_60} (60 days), "
                f"{notifications_sent_150} (150 days)"
            )
        
        return {
            "status": "success",
            "message": f"Contract notifications processed. 60 days: {notifications_sent_60}, 150 days: {notifications_sent_150}, Errors: {len(errors)}",
            "notifications_sent_60_days": notifications_sent_60,
            "notifications_sent_150_days": notifications_sent_150,
            "total_notifications": total_sent,
            "errors": errors
        }
        
    except Exception as e:
        error_msg = f"Error in contract notification check: {str(e)}"
        frappe.log_error(error_msg)
        return {"status": "error", "message": error_msg}

def create_contract_notification(employee, notification_type, days_remaining):
    """
    Create a notification for contract ending
    Args:
        employee: Employee dict with name, employee_name, contract_end_date, etc.
        notification_type: 60 or 150 (days before expiry)
        days_remaining: Actual days remaining until contract end
    """
    try:
        # Create a ToDo for HR team
        priority = "High" if notification_type == 60 else "Medium"
        description = (
            f"Employee {employee.employee_name} contract ends in {days_remaining} days "
            f"on {employee.contract_end_date}. "
            f"Notification sent {notification_type} days before expiry."
        )
        
        todo = frappe.get_doc({
            "doctype": "ToDo",
            "description": description,
            "reference_type": "Employee",
            "reference_name": employee.name,
            "assigned_by": frappe.session.user or "Administrator",
            "priority": priority,
            "status": "Open"
        })
        todo.insert()
        
        # Send email notification
        send_contract_email_notification(employee, notification_type, days_remaining)
        
    except Exception as e:
        frappe.log_error(f"Error creating contract notification: {str(e)}")
        raise

def send_contract_email_notification(employee, notification_type, days_remaining):
    """
    Send email notification for contract ending
    Args:
        employee: Employee dict
        notification_type: 60 or 150 (days before expiry)
        days_remaining: Actual days remaining
    """
    try:
        # Get HR team emails
        hr_emails = get_hr_team_emails()
        
        # Also include employee email if available
        recipients = list(hr_emails)
        if employee.get("company_email"):
            recipients.append(employee.company_email)
        elif employee.get("user_id"):
            try:
                user_email = frappe.db.get_value("User", employee.user_id, "email")
                if user_email:
                    recipients.append(user_email)
            except:
                pass
        
        if not recipients:
            recipients = ["hr@pioneersholding.ae"]  # Default HR email
        
        # Create subject based on notification type
        if notification_type == 60:
            subject = f"⚠️ URGENT: Contract Ending in {days_remaining} Days - {employee.employee_name}"
            urgency = "URGENT"
            action_required = "immediate action"
        else:  # 150 days
            subject = f"📅 Contract Ending in {days_remaining} Days - {employee.employee_name}"
            urgency = "REMINDER"
            action_required = "planning and preparation"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: {'#dc3545' if notification_type == 60 else '#ffc107'};">
                {urgency}: Contract End Notification
            </h2>
        
        <p>Dear HR Team,</p>
        
            <div style="background: {'#f8d7da' if notification_type == 60 else '#fff3cd'}; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px;">
                    <strong>Employee:</strong> {employee.employee_name}<br>
                    <strong>Contract End Date:</strong> {employee.contract_end_date}<br>
                    <strong>Days Remaining:</strong> <span style="color: {'#dc3545' if notification_type == 60 else '#856404'}; font-weight: bold; font-size: 18px;">{days_remaining} days</span>
                </p>
            </div>
        
        <p><strong>Action Required:</strong> Please take {action_required} regarding contract renewal or termination procedures.</p>
        
        <h3>Employee Details:</h3>
        <ul>
            <li><strong>Name:</strong> {employee.employee_name}</li>
            <li><strong>Employee ID:</strong> {employee.name}</li>
            <li><strong>Contract End Date:</strong> {employee.contract_end_date}</li>
                <li><strong>Days Remaining:</strong> {days_remaining} days</li>
                <li><strong>Notification Type:</strong> {notification_type} days before expiry</li>
        </ul>
        
        <h3>Recommended Actions:</h3>
        <ul>
                <li>Review employee performance and attendance records</li>
            <li>Decide on contract renewal or termination</li>
                <li>Prepare necessary documentation (renewal letter, termination letter, etc.)</li>
            <li>Schedule exit interview if terminating</li>
            <li>Update HR records accordingly</li>
                <li>Process final salary and end of service benefits if applicable</li>
        </ul>
        
            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0;">
                <p style="margin: 0;"><strong>⚠️ Important:</strong> Please ensure all necessary procedures are completed before the contract end date to avoid any legal or administrative issues.</p>
            </div>
        
        <p>Best regards,<br>
            <strong>PHR System - Pioneer HR Management</strong></p>
        </div>
        """
        
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            reference_doctype="Employee",
            reference_name=employee.name,
            send_priority=1 if notification_type == 60 else 0
        )
        
    except Exception as e:
        frappe.log_error(f"Error sending contract email: {str(e)}")
        # Don't raise the exception to avoid breaking the main process

def get_hr_team_emails():
    """Get HR team email addresses"""
    try:
        # Get users with HR Manager or HR User role
        hr_users = frappe.get_all("Has Role",
            filters={
                "role": ["in", ["HR Manager", "HR User", "System Manager"]],
                "parenttype": "User"
            },
            fields=["parent"],
            distinct=True
        )
        
        emails = []
        for hr_user in hr_users:
            user_email = frappe.db.get_value("User", hr_user.parent, "email")
            if user_email:
                emails.append(user_email)
        
        # If no HR users found, get all system users
        if not emails:
            all_users = frappe.get_all("User",
                filters={"enabled": 1, "user_type": "System User"},
                fields=["email"],
                limit=5
            )
            emails = [user.email for user in all_users if user.email]
        
        return emails if emails else ["hr@pioneersholding.ae"]
        
    except Exception as e:
        frappe.log_error(f"Error getting HR team emails: {str(e)}")
        return ["hr@pioneersholding.ae"]

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

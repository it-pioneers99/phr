import frappe
from frappe import _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def check_contract_expiration_notifications():
    """Check for contracts expiring in 90 and 30 days and send notifications"""
    try:
        # Get contracts expiring in 90 days
        contracts_90_days = get_contracts_expiring_in_days(90)
        for contract in contracts_90_days:
            send_contract_notification(contract, 90)
        
        # Get contracts expiring in 30 days
        contracts_30_days = get_contracts_expiring_in_days(30)
        for contract in contracts_30_days:
            send_contract_notification(contract, 30)
        
        # Get expired contracts
        expired_contracts = get_expired_contracts()
        for contract in expired_contracts:
            send_contract_notification(contract, 0)
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error checking contract expiration notifications: {str(e)}")
        return False

def get_contracts_expiring_in_days(days):
    """Get contracts expiring in specified number of days"""
    try:
        target_date = date.today() + timedelta(days=days)
        
        contracts = frappe.get_all('Employee', 
            fields=['name', 'employee_name', 'contract_end_date', 'date_of_joining'],
            filters={
                'contract_end_date': target_date,
                'status': 'Active'
            }
        )
        
        return contracts
        
    except Exception as e:
        frappe.log_error(f"Error getting contracts expiring in {days} days: {str(e)}")
        return []

def get_expired_contracts():
    """Get contracts that have expired"""
    try:
        today = date.today()
        
        contracts = frappe.get_all('Employee', 
            fields=['name', 'employee_name', 'contract_end_date', 'date_of_joining'],
            filters={
                'contract_end_date': ['<', today],
                'status': 'Active'
            }
        )
        
        return contracts
        
    except Exception as e:
        frappe.log_error(f"Error getting expired contracts: {str(e)}")
        return []

def send_contract_notification(contract, days_remaining):
    """Send contract expiration notification"""
    try:
        employee_name = contract.get('employee_name', 'Unknown')
        contract_end_date = contract.get('contract_end_date')
        
        if days_remaining == 0:
            subject = f"Contract Expired - {employee_name}"
            message = f"The contract for {employee_name} has expired on {contract_end_date}."
        elif days_remaining == 30:
            subject = f"Contract Expiring in 30 Days - {employee_name}"
            message = f"The contract for {employee_name} will expire in 30 days on {contract_end_date}."
        elif days_remaining == 90:
            subject = f"Contract Expiring in 90 Days - {employee_name}"
            message = f"The contract for {employee_name} will expire in 90 days on {contract_end_date}."
        else:
            return
        
        # Create ToDo for HR team
        create_contract_todo(contract, days_remaining, subject, message)
        
        # Send email notification (if email is configured)
        send_contract_email(contract, subject, message)
        
        # Update notification flags
        update_notification_flags(contract['name'], days_remaining)
        
    except Exception as e:
        frappe.log_error(f"Error sending contract notification: {str(e)}")

def create_contract_todo(contract, days_remaining, subject, message):
    """Create ToDo for contract management"""
    try:
        todo = frappe.get_doc({
            'doctype': 'ToDo',
            'description': message,
            'reference_type': 'Employee',
            'reference_name': contract['name'],
            'priority': 'High' if days_remaining <= 30 else 'Medium',
            'status': 'Open',
            'assigned_by': frappe.session.user
        })
        todo.insert()
        
    except Exception as e:
        frappe.log_error(f"Error creating contract todo: {str(e)}")

def send_contract_email(contract, subject, message):
    """Send email notification for contract expiration"""
    try:
        # Get HR team email addresses
        hr_emails = get_hr_team_emails()
        
        if hr_emails:
            frappe.sendmail(
                recipients=hr_emails,
                subject=subject,
                message=message,
                reference_doctype='Employee',
                reference_name=contract['name']
            )
            
    except Exception as e:
        frappe.log_error(f"Error sending contract email: {str(e)}")

def get_hr_team_emails():
    """Get HR team email addresses"""
    try:
        hr_emails = frappe.get_all('User', 
            fields=['email'],
            filters={
                'enabled': 1,
                'user_type': 'System User'
            }
        )
        
        return [user.email for user in hr_emails if user.email]
        
    except Exception as e:
        frappe.log_error(f"Error getting HR team emails: {str(e)}")
        return []

def update_notification_flags(employee, days_remaining):
    """Update notification flags for employee"""
    try:
        employee_doc = frappe.get_doc('Employee', employee)
        
        if days_remaining == 90:
            employee_doc.notification_sent_90_days = 1
            employee_doc.last_notification_date = datetime.now().date()
        elif days_remaining == 30:
            employee_doc.notification_sent_30_days = 1
            employee_doc.last_notification_date = datetime.now().date()
        elif days_remaining == 0:
            employee_doc.contract_status = 'Expired'
        
        employee_doc.save()
        
    except Exception as e:
        frappe.log_error(f"Error updating notification flags for {employee}: {str(e)}")

@frappe.whitelist()
def calculate_contract_dates(employee, joining_date):
    """Calculate contract dates based on joining date"""
    try:
        if isinstance(joining_date, str):
            joining_date = datetime.strptime(joining_date, '%Y-%m-%d').date()
        
        # Testing period ends 6 months after joining
        testing_end_date = joining_date + relativedelta(months=6)
        
        # Contract ends 180 days after joining (6 months)
        contract_end_date = joining_date + timedelta(days=180)
        
        # Calculate remaining days
        today = date.today()
        remaining_contract_days = (contract_end_date - today).days
        remaining_testing_days = max(0, (testing_end_date - today).days)
        
        return {
            'testing_end_date': testing_end_date,
            'contract_end_date': contract_end_date,
            'remaining_contract_days': remaining_contract_days,
            'remaining_testing_days': remaining_testing_days,
            'contract_duration_days': 180
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating contract dates for {employee}: {str(e)}")
        return None

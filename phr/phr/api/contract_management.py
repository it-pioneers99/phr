import frappe
from frappe import _
from phr.phr.phr.utils.contract_notifications import (
    check_contract_expiration_notifications,
    calculate_contract_dates,
    reset_notification_flags
)

@frappe.whitelist()
def get_contract_summary(employee_id):
    """Get contract summary for an employee"""
    
    employee = frappe.get_doc('Employee', employee_id)
    
    if not employee.contract_end_date:
        return {
            'status': 'error',
            'message': 'Contract end date not set for this employee'
        }
    
    from datetime import datetime, timedelta
    from frappe.utils import getdate, today
    
    contract_end = getdate(employee.contract_end_date)
    today_date = getdate(today())
    remaining_days = (contract_end - today_date).days
    
    return {
        'status': 'success',
        'employee_name': employee.employee_name,
        'contract_start_date': employee.contract_start_date,
        'contract_end_date': employee.contract_end_date,
        'testing_period_end_date': employee.testing_period_end_date,
        'contract_duration_days': employee.contract_duration_days,
        'remaining_days': remaining_days,
        'contract_status': employee.contract_status,
        'notification_sent_90_days': employee.notification_sent_90_days,
        'notification_sent_30_days': employee.notification_sent_30_days,
        'last_notification_date': employee.last_notification_date
    }

@frappe.whitelist()
def calculate_employee_contract_dates(employee_id, joining_date):
    """Calculate contract dates for an employee"""
    
    try:
        result = calculate_contract_dates(employee_id, joining_date)
        return {
            'status': 'success',
            'message': 'Contract dates calculated successfully',
            'data': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@frappe.whitelist()
def send_contract_notifications():
    """Send contract expiration notifications"""
    
    try:
        result = check_contract_expiration_notifications()
        return result
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@frappe.whitelist()
def reset_employee_notifications(employee_id):
    """Reset notification flags for an employee"""
    
    try:
        reset_notification_flags(employee_id)
        return {
            'status': 'success',
            'message': 'Notification flags reset successfully'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@frappe.whitelist()
def get_expiring_contracts(days=90):
    """Get list of contracts expiring within specified days"""
    
    from frappe.utils import getdate, today, add_days
    
    today_date = getdate(today())
    future_date = add_days(today_date, days)
    
    employees = frappe.get_all('Employee', 
        filters={
            'status': 'Active',
            'contract_end_date': ['between', [today_date, future_date]]
        },
        fields=['name', 'employee_name', 'contract_end_date', 'contract_status',
                'notification_sent_90_days', 'notification_sent_30_days']
    )
    
    for employee in employees:
        contract_end = getdate(employee.contract_end_date)
        remaining_days = (contract_end - today_date).days
        employee['remaining_days'] = remaining_days
    
    return {
        'status': 'success',
        'employees': employees,
        'total_count': len(employees)
    }

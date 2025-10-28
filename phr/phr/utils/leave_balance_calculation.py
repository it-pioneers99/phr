import frappe
from frappe import _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def calculate_employee_leave_balance(employee, date_of_joining):
    """Calculate employee leave balance based on months of service with different rates for <5 and >=5 years"""
    try:
        if isinstance(date_of_joining, str):
            date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
        
        current_date = date.today()
        
        # Calculate months of service
        months_of_service = calculate_months_of_service(date_of_joining, current_date)
        
        # Calculate years of service
        years_of_service = months_of_service / 12
        
        # Calculate annual leave balance with different rates
        annual_leave_balance = calculate_annual_leave_balance(months_of_service, years_of_service, employee)
        
        # Calculate used annual leave from leave applications
        annual_leave_used = get_used_annual_leave(employee, date_of_joining)
        
        # Calculate remaining annual leave
        annual_leave_remaining = annual_leave_balance - annual_leave_used
        
        # Calculate sick leave balance (daily accumulation)
        sick_leave_balance = calculate_sick_leave_balance(date_of_joining, current_date)
        
        # Calculate used sick leave from leave applications
        sick_leave_used = get_used_sick_leave(employee, date_of_joining)
        
        # Calculate remaining sick leave
        sick_leave_remaining = sick_leave_balance - sick_leave_used
        
        return {
            'annual_leave_balance': round(annual_leave_balance, 2),
            'annual_leave_used': round(annual_leave_used, 2),
            'annual_leave_remaining': round(annual_leave_remaining, 2),
            'sick_leave_balance': round(sick_leave_balance, 2),
            'sick_leave_used': round(sick_leave_used, 2),
            'sick_leave_remaining': round(sick_leave_remaining, 2),
            'months_of_service': months_of_service,
            'years_of_service': round(years_of_service, 2),
            'calculation_rate': get_calculation_rate(years_of_service, employee)
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating leave balance for {employee}: {str(e)}")
        return None

def get_calculation_rate(years_of_service, employee=None):
    """Get calculation rate based on years of service and additional annual leave flag"""
    try:
        # Check if employee has additional annual leave flag
        is_additional_annual_leave = False
        if employee:
            is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            return '2.5 days/month'
        elif years_of_service >= 5:
            return '2.5 days/month'
        else:
            return '1.75 days/month'
            
    except Exception as e:
        frappe.log_error(f"Error getting calculation rate: {str(e)}")
        return '1.75 days/month'

def calculate_annual_leave_balance(months_of_service, years_of_service, employee=None):
    """Calculate annual leave balance with different rates based on years of service and additional annual leave flag"""
    try:
        # Check if employee has additional annual leave flag
        is_additional_annual_leave = False
        if employee:
            is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            # If additional annual leave is checked, always give 2.5 days per month
            return months_of_service * 2.5
        elif years_of_service < 5:
            # Less than 5 years: 1.75 days per month
            return months_of_service * 1.75
        else:
            # 5 years or more: 2.5 days per month
            return months_of_service * 2.5
            
    except Exception as e:
        frappe.log_error(f"Error calculating annual leave balance: {str(e)}")
        return 0

def calculate_months_of_service(joining_date, current_date):
    """Calculate months of service from joining date to current date"""
    try:
        # Calculate the difference in months
        months = (current_date.year - joining_date.year) * 12 + (current_date.month - joining_date.month)
        
        # Adjust for partial month
        if current_date.day < joining_date.day:
            months -= 1
        
        return max(0, months)
        
    except Exception as e:
        frappe.log_error(f"Error calculating months of service: {str(e)}")
        return 0

def get_used_annual_leave(employee, joining_date):
    """Get used annual leave from leave applications since joining date"""
    try:
        # Get all approved annual leave applications since joining date
        leave_applications = frappe.get_all('Leave Application',
            fields=['total_leave_days'],
            filters={
                'employee': employee,
                'leave_type': 'Annual Leave',
                'status': 'Approved',
                'from_date': ['>=', joining_date]
            }
        )
        
        total_used = sum(app['total_leave_days'] or 0 for app in leave_applications)
        return total_used
        
    except Exception as e:
        frappe.log_error(f"Error getting used annual leave for {employee}: {str(e)}")
        return 0

def get_used_sick_leave(employee, joining_date):
    """Get used sick leave from leave applications since joining date"""
    try:
        # Get all approved sick leave applications since joining date
        leave_applications = frappe.get_all('Leave Application',
            fields=['total_leave_days'],
            filters={
                'employee': employee,
                'leave_type': 'Sick Leave',
                'status': 'Approved',
                'from_date': ['>=', joining_date]
            }
        )
        
        total_used = sum(app['total_leave_days'] or 0 for app in leave_applications)
        return total_used
        
    except Exception as e:
        frappe.log_error(f"Error getting used sick leave for {employee}: {str(e)}")
        return 0

def calculate_sick_leave_balance(joining_date, current_date):
    """Calculate sick leave balance based on daily accumulation"""
    try:
        # Calculate years of service
        years_of_service = (current_date - joining_date).days / 365.25
        
        # Daily accumulation rate based on years of service
        if years_of_service < 5:
            daily_rate = 0.0575342466  # Less than 5 years
        else:
            daily_rate = 0.0821917808  # 5 years or more
        
        # Calculate total days from joining to current date
        total_days = (current_date - joining_date).days
        
        # Calculate sick leave balance
        sick_leave_balance = total_days * daily_rate
        
        return sick_leave_balance
        
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave balance: {str(e)}")
        return 0

@frappe.whitelist()
def update_employee_leave_balance_fields(employee):
    """Update employee leave balance fields in the database"""
    try:
        # Get employee data
        employee_doc = frappe.get_doc('Employee', employee)
        
        if not employee_doc.date_of_joining:
            frappe.msgprint(f"No joining date found for employee {employee}")
            return False
        
        # Calculate leave balances
        balance_data = calculate_employee_leave_balance(employee, employee_doc.date_of_joining)
        
        if balance_data:
            # Update employee fields
            employee_doc.annual_leave_balance = balance_data['annual_leave_balance']
            employee_doc.annual_leave_used = balance_data['annual_leave_used']
            employee_doc.annual_leave_remaining = balance_data['annual_leave_remaining']
            employee_doc.sick_leave_balance = balance_data['sick_leave_balance']
            employee_doc.sick_leave_used = balance_data['sick_leave_used']
            employee_doc.sick_leave_remaining = balance_data['sick_leave_remaining']
            employee_doc.last_leave_calculation_date = datetime.now().date()
            
            employee_doc.save()
            
            return True
        
        return False
        
    except Exception as e:
        frappe.log_error(f"Error updating leave balance fields for {employee}: {str(e)}")
        return False

@frappe.whitelist()
def sync_all_employee_leave_balances():
    """Sync leave balances for all active employees"""
    try:
        # Get all active employees
        employees = frappe.get_all('Employee',
            fields=['name', 'date_of_joining'],
            filters={'status': 'Active'}
        )
        
        updated_count = 0
        error_count = 0
        
        for emp in employees:
            if emp['date_of_joining']:
                try:
                    if update_employee_leave_balance_fields(emp['name']):
                        updated_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    frappe.log_error(f"Error syncing leave balance for {emp['name']}: {str(e)}")
                    error_count += 1
        
        frappe.msgprint(f"Updated {updated_count} employees. {error_count} errors occurred.")
        return True
        
    except Exception as e:
        frappe.log_error(f"Error syncing all employee leave balances: {str(e)}")
        return False

@frappe.whitelist()
def get_leave_application_summary(employee, from_date=None, to_date=None):
    """Get summary of leave applications for an employee"""
    try:
        filters = {
            'employee': employee,
            'status': 'Approved'
        }
        
        if from_date:
            filters['from_date'] = ['>=', from_date]
        if to_date:
            filters['to_date'] = ['<=', to_date]
        
        # Get leave applications grouped by leave type
        leave_applications = frappe.get_all('Leave Application',
            fields=['leave_type', 'total_leave_days', 'from_date', 'to_date'],
            filters=filters,
            order_by='from_date desc'
        )
        
        # Group by leave type
        summary = {}
        for app in leave_applications:
            leave_type = app['leave_type']
            if leave_type not in summary:
                summary[leave_type] = {
                    'total_days': 0,
                    'applications': []
                }
            
            summary[leave_type]['total_days'] += app['total_leave_days'] or 0
            summary[leave_type]['applications'].append({
                'from_date': app['from_date'],
                'to_date': app['to_date'],
                'days': app['total_leave_days']
            })
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Error getting leave application summary for {employee}: {str(e)}")
        return {}

@frappe.whitelist()
def get_leave_balance_breakdown(employee, date_of_joining):
    """Get detailed breakdown of leave balance calculation"""
    try:
        if isinstance(date_of_joining, str):
            date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
        
        current_date = date.today()
        months_of_service = calculate_months_of_service(date_of_joining, current_date)
        years_of_service = months_of_service / 12
        
        # Calculate breakdown
        if years_of_service < 5:
            months_under_5 = months_of_service
            months_over_5 = 0
            rate_under_5 = 1.75
            rate_over_5 = 0
        else:
            months_under_5 = 60  # 5 years = 60 months
            months_over_5 = months_of_service - 60
            rate_under_5 = 1.75
            rate_over_5 = 2.5
        
        balance_under_5 = months_under_5 * rate_under_5
        balance_over_5 = months_over_5 * rate_over_5
        total_balance = balance_under_5 + balance_over_5
        
        return {
            'months_of_service': months_of_service,
            'years_of_service': round(years_of_service, 2),
            'months_under_5': months_under_5,
            'months_over_5': months_over_5,
            'rate_under_5': rate_under_5,
            'rate_over_5': rate_over_5,
            'balance_under_5': round(balance_under_5, 2),
            'balance_over_5': round(balance_over_5, 2),
            'total_balance': round(total_balance, 2)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting leave balance breakdown for {employee}: {str(e)}")
        return None

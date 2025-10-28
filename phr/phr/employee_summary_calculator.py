#!/usr/bin/env python3
"""
PHR Employee Summary Calculator
Calculates annual leave balance, sick leave tracking, salary deductions, and test period notifications
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, today, flt, cint
from datetime import datetime, timedelta
import math


class EmployeeSummaryCalculator:
    """Main class for calculating employee summaries"""
    
    def __init__(self, employee_id):
        self.employee_id = employee_id
        self.employee = frappe.get_doc("Employee", employee_id)
        self.today = getdate(today())
        
    def calculate_all_summaries(self):
        """Calculate all employee summaries"""
        try:
            # Calculate years of service
            years_of_service = self.calculate_years_of_service()
            
            # Calculate annual leave balance
            annual_leave_data = self.calculate_annual_leave_balance(years_of_service)
            
            # Calculate sick leave balance and deductions
            sick_leave_data = self.calculate_sick_leave_balance()
            
            # Calculate test period information
            test_period_data = self.calculate_test_period_info()
            
            # Update employee record
            self.update_employee_record({
                'years_of_service': years_of_service,
                **annual_leave_data,
                **sick_leave_data,
                **test_period_data
            })
            
            # Send notifications if needed
            self.send_test_period_notifications(test_period_data)
            
            return {
                'success': True,
                'years_of_service': years_of_service,
                'annual_leave': annual_leave_data,
                'sick_leave': sick_leave_data,
                'test_period': test_period_data
            }
            
        except Exception as e:
            frappe.log_error(f"Error calculating employee summary for {self.employee_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_years_of_service(self):
        """Calculate years of service from joining date"""
        if not self.employee.date_of_joining:
            return 0
            
        joining_date = getdate(self.employee.date_of_joining)
        years = (self.today - joining_date).days / 365.25
        return round(years, 2)
    
    def calculate_annual_leave_balance(self, years_of_service):
        """Calculate annual leave balance based on years of service"""
        # Annual leave allocation based on years of service
        if years_of_service < 5:
            annual_leave_allocated = 21  # 21 days for less than 5 years
        else:
            annual_leave_allocated = 30  # 30 days for 5+ years
        
        # Get used annual leave from Leave Application
        used_annual_leave = self.get_used_leave_days("Annual Leave")
        
        # Calculate remaining balance
        remaining_balance = max(0, annual_leave_allocated - used_annual_leave)
        
        return {
            'annual_leave_allocated': annual_leave_allocated,
            'annual_leave_used': used_annual_leave,
            'annual_leave_remaining': remaining_balance,
            'annual_leave_balance': annual_leave_allocated
        }
    
    def calculate_sick_leave_balance(self):
        """Calculate sick leave balance and salary deductions"""
        # Get used sick leave days
        used_sick_leave = self.get_used_leave_days("Sick Leave")
        
        # Calculate salary deductions based on sick leave usage
        deduction_data = self.calculate_sick_leave_deductions(used_sick_leave)
        
        # Calculate remaining sick leave balance (assuming 95 days per year)
        sick_leave_allocated = 95
        remaining_balance = max(0, sick_leave_allocated - used_sick_leave)
        
        return {
            'sick_leave_allocated': sick_leave_allocated,
            'sick_leave_used': used_sick_leave,
            'sick_leave_remaining': remaining_balance,
            'sick_leave_balance': sick_leave_allocated,
            'salary_deductions': deduction_data
        }
    
    def calculate_sick_leave_deductions(self, used_days):
        """Calculate salary deductions for sick leave based on usage"""
        if used_days <= 30:
            # First 30 days: No deduction
            return {
                'no_deduction_days': min(used_days, 30),
                'deduction_25_percent_days': 0,
                'deduction_100_percent_days': 0,
                'total_deduction_amount': 0
            }
        elif used_days <= 90:
            # Days 31-90: 25% deduction
            no_deduction_days = 30
            deduction_25_days = used_days - 30
            deduction_100_days = 0
        else:
            # Days 91+: 100% deduction
            no_deduction_days = 30
            deduction_25_days = 60  # Days 31-90
            deduction_100_days = used_days - 90
        
        # Calculate deduction amounts (assuming we have employee salary)
        monthly_salary = flt(self.employee.get('salary', 0))
        daily_salary = monthly_salary / 30  # Assuming 30 days per month
        
        deduction_25_amount = deduction_25_days * daily_salary * 0.25
        deduction_100_amount = deduction_100_days * daily_salary
        
        return {
            'no_deduction_days': no_deduction_days,
            'deduction_25_percent_days': deduction_25_days,
            'deduction_100_percent_days': deduction_100_days,
            'total_deduction_amount': deduction_25_amount + deduction_100_amount,
            'deduction_25_amount': deduction_25_amount,
            'deduction_100_amount': deduction_100_amount
        }
    
    def calculate_test_period_info(self):
        """Calculate test period information and remaining days"""
        if not self.employee.date_of_joining:
            return {
                'testing_period_end_date': None,
                'remaining_testing_days': 0,
                'testing_period_status': 'Not Started'
            }
        
        joining_date = getdate(self.employee.date_of_joining)
        test_period_end = add_days(joining_date, 180)  # 180 days test period
        remaining_days = (test_period_end - self.today).days
        
        if remaining_days < 0:
            status = 'Completed'
        elif remaining_days <= 30:
            status = 'Ending Soon'
        else:
            status = 'In Progress'
        
        return {
            'testing_period_end_date': test_period_end,
            'remaining_testing_days': max(0, remaining_days),
            'testing_period_status': status
        }
    
    def get_used_leave_days(self, leave_type):
        """Get used leave days for a specific leave type"""
        leave_applications = frappe.get_all("Leave Application",
            filters={
                "employee": self.employee_id,
                "leave_type": leave_type,
                "status": "Approved",
                "docstatus": 1
            },
            fields=["total_leave_days"]
        )
        
        total_used = sum(flt(la.total_leave_days) for la in leave_applications)
        return total_used
    
    def update_employee_record(self, data):
        """Update employee record with calculated data"""
        try:
            # Update basic fields
            self.employee.db_set('years_of_service', data.get('years_of_service', 0))
            
            # Update annual leave fields
            self.employee.db_set('annual_leave_allocated', data.get('annual_leave_allocated', 0))
            self.employee.db_set('annual_leave_used', data.get('annual_leave_used', 0))
            self.employee.db_set('annual_leave_remaining', data.get('annual_leave_remaining', 0))
            self.employee.db_set('annual_leave_balance', data.get('annual_leave_balance', 0))
            
            # Update sick leave fields
            self.employee.db_set('sick_leave_allocated', data.get('sick_leave_allocated', 0))
            self.employee.db_set('sick_leave_used', data.get('sick_leave_used', 0))
            self.employee.db_set('sick_leave_remaining', data.get('sick_leave_remaining', 0))
            self.employee.db_set('sick_leave_balance', data.get('sick_leave_balance', 0))
            
            # Update test period fields
            self.employee.db_set('testing_period_end_date', data.get('testing_period_end_date'))
            self.employee.db_set('remaining_testing_days', data.get('remaining_testing_days', 0))
            
            # Update last calculation date
            self.employee.db_set('last_leave_calculation_date', self.today)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error updating employee record: {str(e)}")
            raise
    
    def send_test_period_notifications(self, test_period_data):
        """Send test period notifications if needed"""
        remaining_days = test_period_data.get('remaining_testing_days', 0)
        
        if remaining_days == 120:  # 60 days before end
            self.send_notification("Test period will end in 60 days (120 days from today)")
        elif remaining_days == 30:  # 150 days before end (1 month)
            self.send_notification("Test period will end in 1 month (30 days from today)")
    
    def send_notification(self, message):
        """Send notification to HR team"""
        try:
            # Create a ToDo for HR team
            todo = frappe.new_doc("ToDo")
            todo.description = f"Employee {self.employee.employee_name} - {message}"
            todo.reference_type = "Employee"
            todo.reference_name = self.employee_id
            todo.assigned_by = "Administrator"
            todo.priority = "High"
            todo.insert()
            
            # Send email notification
            frappe.sendmail(
                recipients=["hr@pioneersholding.ae"],  # Update with actual HR email
                subject=f"Test Period Notification - {self.employee.employee_name}",
                message=message,
                reference_doctype="Employee",
                reference_name=self.employee_id
            )
            
        except Exception as e:
            frappe.log_error(f"Error sending notification: {str(e)}")


def calculate_employee_summary(employee_id):
    """Main function to calculate employee summary"""
    calculator = EmployeeSummaryCalculator(employee_id)
    return calculator.calculate_all_summaries()


def calculate_all_employees_summary():
    """Calculate summary for all active employees"""
    active_employees = frappe.get_all("Employee",
        filters={"status": "Active"},
        fields=["name"]
    )
    
    results = []
    for emp in active_employees:
        result = calculate_employee_summary(emp.name)
        results.append({
            'employee': emp.name,
            'result': result
        })
    
    return results


def get_employee_summary_dashboard(employee_id):
    """Get comprehensive employee summary for dashboard"""
    calculator = EmployeeSummaryCalculator(employee_id)
    summary = calculator.calculate_all_summaries()
    
    if not summary['success']:
        return summary
    
    # Format data for dashboard display
    dashboard_data = {
        'employee_name': calculator.employee.employee_name,
        'employee_id': employee_id,
        'years_of_service': summary['years_of_service'],
        'annual_leave': {
            'allocated': summary['annual_leave']['annual_leave_allocated'],
            'used': summary['annual_leave']['annual_leave_used'],
            'remaining': summary['annual_leave']['annual_leave_remaining'],
            'percentage_used': round((summary['annual_leave']['annual_leave_used'] / 
                                   summary['annual_leave']['annual_leave_allocated']) * 100, 2) 
                                   if summary['annual_leave']['annual_leave_allocated'] > 0 else 0
        },
        'sick_leave': {
            'allocated': summary['sick_leave']['sick_leave_allocated'],
            'used': summary['sick_leave']['sick_leave_used'],
            'remaining': summary['sick_leave']['sick_leave_remaining'],
            'deductions': summary['sick_leave']['salary_deductions']
        },
        'test_period': {
            'end_date': summary['test_period']['testing_period_end_date'],
            'remaining_days': summary['test_period']['remaining_testing_days'],
            'status': summary['test_period']['testing_period_status']
        }
    }
    
    return dashboard_data


if __name__ == "__main__":
    # Test with a specific employee
    test_employee = "EMP-001"  # Replace with actual employee ID
    result = calculate_employee_summary(test_employee)
    print(f"Employee Summary Result: {result}")

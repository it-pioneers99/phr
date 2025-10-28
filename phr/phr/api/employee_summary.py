"""
PHR Employee Summary API
Provides API endpoints for employee summary calculations and dashboard data
"""

import frappe
from frappe import _
from frappe.utils import getdate, today
from ..employee_summary_calculator import (
    calculate_employee_summary,
    calculate_all_employees_summary,
    get_employee_summary_dashboard
)


@frappe.whitelist()
def get_employee_summary(employee_id):
    """Get comprehensive employee summary"""
    try:
        if not employee_id:
            return {"error": "Employee ID is required"}
        
        if not frappe.db.exists("Employee", employee_id):
            return {"error": "Employee not found"}
        
        dashboard_data = get_employee_summary_dashboard(employee_id)
        return {"success": True, "data": dashboard_data}
        
    except Exception as e:
        frappe.log_error(f"Error getting employee summary: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def calculate_employee_leave_balance(employee_id):
    """Calculate and update employee leave balance"""
    try:
        if not employee_id:
            return {"error": "Employee ID is required"}
        
        result = calculate_employee_summary(employee_id)
        return result
        
    except Exception as e:
        frappe.log_error(f"Error calculating leave balance: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_all_employees_summary():
    """Get summary for all active employees"""
    try:
        results = calculate_all_employees_summary()
        return {"success": True, "data": results}
        
    except Exception as e:
        frappe.log_error(f"Error getting all employees summary: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_leave_balance_report():
    """Get leave balance report for all employees"""
    try:
        employees = frappe.get_all("Employee",
            filters={"status": "Active"},
            fields=["name", "employee_name", "date_of_joining", "status"]
        )
        
        report_data = []
        for emp in employees:
            summary = get_employee_summary_dashboard(emp.name)
            if summary:
                report_data.append({
                    'employee_id': emp.name,
                    'employee_name': emp.employee_name,
                    'years_of_service': summary['years_of_service'],
                    'annual_leave_remaining': summary['annual_leave']['remaining'],
                    'sick_leave_remaining': summary['sick_leave']['remaining'],
                    'test_period_remaining': summary['test_period']['remaining_days']
                })
        
        return {"success": True, "data": report_data}
        
    except Exception as e:
        frappe.log_error(f"Error getting leave balance report: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_test_period_alerts():
    """Get employees whose test period is ending soon"""
    try:
        employees = frappe.get_all("Employee",
            filters={
                "status": "Active",
                "remaining_testing_days": ["<=", 30]
            },
            fields=["name", "employee_name", "testing_period_end_date", "remaining_testing_days"]
        )
        
        alerts = []
        for emp in employees:
            alerts.append({
                'employee_id': emp.name,
                'employee_name': emp.employee_name,
                'test_period_end_date': emp.testing_period_end_date,
                'remaining_days': emp.remaining_testing_days,
                'alert_level': 'High' if emp.remaining_testing_days <= 7 else 'Medium'
            })
        
        return {"success": True, "data": alerts}
        
    except Exception as e:
        frappe.log_error(f"Error getting test period alerts: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def bulk_calculate_leave_balances():
    """Bulk calculate leave balances for all employees"""
    try:
        results = calculate_all_employees_summary()
        
        success_count = sum(1 for r in results if r['result']['success'])
        error_count = len(results) - success_count
        
        return {
            "success": True,
            "message": f"Processed {len(results)} employees. Success: {success_count}, Errors: {error_count}",
            "results": results
        }
        
    except Exception as e:
        frappe.log_error(f"Error in bulk calculation: {str(e)}")
        return {"error": str(e)}

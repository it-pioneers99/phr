import frappe
from frappe import _
from datetime import datetime, timedelta
from phr.phr.utils.contract_notifications import get_contract_summary

from phr.phr.utils.dynamic_leave_allocation import calculate_years_of_service

def get_leave_dashboard_data():
    """Get comprehensive leave dashboard data"""
    return {
        "contract_summary": get_contract_summary(),
        "leave_balance_summary": get_leave_balance_summary(),
        "employee_tenure_summary": get_employee_tenure_summary(),
        "sick_leave_summary": get_sick_leave_summary(),
        "testing_period_summary": get_testing_period_summary()
    }

def get_leave_balance_summary():
    """Get leave balance summary for all employees"""
    # Get employees with leave balances
    employees = frappe.get_all("Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "annual_leave_balance", "sick_leave_balance", "sick_leave_remaining"]
    )
    
    total_annual_balance = sum(emp.annual_leave_balance or 0 for emp in employees)
    total_sick_balance = sum(emp.sick_leave_balance or 0 for emp in employees)
    total_sick_remaining = sum(emp.sick_leave_remaining or 0 for emp in employees)
    
    return {
        "total_employees": len(employees),
        "total_annual_balance": total_annual_balance,
        "total_sick_balance": total_sick_balance,
        "total_sick_remaining": total_sick_remaining,
        "average_annual_balance": total_annual_balance / len(employees) if employees else 0,
        "average_sick_balance": total_sick_balance / len(employees) if employees else 0
    }

def get_employee_tenure_summary():
    """Get employee tenure summary"""
    employees = frappe.get_all("Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "years_of_service", "date_of_joining"]
    )
    
    under_5_years = 0
    over_5_years = 0
    new_employees = 0
    
    for emp in employees:
        years = emp.years_of_service or 0
        if years < 1:
            new_employees += 1
        elif years < 5:
            under_5_years += 1
        else:
            over_5_years += 1
    
    return {
        "total_employees": len(employees),
        "new_employees": new_employees,
        "under_5_years": under_5_years,
        "over_5_years": over_5_years,
        "average_tenure": sum(emp.years_of_service or 0 for emp in employees) / len(employees) if employees else 0
    }

def get_sick_leave_summary():
    """Get sick leave summary"""
    # Get sick leave applications for current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    month_start = datetime(current_year, current_month, 1).date()
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    sick_leaves = frappe.get_all("Leave Application",
        filters={
            "leave_type": "Sick Leave",
            "from_date": ["between", [month_start, month_end]],
            "status": "Approved",
            "docstatus": 1
        },
        fields=["employee", "total_leave_days"]
    )
    
    total_sick_days = sum(leave.total_leave_days for leave in sick_leaves)
    unique_employees = len(set(leave.employee for leave in sick_leaves))
    
    return {
        "total_sick_applications": len(sick_leaves),
        "total_sick_days": total_sick_days,
        "unique_employees": unique_employees,
        "average_sick_days_per_employee": total_sick_days / unique_employees if unique_employees > 0 else 0
    }

def get_testing_period_summary():
    """Get testing period summary"""
    current_date = datetime.now().date()
    
    # Employees in testing period
    testing_employees = frappe.get_all("Employee",
        filters={
            "status": "Active",
            "testing_period_end_date": [">=", current_date],
            "testing_period_remaining_days": [">", 0]
        },
        fields=["name", "employee_name", "testing_period_remaining_days"]
    )
    
    # Employees whose testing period is ending soon (within 30 days)
    ending_soon = [emp for emp in testing_employees if emp.testing_period_remaining_days <= 30]
    
    return {
        "total_in_testing": len(testing_employees),
        "ending_soon": len(ending_soon),
        "employees": testing_employees
    }

def get_leave_type_distribution():
    """Get leave type distribution"""
    leave_types = frappe.get_all("Leave Type",
        filters={"is_active": 1},
        fields=["name", "is_annual_leave", "is_sick_leave", "is_muslim", "is_female"]
    )
    
    distribution = {
        "annual_leaves": [lt for lt in leave_types if lt.is_annual_leave],
        "sick_leaves": [lt for lt in leave_types if lt.is_sick_leave],
        "muslim_leaves": [lt for lt in leave_types if lt.is_muslim],
        "female_leaves": [lt for lt in leave_types if lt.is_female]
    }
    
    return distribution

def get_employee_leave_history(employee):
    """Get leave history for a specific employee"""
    leave_applications = frappe.get_all("Leave Application",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fields=["leave_type", "from_date", "to_date", "total_leave_days", "status"],
        order_by="from_date desc",
        limit=10
    )
    
    return leave_applications

def get_leave_analytics():
    """Get comprehensive leave analytics"""
    current_year = datetime.now().year
    
    # Monthly leave trends
    monthly_trends = []
    for month in range(1, 13):
        month_start = datetime(current_year, month, 1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        leave_count = frappe.db.count("Leave Application", {
            "from_date": ["between", [month_start, month_end]],
            "docstatus": 1,
            "status": "Approved"
        })
        
        monthly_trends.append({
            "month": month,
            "leave_count": leave_count
        })
    
    # Leave type usage
    leave_type_usage = frappe.db.sql("""
        SELECT 
            la.leave_type,
            COUNT(*) as application_count,
            SUM(la.total_leave_days) as total_days
        FROM `tabLeave Application` la
        WHERE la.docstatus = 1
        AND la.status = 'Approved'
        AND YEAR(la.from_date) = %s
        GROUP BY la.leave_type
        ORDER BY total_days DESC
    """, (current_year,), as_dict=True)
    
    return {
        "monthly_trends": monthly_trends,
        "leave_type_usage": leave_type_usage
    }

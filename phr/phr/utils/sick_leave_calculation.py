import frappe
from frappe import _
from datetime import datetime, timedelta

def calculate_sick_leave_deduction(employee, month, year):
    """Calculate sick leave deduction for an employee for a specific month"""
    # Get sick leave applications for the month
    month_start = datetime(year, month, 1).date()
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    sick_leaves = frappe.get_all("Leave Application",
        filters={
            "employee": employee,
            "leave_type": "Sick Leave",
            "from_date": ["between", [month_start, month_end]],
            "status": "Approved",
            "docstatus": 1
        },
        fields=["total_leave_days", "from_date", "to_date"]
    )
    
    total_sick_days = sum(leave.total_leave_days for leave in sick_leaves)
    
    if total_sick_days == 0:
        return 0
    
    # Calculate deduction based on sick leave rules
    deduction_amount = calculate_sick_leave_deduction_amount(employee, total_sick_days)
    
    return deduction_amount

def calculate_sick_leave_deduction_amount(employee, total_sick_days):
    """Calculate sick leave deduction amount based on days"""
    # Get employee's daily salary
    daily_salary = get_employee_daily_salary(employee)
    
    if total_sick_days <= 30:
        # First 30 days: No deduction (100% salary)
        return 0
    elif total_sick_days <= 90:
        # Days 31-90: 25% deduction (75% salary)
        excess_days = total_sick_days - 30
        deduction = daily_salary * excess_days * 0.25
        return deduction
    else:
        # Days 90+: 100% deduction (unpaid)
        excess_days = total_sick_days - 90
        deduction = daily_salary * excess_days  # 100% deduction for days over 90
        return deduction

def get_employee_daily_salary(employee):
    """Get employee's daily salary"""
    # Get employee's basic salary
    basic_salary = frappe.db.get_value("Employee", employee, "basic_salary")
    
    if not basic_salary:
        # Try to get from salary structure
        salary_structure = frappe.get_all("Salary Structure Assignment",
            filters={"employee": employee, "docstatus": 1},
            fields=["salary_structure"],
            order_by="from_date desc",
            limit=1
        )
        
        if salary_structure:
            basic_salary = frappe.db.get_value("Salary Structure",
                salary_structure[0].salary_structure,
                "basic_salary"
            )
    
    if not basic_salary:
        # Default to 0 if no salary found
        return 0
    
    # Calculate daily salary (assuming 30 days per month)
    daily_salary = basic_salary / 30
    return daily_salary

def create_sick_leave_salary_components():
    """Create salary components for sick leave"""
    components = [
        {
            "name": "Sick Leave Deduction 25%",
            "type": "Deduction",
            "description": "Sick leave deduction for days 31-90 (25% of daily salary)"
        },
        {
            "name": "Sick Leave Deduction 100%",
            "type": "Deduction", 
            "description": "Sick leave deduction for days over 90 (100% of daily salary)"
        }
    ]
    
    for component in components:
        if not frappe.db.exists("Salary Component", component["name"]):
            salary_component = frappe.new_doc("Salary Component")
            salary_component.salary_component = component["name"]
            salary_component.type = component["type"]
            salary_component.description = component["description"]
            salary_component.insert()
            
            frappe.msgprint(_("Created salary component: {0}").format(component["name"]))

def get_sick_leave_balance_summary(employee, leave_period=None):
    """Get sick leave balance summary for an employee"""
    if not leave_period:
        current_year = datetime.now().year
        leave_period = {
            "from_date": datetime(current_year, 1, 1).date(),
            "to_date": datetime(current_year, 12, 31).date()
        }
    
    # Get allocated sick leave
    allocated = frappe.db.sql("""
        SELECT SUM(new_leaves_allocated)
        FROM `tabLeave Allocation`
        WHERE employee = %s
        AND leave_type = 'Sick Leave'
        AND from_date >= %s
        AND to_date <= %s
        AND docstatus = 1
    """, (employee, leave_period["from_date"], leave_period["to_date"]), as_list=True)
    
    allocated_days = allocated[0][0] or 0
    
    # Get used sick leave
    used = frappe.db.sql("""
        SELECT SUM(total_leave_days)
        FROM `tabLeave Application`
        WHERE employee = %s
        AND leave_type = 'Sick Leave'
        AND from_date >= %s
        AND to_date <= %s
        AND docstatus = 1
        AND status = 'Approved'
    """, (employee, leave_period["from_date"], leave_period["to_date"]), as_list=True)
    
    used_days = used[0][0] or 0
    remaining_days = allocated_days - used_days
    
    return {
        "allocated": allocated_days,
        "used": used_days,
        "remaining": remaining_days
    }

def validate_sick_leave_application(employee, from_date, to_date, total_days):
    """Validate sick leave application"""
    # Check if employee has sufficient sick leave balance
    balance_summary = get_sick_leave_balance_summary(employee)
    
    if total_days > balance_summary["remaining"]:
        frappe.throw(_("Insufficient sick leave balance. Available: {0} days, Requested: {1} days").format(
            balance_summary["remaining"], total_days
        ))
    
    # Check for consecutive sick leave applications
    check_consecutive_sick_leave(employee, from_date, to_date)

def check_consecutive_sick_leave(employee, from_date, to_date):
    """Check for consecutive sick leave applications"""
    # Get previous sick leave applications
    previous_leaves = frappe.get_all("Leave Application",
        filters={
            "employee": employee,
            "leave_type": "Sick Leave",
            "status": "Approved",
            "docstatus": 1
        },
        fields=["from_date", "to_date"],
        order_by="to_date desc",
        limit=1
    )
    
    if previous_leaves:
        last_leave = previous_leaves[0]
        gap_days = (from_date - last_leave.to_date).days
        
        if gap_days <= 1:
            frappe.msgprint(_("Warning: This sick leave application is consecutive with the previous one. Please ensure medical documentation is provided."))

def update_sick_leave_balances_daily():
    """Update sick leave balances for all employees daily"""
    active_employees = frappe.get_all("Employee",
        filters={"status": "Active"},
        fields=["name"]
    )
    
    for employee in active_employees:
        balance_summary = get_sick_leave_balance_summary(employee.name)
        
        # Update employee fields
        frappe.db.set_value("Employee", employee.name, "sick_leave_balance", balance_summary["allocated"])
        frappe.db.set_value("Employee", employee.name, "sick_leave_used", balance_summary["used"])
        frappe.db.set_value("Employee", employee.name, "sick_leave_remaining", balance_summary["remaining"])
    
    frappe.msgprint(_("Updated sick leave balances for {0} employees").format(len(active_employees)))

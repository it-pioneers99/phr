import frappe
from frappe import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def calculate_years_of_service(employee):
    """Calculate years of service for an employee"""
    if not employee:
        return 0
    
    employee_doc = frappe.get_doc("Employee", employee)
    if not employee_doc.date_of_joining:
        return 0
    
    joining_date = employee_doc.date_of_joining
    current_date = datetime.now().date()
    
    # Calculate years with decimal precision
    years = (current_date - joining_date).days / 365.25
    return round(years, 2)

def update_employee_years_of_service(employee):
    """Update years of service for an employee"""
    years = calculate_years_of_service(employee)
    
    frappe.db.set_value("Employee", employee, "years_of_service", years)
    
    # Update testing period remaining days
    update_testing_period_days(employee)
    
    return years

def update_testing_period_days(employee):
    """Update testing period remaining days"""
    employee_doc = frappe.get_doc("Employee", employee)
    
    if not employee_doc.testing_period_end_date:
        return
    
    end_date = employee_doc.testing_period_end_date
    current_date = datetime.now().date()
    
    if current_date <= end_date:
        remaining_days = (end_date - current_date).days
        frappe.db.set_value("Employee", employee, "testing_period_remaining_days", remaining_days)
    else:
        frappe.db.set_value("Employee", employee, "testing_period_remaining_days", 0)

def get_eligible_leave_types(employee):
    """Get leave types eligible for an employee based on demographics"""
    employee_doc = frappe.get_doc("Employee", employee)
    
    # Base query
    filters = {"is_active": 1}
    
    # Add demographic filters
    if employee_doc.is_muslim and employee_doc.is_female:
        # Muslim female - can access all leave types
        pass
    elif employee_doc.is_female and not employee_doc.is_muslim:
        # Non-Muslim female - exclude Muslim-only leaves
        filters["is_muslim"] = 0
    elif employee_doc.is_muslim and not employee_doc.is_female:
        # Muslim male - exclude female-only leaves
        filters["is_female"] = 0
    else:
        # Non-Muslim male - exclude both Muslim and female-only leaves
        filters["is_muslim"] = 0
        filters["is_female"] = 0
    
    leave_types = frappe.get_all("Leave Type", filters=filters, fields=["name", "is_annual_leave", "is_sick_leave"])
    return leave_types

def calculate_leave_allocation_days(employee, leave_type):
    """Calculate allocation days for a leave type based on employee years of service"""
    years = calculate_years_of_service(employee)
    leave_type_doc = frappe.get_doc("Leave Type", leave_type)
    
    # Check if this is Online Present leave type - use max_leaves_allowed
    if hasattr(leave_type_doc, 'is_online_present') and leave_type_doc.is_online_present:
        return leave_type_doc.get("max_leaves_allowed", 12)
    
    # Get is_additional_annual_leave value from database
    is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
    
    # For other leave types, use the standard logic with additional annual leave consideration
    if is_additional_annual_leave:
        # If additional annual leave is checked, always give 30 days for annual leave
        if leave_type_doc.is_annual_leave:
            days = 30
        else:
            days = leave_type_doc.allocation_days_over_5_years or 30
    elif years < 5:
        days = leave_type_doc.allocation_days_under_5_years or 21
    else:
        days = leave_type_doc.allocation_days_over_5_years or 30
    
    # Ensure we don't exceed max_leaves_allowed if it's set
    max_allowed = leave_type_doc.get("max_leaves_allowed")
    if max_allowed and days > max_allowed:
        days = max_allowed
    
    return days

def create_dynamic_leave_allocation(employee, leave_period=None):
    """Create dynamic leave allocation for an employee"""
    if not leave_period:
        leave_period = get_current_leave_period()
    
    # Get eligible leave types
    eligible_leave_types = get_eligible_leave_types(employee)
    
    for leave_type_info in eligible_leave_types:
        leave_type = leave_type_info.name
        
        # Check if allocation already exists for this period
        existing_allocation = frappe.db.exists("Leave Allocation", {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": leave_period["from_date"],
            "to_date": leave_period["to_date"],
            "docstatus": 1
        })
        
        if existing_allocation:
            continue
        
        # Calculate allocation days
        allocation_days = calculate_leave_allocation_days(employee, leave_type)
        
        # Pro-rate allocation based on joining date
        pro_rated_days = calculate_pro_rated_allocation(employee, allocation_days, leave_period)
        
        if pro_rated_days > 0:
            # Create leave allocation
            allocation_doc = frappe.new_doc("Leave Allocation")
            allocation_doc.employee = employee
            allocation_doc.leave_type = leave_type
            allocation_doc.from_date = leave_period["from_date"]
            allocation_doc.to_date = leave_period["to_date"]
            allocation_doc.new_leaves_allocated = pro_rated_days
            allocation_doc.docstatus = 1
            allocation_doc.save()
            
            frappe.msgprint(_("Created leave allocation for {0}: {1} days").format(leave_type, pro_rated_days))

def calculate_pro_rated_allocation(employee, total_days, leave_period):
    """Calculate pro-rated allocation based on joining date"""
    employee_doc = frappe.get_doc("Employee", employee)
    joining_date = employee_doc.date_of_joining
    
    period_start = leave_period["from_date"]
    period_end = leave_period["to_date"]
    
    # If employee joined before the period, give full allocation
    if joining_date <= period_start:
        return total_days
    
    # If employee joined after the period, no allocation
    if joining_date > period_end:
        return 0
    
    # Calculate pro-rated allocation
    days_in_period = (period_end - period_start).days + 1
    days_worked = (period_end - joining_date).days + 1
    
    pro_rated_days = (total_days * days_worked) / days_in_period
    return round(pro_rated_days, 1)

def get_current_leave_period():
    """Get current leave period"""
    current_year = datetime.now().year
    return {
        "from_date": datetime(current_year, 1, 1).date(),
        "to_date": datetime(current_year, 12, 31).date()
    }

def update_leave_balances(employee):
    """Update leave balances for an employee"""
    # Get current leave period
    leave_period = get_current_leave_period()
    
    # Calculate annual leave balance
    annual_balance = calculate_leave_balance(employee, "Annual Leave", leave_period)
    frappe.db.set_value("Employee", employee, "annual_leave_balance", annual_balance)
    
    # Calculate sick leave balance
    sick_balance = calculate_leave_balance(employee, "Sick Leave", leave_period)
    sick_used = calculate_leave_used(employee, "Sick Leave", leave_period)
    sick_remaining = sick_balance - sick_used
    
    frappe.db.set_value("Employee", employee, "sick_leave_balance", sick_balance)
    frappe.db.set_value("Employee", employee, "sick_leave_used", sick_used)
    frappe.db.set_value("Employee", employee, "sick_leave_remaining", sick_remaining)

def calculate_leave_balance(employee, leave_type, leave_period):
    """Calculate leave balance for an employee"""
    # Get allocated leaves
    allocated = frappe.db.sql("""
        SELECT SUM(new_leaves_allocated)
        FROM `tabLeave Allocation`
        WHERE employee = %s
        AND leave_type = %s
        AND from_date >= %s
        AND to_date <= %s
        AND docstatus = 1
    """, (employee, leave_type, leave_period["from_date"], leave_period["to_date"]), as_list=True)
    
    allocated_days = allocated[0][0] or 0
    
    # Get used leaves
    used = frappe.db.sql("""
        SELECT SUM(total_leave_days)
        FROM `tabLeave Application`
        WHERE employee = %s
        AND leave_type = %s
        AND from_date >= %s
        AND to_date <= %s
        AND docstatus = 1
        AND status = 'Approved'
    """, (employee, leave_type, leave_period["from_date"], leave_period["to_date"]), as_list=True)
    
    used_days = used[0][0] or 0
    
    return allocated_days - used_days

def calculate_leave_used(employee, leave_type, leave_period):
    """Calculate leave used for an employee"""
    used = frappe.db.sql("""
        SELECT SUM(total_leave_days)
        FROM `tabLeave Application`
        WHERE employee = %s
        AND leave_type = %s
        AND from_date >= %s
        AND to_date <= %s
        AND docstatus = 1
        AND status = 'Approved'
    """, (employee, leave_type, leave_period["from_date"], leave_period["to_date"]), as_list=True)
    
    return used[0][0] or 0

def check_contract_end_notifications():
    """Check for employees whose contracts are ending soon"""
    # Get employees with contracts ending in 90 days
    ninety_days_from_now = datetime.now().date() + timedelta(days=90)
    
    employees = frappe.get_all("Employee", 
        filters={
            "contract_end_date": ["<=", ninety_days_from_now],
            "contract_end_date": [">=", datetime.now().date()],
            "status": "Active"
        },
        fields=["name", "employee_name", "contract_end_date"]
    )
    
    for employee in employees:
        days_remaining = (employee.contract_end_date - datetime.now().date()).days
        frappe.msgprint(_("Contract ending for {0} in {1} days").format(
            employee.employee_name, days_remaining
        ))

def sync_all_employee_balances():
    """Sync leave balances for all active employees"""
    active_employees = frappe.get_all("Employee", 
        filters={"status": "Active"},
        fields=["name"]
    )
    
    for employee in active_employees:
        update_leave_balances(employee.name)
    
    frappe.msgprint(_("Synced leave balances for {0} employees").format(len(active_employees)))

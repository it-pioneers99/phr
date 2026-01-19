"""
Salary Component Integration Utilities
Handles integration of Overtime, Shift Permissions, and other components with Salary Slip
"""
import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day, flt
from datetime import datetime, timedelta

def get_overtime_allowance_for_salary_slip(employee, start_date, end_date):
    """
    Get total overtime allowance for an employee in a given period
    Returns amount to be added as earning component
    """
    try:
        # Get all approved overtime requests in the period
        overtime_requests = frappe.get_all(
            "Overtime Request",
            filters={
                "employee": employee,
                "overtime_date": ["between", [start_date, end_date]],
                "status": "Approved",
                "docstatus": 1
            },
            fields=["name", "hours_requested", "overtime_date"]
        )
        
        if not overtime_requests:
            return 0
        
        # Get employee's salary to calculate hourly rate
        employee_doc = frappe.get_doc("Employee", employee)
        monthly_salary = get_employee_monthly_salary(employee_doc)
        
        if not monthly_salary:
            return 0
        
        # Calculate hourly rate (assuming 8 hours per day, 30 days per month)
        hourly_rate = monthly_salary / 30 / 8
        
        # Calculate total overtime allowance (50% premium)
        total_allowance = 0
        for ot in overtime_requests:
            # Overtime rate = hourly rate × 1.5 (50% premium)
            overtime_rate = hourly_rate * 1.5
            total_allowance += flt(ot.hours_requested) * overtime_rate
        
        return total_allowance
        
    except Exception as e:
        frappe.log_error(f"Error calculating overtime allowance for {employee}: {str(e)}")
        return 0

def get_shift_permission_deduction_for_salary_slip(employee, start_date, end_date):
    """
    Get total shift permission deduction for an employee in a given period
    Returns amount to be deducted from salary if leave balance is insufficient
    """
    try:
        # Get all approved shift permission requests in the period
        permission_requests = frappe.get_all(
            "Shift Permission Request",
            filters={
                "employee": employee,
                "permission_date": ["between", [start_date, end_date]],
                "status": "Approved",
                "docstatus": 1,
                "deduct_from_salary": 1  # Only if marked for salary deduction
            },
            fields=["name", "hours_requested", "permission_date"]
        )
        
        if not permission_requests:
            return 0
        
        # Get employee's salary to calculate daily/hourly rate
        employee_doc = frappe.get_doc("Employee", employee)
        monthly_salary = get_employee_monthly_salary(employee_doc)
        
        if not monthly_salary:
            return 0
        
        # Calculate daily rate
        daily_rate = monthly_salary / 30
        
        # Calculate total deduction
        total_deduction = 0
        for perm in permission_requests:
            hours = flt(perm.hours_requested)
            
            # Convert hours to days for deduction
            # 4 hours = 0.5 day (half day)
            # 8 hours = 1 day (full day)
            if hours >= 4:
                # Half day or more
                days = hours / 8
                total_deduction += daily_rate * days
            elif hours >= 2:
                # Quarter day
                total_deduction += daily_rate * 0.25
            else:
                # Less than 2 hours, calculate proportionally
                total_deduction += (daily_rate / 8) * hours
        
        return total_deduction
        
    except Exception as e:
        frappe.log_error(f"Error calculating shift permission deduction for {employee}: {str(e)}")
        return 0

def process_shift_permission_leave_deduction(permission_request):
    """
    Process leave deduction for approved shift permission request
    If leave balance is insufficient, mark for salary deduction
    """
    try:
        if not permission_request.hours_requested or permission_request.hours_requested < 4:
            # Less than 4 hours (half day) - no deduction needed
            return
        
        # Get employee's annual leave balance
        employee = permission_request.employee
        current_year = getdate().year
        
        # Get annual leave allocation
        annual_leave_type = frappe.db.get_value("Leave Type", {"is_annual_leave": 1}, "name")
        if not annual_leave_type:
            # No annual leave type found, mark for salary deduction
            frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_salary", 1)
            return
        
        # Get leave allocation for current year
        allocation = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": annual_leave_type,
                "from_date": [">=", f"{current_year}-01-01"],
                "to_date": ["<=", f"{current_year}-12-31"],
                "docstatus": 1
            },
            fields=["name", "unused_leaves"],
            limit=1
        )
        
        if not allocation:
            # No allocation found, mark for salary deduction
            frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_salary", 1)
            return
        
        # Calculate days to deduct (4 hours = 0.5 day)
        days_to_deduct = permission_request.hours_requested / 8
        
        unused_leaves = flt(allocation[0].unused_leaves or 0)
        
        if unused_leaves >= days_to_deduct:
            # Sufficient leave balance - deduct from leave
            allocation_doc = frappe.get_doc("Leave Allocation", allocation[0].name)
            allocation_doc.unused_leaves = unused_leaves - days_to_deduct
            allocation_doc.save()
            frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_leave", 1)
            frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_salary", 0)
            frappe.db.commit()
        else:
            # Insufficient leave balance - mark for salary deduction
            frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_salary", 1)
            frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_leave", 0)
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error(f"Error processing shift permission leave deduction: {str(e)}")
        # On error, mark for salary deduction as fallback
        frappe.db.set_value("Shift Permission Request", permission_request.name, "deduct_from_salary", 1)

def get_employee_monthly_salary(employee_doc):
    """
    Get employee's monthly salary from various sources
    Checks: salary field, salary structure, or custom field
    """
    try:
        # Try direct salary field
        if hasattr(employee_doc, 'salary') and employee_doc.salary:
            return flt(employee_doc.salary)
        
        # Try to get from salary structure assignment
        salary_structure_assignment = frappe.get_all(
            "Salary Structure Assignment",
            filters={
                "employee": employee_doc.name,
                "docstatus": 1
            },
            fields=["base"],
            order_by="from_date desc",
            limit=1
        )
        
        if salary_structure_assignment:
            return flt(salary_structure_assignment[0].base)
        
        # Try custom field
        custom_salary = frappe.db.get_value("Employee", employee_doc.name, "custom_monthly_salary")
        if custom_salary:
            return flt(custom_salary)
        
        return 0
        
    except Exception as e:
        frappe.log_error(f"Error getting employee salary for {employee_doc.name}: {str(e)}")
        return 0

@frappe.whitelist()
def add_overtime_allowance_to_salary_slip(salary_slip_name):
    """
    Add overtime allowance as earning component to salary slip
    Called from Salary Slip before_save or validate
    """
    try:
        salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)
        employee = salary_slip.employee
        start_date = salary_slip.start_date
        end_date = salary_slip.end_date
        
        # Get overtime allowance amount
        overtime_amount = get_overtime_allowance_for_salary_slip(employee, start_date, end_date)
        
        if overtime_amount <= 0:
            return
        
        # Check if "Overtime Allowance" component already exists
        existing_component = None
        if hasattr(salary_slip, "earnings"):
            for earning in salary_slip.earnings:
                if earning.salary_component == "Overtime Allowance":
                    existing_component = earning
                    break
        
        if existing_component:
            # Update existing component
            existing_component.amount = overtime_amount
        else:
            # Add new earning component
            # First, ensure "Overtime Allowance" salary component exists
            if not frappe.db.exists("Salary Component", "Overtime Allowance"):
                create_overtime_allowance_component()
            
            salary_slip.append("earnings", {
                "salary_component": "Overtime Allowance",
                "amount": overtime_amount
            })
        
        salary_slip.save()
        
    except Exception as e:
        frappe.log_error(f"Error adding overtime allowance to salary slip {salary_slip_name}: {str(e)}")

@frappe.whitelist()
def add_shift_permission_deduction_to_salary_slip(salary_slip_name):
    """
    Add shift permission deduction as deduction component to salary slip
    Called from Salary Slip before_save or validate
    """
    try:
        salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)
        employee = salary_slip.employee
        start_date = salary_slip.start_date
        end_date = salary_slip.end_date
        
        # Get shift permission deduction amount
        deduction_amount = get_shift_permission_deduction_for_salary_slip(employee, start_date, end_date)
        
        if deduction_amount <= 0:
            return
        
        # Check if "Shift Permission Deduction" component already exists
        existing_component = None
        if hasattr(salary_slip, "deductions"):
            for deduction in salary_slip.deductions:
                if deduction.salary_component == "Shift Permission Deduction":
                    existing_component = deduction
                    break
        
        if existing_component:
            # Update existing component
            existing_component.amount = deduction_amount
        else:
            # Add new deduction component
            # First, ensure "Shift Permission Deduction" salary component exists
            if not frappe.db.exists("Salary Component", "Shift Permission Deduction"):
                create_shift_permission_deduction_component()
            
            salary_slip.append("deductions", {
                "salary_component": "Shift Permission Deduction",
                "amount": deduction_amount
            })
        
        salary_slip.save()
        
    except Exception as e:
        frappe.log_error(f"Error adding shift permission deduction to salary slip {salary_slip_name}: {str(e)}")

def create_overtime_allowance_component():
    """Create Overtime Allowance salary component if it doesn't exist"""
    try:
        if frappe.db.exists("Salary Component", "Overtime Allowance"):
            return
        
        component = frappe.new_doc("Salary Component")
        component.salary_component = "Overtime Allowance"
        component.type = "Earning"
        component.description = "Overtime allowance calculated at 50% premium on hourly rate"
        component.insert()
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating Overtime Allowance component: {str(e)}")

def create_shift_permission_deduction_component():
    """Create Shift Permission Deduction salary component if it doesn't exist"""
    try:
        if frappe.db.exists("Salary Component", "Shift Permission Deduction"):
            return
        
        component = frappe.new_doc("Salary Component")
        component.salary_component = "Shift Permission Deduction"
        component.type = "Deduction"
        component.description = "Deduction for shift permissions when leave balance is insufficient"
        component.insert()
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating Shift Permission Deduction component: {str(e)}")


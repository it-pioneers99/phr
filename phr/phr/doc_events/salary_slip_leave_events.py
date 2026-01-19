import frappe
from frappe.utils import getdate, date_diff
from frappe import _
from phr.phr.utils.leave_management import calculate_sick_leave_deduction
from phr.phr.utils.salary_component_integration import (
    get_overtime_allowance_for_salary_slip,
    get_shift_permission_deduction_for_salary_slip
)

@frappe.whitelist()
def before_submit(doc, method=None):
    """Handle salary slip before submit for various deductions and earnings"""
    try:
        employee = doc.employee
        start_date = getdate(doc.start_date)
        end_date = getdate(doc.end_date)
        
        # 1. Process sick leave deduction
        process_sick_leave_deduction(doc, employee, start_date, end_date)
        
        # 2. Process overtime allowance (earning)
        process_overtime_allowance(doc, employee, start_date, end_date)
        
        # 3. Process shift permission deduction
        process_shift_permission_deduction(doc, employee, start_date, end_date)
        
    except Exception as e:
        frappe.log_error(f"Error in salary slip before_submit for {doc.name}: {str(e)}", "PHR Salary Slip Events")

def process_sick_leave_deduction(doc, employee, start_date, end_date):
    """Process sick leave deduction"""
    try:
        # Get sick leave type
        sick_leave_type = frappe.db.get_value("Leave Type", {"is_sick_leave": 1})
        
        if not sick_leave_type:
            return
        
        # Get sick leaves taken during this period
        sick_leaves_taken = frappe.db.sql(
            """
            SELECT SUM(total_leave_days)
            FROM `tabLeave Application`
            WHERE employee = %s
            AND leave_type = %s
            AND status = 'Approved'
            AND docstatus = 1
            AND (
                (from_date BETWEEN %s AND %s) OR
                (to_date BETWEEN %s AND %s) OR
                (from_date <= %s AND to_date >= %s)
            )
            """,
            (employee, sick_leave_type, start_date, end_date, start_date, end_date, start_date, end_date),
            as_list=True
        )[0][0] or 0
        
        if sick_leaves_taken > 0:
            # Get employee basic salary
            employee_doc = frappe.get_doc("Employee", employee)
            basic_salary = employee_doc.base or 0
            
            if not basic_salary:
                return
            
            # Calculate sick leave deduction
            sick_leave_deduction_amount = calculate_sick_leave_deduction(
                employee, 
                sick_leaves_taken, 
                basic_salary
            )
            
            if sick_leave_deduction_amount > 0:
                # Add or update "Sick Leave Deduction" salary component
                add_salary_component(doc, "Sick Leave Deduction", sick_leave_deduction_amount, "Deduction")
        
    except Exception as e:
        frappe.log_error(f"Error processing sick leave deduction: {str(e)}", "PHR Salary Slip Events")

def process_overtime_allowance(doc, employee, start_date, end_date):
    """Process overtime allowance as earning"""
    try:
        overtime_amount = get_overtime_allowance_for_salary_slip(employee, start_date, end_date)
        
        if overtime_amount > 0:
            # Ensure component exists
            if not frappe.db.exists("Salary Component", "Overtime Allowance"):
                from phr.phr.utils.salary_component_integration import create_overtime_allowance_component
                create_overtime_allowance_component()
            
            add_salary_component(doc, "Overtime Allowance", overtime_amount, "Earning")
        
    except Exception as e:
        frappe.log_error(f"Error processing overtime allowance: {str(e)}", "PHR Salary Slip Events")

def process_shift_permission_deduction(doc, employee, start_date, end_date):
    """Process shift permission deduction"""
    try:
        deduction_amount = get_shift_permission_deduction_for_salary_slip(employee, start_date, end_date)
        
        if deduction_amount > 0:
            # Ensure component exists
            if not frappe.db.exists("Salary Component", "Shift Permission Deduction"):
                from phr.phr.utils.salary_component_integration import create_shift_permission_deduction_component
                create_shift_permission_deduction_component()
            
            add_salary_component(doc, "Shift Permission Deduction", deduction_amount, "Deduction")
        
    except Exception as e:
        frappe.log_error(f"Error processing shift permission deduction: {str(e)}", "PHR Salary Slip Events")

def add_salary_component(salary_slip_doc, component_name, amount, component_type):
    """Add or update salary component in salary slip"""
    try:
        # Check if component already exists
        found = False
        target_table = salary_slip_doc.get("deductions") if component_type == "Deduction" else salary_slip_doc.get("earnings")
        
        for item in target_table:
            if item.salary_component == component_name:
                item.amount = amount
                found = True
                break
        
        if not found:
            # Create new component
            if component_type == "Deduction":
                salary_slip_doc.append("deductions", {
                    "salary_component": component_name, 
                    "amount": amount
                })
            else:
                salary_slip_doc.append("earnings", {
                    "salary_component": component_name, 
                    "amount": amount
                })
        
    except Exception as e:
        frappe.log_error(f"Error adding salary component {component_name}: {str(e)}", "PHR Salary Slip Events")

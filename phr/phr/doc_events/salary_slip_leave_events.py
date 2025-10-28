import frappe
from frappe.utils import getdate, date_diff
from frappe import _
from phr.phr.utils.leave_management import calculate_sick_leave_deduction

@frappe.whitelist()
def before_submit(doc, method=None):
    """Handle salary slip before submit for sick leave deduction"""
    try:
        employee = doc.employee
        start_date = getdate(doc.start_date)
        end_date = getdate(doc.end_date)
        
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
                frappe.msgprint(_("Basic salary not found for employee {0}. Cannot calculate sick leave deduction.").format(employee), alert=True)
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
                frappe.msgprint(f"Sick leave deduction of {sick_leave_deduction_amount} added to salary slip for {employee}.", "PHR Salary Slip Events")
        
    except Exception as e:
        frappe.log_error(f"Error in salary slip before_submit for {doc.name}: {str(e)}", "PHR Salary Slip Events")

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

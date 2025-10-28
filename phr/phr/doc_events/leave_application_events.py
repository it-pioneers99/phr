import frappe
from frappe.utils import getdate, date_diff, nowdate
from frappe import _
from phr.phr.utils.leave_management import calculate_sick_leave_deduction

@frappe.whitelist()
def validate(doc, method=None):
    """Validate leave application"""
    try:
        if doc.leave_type and doc.employee:
            # Get leave type details
            leave_type_doc = frappe.get_doc("Leave Type", doc.leave_type)
            employee_doc = frappe.get_doc("Employee", doc.employee)
            
            # Check demographic compatibility
            if leave_type_doc.is_female and not employee_doc.is_female:
                frappe.throw(_("This leave type is only for female employees."))
            
            if leave_type_doc.is_muslim and not employee_doc.is_muslim:
                frappe.throw(_("This leave type is only for Muslim employees."))
            
            # Check sick leave deduction applicability
            if leave_type_doc.is_sick_leave:
                doc.is_sick_leave_deduction_applicable = 1
                
                # Calculate sick leave deduction amount
                if doc.from_date and doc.to_date:
                    total_days = date_diff(doc.to_date, doc.from_date) + 1
                    basic_salary = employee_doc.base or 0
                    
                    if basic_salary:
                        deduction_amount = calculate_sick_leave_deduction(
                            doc.employee, 
                            total_days, 
                            basic_salary
                        )
                        doc.sick_leave_deduction_amount = deduction_amount
                    else:
                        frappe.msgprint(_("Basic salary not found. Sick leave deduction cannot be calculated."), alert=True)
            else:
                doc.is_sick_leave_deduction_applicable = 0
                doc.sick_leave_deduction_amount = 0
        
        # Auto-calculate total leave days
        if doc.from_date and doc.to_date:
            start_date = getdate(doc.from_date)
            end_date = getdate(doc.to_date)
            doc.total_leave_days = date_diff(end_date, start_date) + 1
        
    except Exception as e:
        frappe.log_error(f"Error in leave application validate for {doc.name}: {str(e)}", "PHR Leave Events")

@frappe.whitelist()
def on_submit(doc, method=None):
    """Handle leave application submission"""
    try:
        # Update employee leave balances
        update_employee_leave_balance_after_leave(doc.employee, doc.leave_type, doc.total_leave_days, "deduct")
        
        if doc.is_sick_leave_deduction_applicable:
            frappe.msgprint(f"Sick leave submitted for {doc.employee_name}. Deduction will be calculated in salary slip.", "PHR Leave Events")
        
    except Exception as e:
        frappe.log_error(f"Error in leave application on_submit for {doc.name}: {str(e)}", "PHR Leave Events")

@frappe.whitelist()
def on_cancel(doc, method=None):
    """Handle leave application cancellation"""
    try:
        # Revert employee leave balances
        update_employee_leave_balance_after_leave(doc.employee, doc.leave_type, doc.total_leave_days, "add")
        
        frappe.msgprint(f"Leave application for {doc.employee_name} cancelled. Leave balance reverted.", "PHR Leave Events")
        
    except Exception as e:
        frappe.log_error(f"Error in leave application on_cancel for {doc.name}: {str(e)}", "PHR Leave Events")

def update_employee_leave_balance_after_leave(employee, leave_type, days, action="deduct"):
    """Update employee leave balance after leave application"""
    try:
        # Get current year for leave period
        current_year = getdate(nowdate()).year
        leave_period_start = getdate(f"{current_year}-01-01")
        leave_period_end = getdate(f"{current_year}-12-31")
        
        # Find the allocation
        allocation = frappe.get_list(
            "Leave Allocation",
            filters={
                "employee": employee, 
                "leave_type": leave_type, 
                "from_date": [">=", leave_period_start],
                "to_date": ["<=", leave_period_end],
                "docstatus": 1
            },
            fields=["name", "total_leaves_allocated", "leaves_taken"]
        )
        
        if allocation:
            allocation_doc = frappe.get_doc("Leave Allocation", allocation[0].name)
            
            if action == "deduct":
                allocation_doc.leaves_taken += days
            elif action == "add":
                allocation_doc.leaves_taken -= days
            
            allocation_doc.save(ignore_permissions=True)
            
            # Update employee leave balances
            from phr.phr.utils.leave_management import update_employee_leave_balances
            update_employee_leave_balances(employee)
            
            frappe.msgprint(f"Leave balance for {employee} updated for {leave_type}.", "PHR Leave Events")
        else:
            frappe.msgprint(f"No active leave allocation found for {employee} and {leave_type}.", "PHR Leave Events")
            
    except Exception as e:
        frappe.log_error(f"Error updating leave balance for {employee}: {str(e)}", "PHR Leave Events")

import frappe
from frappe import _
from phr.phr.phr.utils.leave_allocation import calculate_sick_leave_deduction

def before_submit(doc, method):
    """Calculate sick leave deductions before submitting salary slip"""
    try:
        # Get employee details
        employee = frappe.get_doc('Employee', doc.employee)
        
        # Get sick leave taken in the salary period
        sick_leave_days = get_sick_leave_days(doc.employee, doc.start_date, doc.end_date)
        
        if sick_leave_days > 0:
            # Calculate sick leave deduction
            monthly_salary = doc.gross_pay or 0
            deduction_data = calculate_sick_leave_deduction(
                doc.employee, 
                sick_leave_days, 
                monthly_salary
            )
            
            if deduction_data and deduction_data['deduction_amount'] > 0:
                # Add sick leave deduction to salary slip
                add_sick_leave_deduction(doc, deduction_data)
                
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave deduction for salary slip {doc.name}: {str(e)}")

def get_sick_leave_days(employee, start_date, end_date):
    """Get sick leave days taken by employee in the given period"""
    try:
        # Query leave applications for sick leave in the period
        sick_leave_days = frappe.db.sql("""
            SELECT SUM(total_leave_days) as total_days
            FROM `tabLeave Application`
            WHERE employee = %s
            AND leave_type = 'Sick Leave'
            AND status = 'Approved'
            AND from_date >= %s
            AND to_date <= %s
        """, (employee, start_date, end_date))
        
        return sick_leave_days[0][0] or 0
        
    except Exception as e:
        frappe.log_error(f"Error getting sick leave days for {employee}: {str(e)}")
        return 0

def add_sick_leave_deduction(doc, deduction_data):
    """Add sick leave deduction to salary slip"""
    try:
        # Check if sick leave deduction component exists
        if not frappe.db.exists('Salary Component', 'Sick Leave Deduction'):
            create_sick_leave_component()
        
        # Add deduction to salary slip
        doc.append('deductions', {
            'salary_component': 'Sick Leave Deduction',
            'amount': deduction_data['deduction_amount'],
            'description': f"Sick leave deduction for {deduction_data['deduction_details']}"
        })
        
    except Exception as e:
        frappe.log_error(f"Error adding sick leave deduction to salary slip: {str(e)}")

def create_sick_leave_component():
    """Create sick leave deduction salary component"""
    try:
        if not frappe.db.exists('Salary Component', 'Sick Leave Deduction'):
            component = frappe.get_doc({
                'doctype': 'Salary Component',
                'salary_component': 'Sick Leave Deduction',
                'type': 'Deduction',
                'description': 'Deduction for sick leave taken beyond 30 days',
                'is_tax_applicable': 1,
                'variable_based_on_taxable_salary': 1
            })
            component.insert()
            
    except Exception as e:
        frappe.log_error(f"Error creating sick leave salary component: {str(e)}")

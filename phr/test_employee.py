import frappe
from frappe import _

def test_employee_save():
    """Test if Employee document can be saved without PHR event handlers"""
    try:
        # Get an existing employee
        employee = frappe.get_doc("Employee", "MN-EMP00141")
        
        # Try to save the employee
        employee.save()
        
        frappe.msgprint("✅ Employee document saved successfully!")
        frappe.msgprint(f"Employee: {employee.employee_name}")
        frappe.msgprint(f"Status: {employee.status}")
        
    except Exception as e:
        frappe.msgprint(f"❌ Error saving Employee document: {str(e)}")
        import traceback
        traceback.print_exc()

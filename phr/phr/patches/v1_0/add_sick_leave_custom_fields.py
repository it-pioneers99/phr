import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Add custom fields for Sick Leave Balance and Sick Leave Remaining with display: none"""
    
    custom_fields = {
        "Employee": [
            {
                "fieldname": "sick_leave_balance_custom",
                "fieldtype": "Float",
                "label": "Sick Leave Balance",
                "insert_after": "sick_leave_remaining",
                "read_only": 1,
                "precision": 1,
                "hidden": 1,
                "print_hide": 1,
                "report_hide": 1,
                "allow_on_submit": 1,
                "depends_on": "eval:doc.status == 'Active'"
            },
            {
                "fieldname": "sick_leave_remaining_custom", 
                "fieldtype": "Float",
                "label": "Sick Leave Remaining",
                "insert_after": "sick_leave_balance_custom",
                "read_only": 1,
                "precision": 1,
                "hidden": 1,
                "print_hide": 1,
                "report_hide": 1,
                "allow_on_submit": 1,
                "depends_on": "eval:doc.status == 'Active'"
            }
        ]
    }
    
    try:
        create_custom_fields(custom_fields, update=True)
        frappe.msgprint("Sick Leave custom fields added successfully!")
        print("✅ Sick Leave custom fields added to Employee doctype")
    except Exception as e:
        frappe.log_error(f"Error creating Sick Leave custom fields: {str(e)}", "Sick Leave Custom Fields")
        print(f"❌ Error creating Sick Leave custom fields: {str(e)}")
        frappe.throw(f"Error creating Sick Leave custom fields: {str(e)}")

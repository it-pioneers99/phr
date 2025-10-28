#!/usr/bin/env python3
"""
Setup Sick Leave Custom Fields Script
This script adds custom fields for Sick Leave Balance and Sick Leave Remaining with display: none
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_sick_leave_custom_fields():
    """
    Setup custom fields for Sick Leave Balance and Sick Leave Remaining with display: none
    """
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
        frappe.msgprint(_("Sick Leave custom fields added successfully!"))
        print("✅ Sick Leave custom fields added to Employee doctype")
        return {"status": "success", "message": "Sick Leave custom fields added successfully!"}
    except Exception as e:
        frappe.log_error(f"Error creating Sick Leave custom fields: {str(e)}", "Sick Leave Custom Fields")
        print(f"❌ Error creating Sick Leave custom fields: {str(e)}")
        return {"status": "error", "message": str(e)}

def check_existing_fields():
    """
    Check if the custom fields already exist
    """
    fields_to_check = ["sick_leave_balance_custom", "sick_leave_remaining_custom"]
    
    for field_name in fields_to_check:
        if frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": field_name}):
            print(f"ℹ️ Field {field_name} already exists")
        else:
            print(f"❌ Field {field_name} does not exist")

if __name__ == "__main__":
    # This script can be run from the bench console
    print("Setting up Sick Leave custom fields...")
    check_existing_fields()
    result = setup_sick_leave_custom_fields()
    print(f"Setup result: {result}")

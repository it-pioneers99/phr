import frappe
from frappe import _

def setup_phr_system():
    """
    Complete setup of PHR system with all components
    """
    try:
        # Create salary components
        from phr.phr.utils.salary_components import create_salary_components
        create_salary_components()
        
        # Create sample penalty types
        create_sample_penalty_types()
        
        # Create custom fields if needed
        create_custom_fields()
        
        frappe.msgprint(_("PHR System setup completed successfully!"))
        
    except Exception as e:
        frappe.log_error(f"PHR Setup Error: {str(e)}", "PHR System Setup")
        frappe.throw(_("Error setting up PHR system: {0}").format(str(e)))

def create_sample_penalty_types():
    """
    Create sample penalty types based on Saudi Labor Law
    """
    penalty_types = [
        {
            "penalty_type": "Late Arrival",
            "penalty_value": 0.25,
            "is_percentage": 0,
            "penalty_levels": [
                {"occurrence_number": 1, "penalty_type_level": "Warning", "penalty_value_level": 0, "is_percentage_level": 0},
                {"occurrence_number": 2, "penalty_type_level": "Day Deduction", "penalty_value_level": 0.25, "is_percentage_level": 0},
                {"occurrence_number": 3, "penalty_type_level": "Day Deduction", "penalty_value_level": 0.5, "is_percentage_level": 0},
                {"occurrence_number": 4, "penalty_type_level": "Termination", "penalty_value_level": 0, "is_percentage_level": 0}
            ]
        },
        {
            "penalty_type": "Early Departure",
            "penalty_value": 0.25,
            "is_percentage": 0,
            "penalty_levels": [
                {"occurrence_number": 1, "penalty_type_level": "Warning", "penalty_value_level": 0, "is_percentage_level": 0},
                {"occurrence_number": 2, "penalty_type_level": "Day Deduction", "penalty_value_level": 0.25, "is_percentage_level": 0},
                {"occurrence_number": 3, "penalty_type_level": "Day Deduction", "penalty_value_level": 0.5, "is_percentage_level": 0},
                {"occurrence_number": 4, "penalty_type_level": "Termination", "penalty_value_level": 0, "is_percentage_level": 0}
            ]
        },
        {
            "penalty_type": "Absence Without Permission",
            "penalty_value": 1.0,
            "is_percentage": 0,
            "penalty_levels": [
                {"occurrence_number": 1, "penalty_type_level": "Day Deduction", "penalty_value_level": 1, "is_percentage_level": 0},
                {"occurrence_number": 2, "penalty_type_level": "Day Deduction", "penalty_value_level": 2, "is_percentage_level": 0},
                {"occurrence_number": 3, "penalty_type_level": "Withholding Promotion", "penalty_value_level": 0, "is_percentage_level": 0},
                {"occurrence_number": 4, "penalty_type_level": "Termination", "penalty_value_level": 0, "is_percentage_level": 0}
            ]
        },
        {
            "penalty_type": "Fingerprint Forget",
            "penalty_value": 0.25,
            "is_percentage": 0,
            "penalty_levels": [
                {"occurrence_number": 1, "penalty_type_level": "Day Deduction", "penalty_value_level": 0.25, "is_percentage_level": 0},
                {"occurrence_number": 2, "penalty_type_level": "Day Deduction", "penalty_value_level": 0.5, "is_percentage_level": 0},
                {"occurrence_number": 3, "penalty_type_level": "Day Deduction", "penalty_value_level": 1, "is_percentage_level": 0}
            ]
        }
    ]
    
    for penalty_data in penalty_types:
        if not frappe.db.exists("Penalty Type", penalty_data["penalty_type"]):
            penalty_doc = frappe.new_doc("Penalty Type")
            penalty_doc.penalty_type = penalty_data["penalty_type"]
            penalty_doc.penalty_value = penalty_data["penalty_value"]
            penalty_doc.is_percentage = penalty_data["is_percentage"]
            
            for level in penalty_data["penalty_levels"]:
                penalty_doc.append("penalty_levels", level)
            
            penalty_doc.insert()
            penalty_doc.submit()
            
            frappe.msgprint(_("Created penalty type: {0}").format(penalty_data["penalty_type"]))

def create_custom_fields():
    """
    Create custom fields for Employee doctype if needed
    """
    # Add nationality field to Employee if it doesn't exist
    if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "nationality"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Employee"
        custom_field.fieldname = "nationality"
        custom_field.fieldtype = "Select"
        custom_field.label = "Nationality"
        custom_field.options = "Saudi\nEgyptian\nIndian\nPakistani\nFilipino\nOther"
        custom_field.default = "Saudi"
        custom_field.insert_after = "employee_name"
        custom_field.insert()
        
        frappe.msgprint(_("Created custom field: Nationality"))
    
    # Add salary field to Employee if it doesn't exist
    if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "salary"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Employee"
        custom_field.fieldname = "salary"
        custom_field.fieldtype = "Currency"
        custom_field.label = "Current Salary"
        custom_field.insert_after = "nationality"
        custom_field.insert()
        
        frappe.msgprint(_("Created custom field: Current Salary"))
    
    # Add sick leave custom fields with display: none
    setup_sick_leave_custom_fields()

def setup_sick_leave_custom_fields():
    """
    Setup custom fields for Sick Leave Balance and Sick Leave Remaining with display: none
    """
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
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
    except Exception as e:
        frappe.log_error(f"Error creating Sick Leave custom fields: {str(e)}", "Sick Leave Custom Fields")
        frappe.throw(_("Error creating Sick Leave custom fields: {0}").format(str(e)))

if __name__ == "__main__":
    setup_phr_system()

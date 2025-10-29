"""
Server Script to Add PHR Custom Fields
This script can be executed via bench console or as a server script
"""



import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


@frappe.whitelist()
def add_phr_custom_fields():

    """
    Main function to add all PHR custom fields for Employee and Leave Type doctypes
    """

    try:
        frappe.msgprint(_("Starting PHR custom fields setup..."))
        
        # Add Employee custom fields
        setup_employee_fields()
        
        # Add Leave Type custom fields  
        setup_leave_type_fields()
        
        # Add sick leave related fields
        setup_sick_leave_fields()
        
        frappe.msgprint(_("PHR custom fields setup completed successfully!"))
        return {"status": "success", "message": "PHR custom fields added successfully"}
        
    except Exception as e:
        frappe.log_error(f"Error in add_phr_custom_fields: {str(e)}", "PHR Custom Fields")
        frappe.msgprint(_("Error setting up PHR custom fields: {0}").format(str(e)))
        return {"status": "error", "message": str(e)}


def setup_employee_fields():
    """
    Setup custom fields for Employee doctype
    """
    def _field_exists(dt: str, fieldname: str) -> bool:
        try:
            # Check in Custom Field
            if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
                return True
            # Check in DocType (standard fields)
            meta = frappe.get_meta(dt)
            return bool(meta.get_field(fieldname))
        except Exception:
            return False
    custom_fields = {
        "Employee": [
            {
                "fieldname": "contract_end_date",
                "fieldtype": "Date",
                "label": "Contract End Date",
                "insert_after": "date_of_joining",
                "reqd": 0
            },
            {
                "fieldname": "years_of_service",
                "fieldtype": "Float",
                "label": "Years of Service",
                "insert_after": "contract_end_date",
                "read_only": 1,
                "precision": 2
            },
            {
                "fieldname": "is_muslim",
                "fieldtype": "Check",
                "label": "Is Muslim",
                "insert_after": "years_of_service",
                "default": 0
            },
            {
                "fieldname": "is_female",
                "fieldtype": "Check", 
                "label": "Is Female",
                "insert_after": "is_muslim",
                "default": 0
            },
            {
                "fieldname": "testing_period_end_date",
                "fieldtype": "Date",
                "label": "Testing Period End Date",
                "insert_after": "is_female",
                "depends_on": "eval:doc.status == 'Active'"
            },
            {
                "fieldname": "testing_period_remaining_days",
                "fieldtype": "Int",
                "label": "Testing Period Remaining Days",
                "insert_after": "testing_period_end_date",
                "read_only": 1,
                "depends_on": "eval:doc.status == 'Active'"
            },
            {
                "fieldname": "leave_analysis_section",
                "fieldtype": "Section Break",
                "label": "Leave Analysis",
                "insert_after": "testing_period_remaining_days"
            },
            {
                "fieldname": "annual_leave_balance",
                "fieldtype": "Float",
                "label": "Annual Leave Balance",
                "insert_after": "leave_analysis_section",
                "read_only": 1,
                "precision": 1
            },
            {
                "fieldname": "sick_leave_balance",
                "fieldtype": "Float",
                "label": "Sick Leave Balance",
                "insert_after": "annual_leave_balance",
                "read_only": 1,
                "precision": 1
            },
            {
                "fieldname": "sick_leave_used",
                "fieldtype": "Float",
                "label": "Sick Leave Used",
                "insert_after": "sick_leave_balance",
                "read_only": 1,
                "precision": 1
            },
            {
                "fieldname": "sick_leave_remaining",
                "fieldtype": "Float",
                "label": "Sick Leave Remaining",
                "insert_after": "sick_leave_used",
                "read_only": 1,
                "precision": 1
            }
        ]
    }
    
    try:
        # Filter out fields that already exist to avoid ValidationError
        to_create = {"Employee": [f for f in custom_fields["Employee"] if not _field_exists("Employee", f["fieldname"]) ]}
        if to_create["Employee"]:
            create_custom_fields(to_create, update=True)
        else:
            frappe.msgprint(_("All Employee custom fields already exist. Skipping creation."))
        frappe.msgprint(_("Employee custom fields created successfully!"))
    except Exception as e:
        frappe.log_error(f"Error creating Employee custom fields: {str(e)}", "Employee Custom Fields")
        raise


def setup_leave_type_fields():
    """
    Setup custom fields for Leave Type doctype
    """
    def _field_exists(dt: str, fieldname: str) -> bool:
        try:
            if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
                return True
            meta = frappe.get_meta(dt)
            return bool(meta.get_field(fieldname))
        except Exception:
            return False
    custom_fields = {
        "Leave Type": [
            {
                "fieldname": "is_annual_leave",
                "fieldtype": "Check",
                "label": "Is Annual Leave",
                "insert_after": "max_days_allowed",
                "default": 0
            },
            {
                "fieldname": "is_sick_leave",
                "fieldtype": "Check",
                "label": "Is Sick Leave",
                "insert_after": "is_annual_leave",
                "default": 0
            },
            {
                "fieldname": "is_muslim",
                "fieldtype": "Check",
                "label": "Is Muslim",
                "insert_after": "is_sick_leave",
                "default": 0
            },
            {
                "fieldname": "is_female",
                "fieldtype": "Check",
                "label": "Is Female",
                "insert_after": "is_muslim",
                "default": 0
            },
            {
                "fieldname": "allocation_rules_section",
                "fieldtype": "Section Break",
                "label": "Allocation Rules",
                "insert_after": "is_female"
            },
            {
                "fieldname": "allocation_days_under_5_years",
                "fieldtype": "Int",
                "label": "Allocation Days (Under 5 Years)",
                "insert_after": "allocation_rules_section",
                "default": 21
            },
            {
                "fieldname": "allocation_days_over_5_years",
                "fieldtype": "Int",
                "label": "Allocation Days (Over 5 Years)",
                "insert_after": "allocation_days_under_5_years",
                "default": 30
            }
        ]
    }
    
    try:
        to_create = {"Leave Type": [f for f in custom_fields["Leave Type"] if not _field_exists("Leave Type", f["fieldname"]) ]}
        if to_create["Leave Type"]:
            create_custom_fields(to_create, update=True)
        else:
            frappe.msgprint(_("All Leave Type custom fields already exist. Skipping creation."))
        frappe.msgprint(_("Leave Type custom fields created successfully!"))
    except Exception as e:
        frappe.log_error(f"Error creating Leave Type custom fields: {str(e)}", "Leave Type Custom Fields")
        raise


def setup_sick_leave_fields():
    """
    Setup hidden custom fields for Sick Leave tracking
    """
    def _field_exists(dt: str, fieldname: str) -> bool:
        try:
            if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
                return True
            meta = frappe.get_meta(dt)
            return bool(meta.get_field(fieldname))
        except Exception:
            return False
    custom_fields = {
        "Employee": [
            {
                "fieldname": "sick_leave_balance_custom",
                "fieldtype": "Float",
                "label": "Sick Leave Balance (Hidden)",
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
                "label": "Sick Leave Remaining (Hidden)",
                "insert_after": "sick_leave_balance_custom",
                "read_only": 1,
                "precision": 1,
                "hidden": 1,
                "print_hide": 1,
                "report_hide": 1,
                "allow_on_submit": 1,
                "depends_on": "eval:doc.status == 'Active'"
            },
            {
                "fieldname": "nationality",
                "fieldtype": "Select",
                "label": "Nationality",
                "options": "Saudi\nEgyptian\nIndian\nPakistani\nFilipino\nOther",
                "default": "Saudi",
                "insert_after": "employee_name"
            },
            {
                "fieldname": "salary",
                "fieldtype": "Currency",
                "label": "Current Salary",
                "insert_after": "nationality"
            }
        ]
    }
    
    try:
        to_create = {"Employee": [f for f in custom_fields["Employee"] if not _field_exists("Employee", f["fieldname"]) ]}
        if to_create["Employee"]:
            create_custom_fields(to_create, update=True)
        else:
            frappe.msgprint(_("All additional PHR custom fields already exist. Skipping creation."))
        frappe.msgprint(_("Additional PHR custom fields created successfully!"))
    except Exception as e:
        frappe.log_error(f"Error creating additional PHR custom fields: {str(e)}", "PHR Additional Fields")
        raise

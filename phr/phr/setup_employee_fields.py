import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_employee_custom_fields():
    """Setup custom fields for Employee doctype"""
    
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
        create_custom_fields(custom_fields, update=True)
        frappe.msgprint(_("Employee custom fields created successfully!"))
    except Exception as e:
        frappe.log_error(f"Error creating Employee custom fields: {str(e)}", "Employee Custom Fields")
        frappe.throw(_("Error creating Employee custom fields: {0}").format(str(e)))

def setup_leave_type_custom_fields():
    """Setup custom fields for Leave Type doctype"""
    
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
        create_custom_fields(custom_fields, update=True)
        frappe.msgprint(_("Leave Type custom fields created successfully!"))
    except Exception as e:
        frappe.log_error(f"Error creating Leave Type custom fields: {str(e)}", "Leave Type Custom Fields")
        frappe.throw(_("Error creating Leave Type custom fields: {0}").format(str(e)))

if __name__ == "__main__":
    setup_employee_custom_fields()
    setup_leave_type_custom_fields()

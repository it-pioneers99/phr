import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_dynamic_leave_system():
    """Setup dynamic leave management system for PHR app"""
    
    # Custom fields for Employee doctype
    employee_custom_fields = {
        "Employee": [
            {
                "fieldname": "phr_leave_management_section",
                "fieldtype": "Section Break",
                "label": "PHR Leave Management",
                "insert_after": "attendance_and_leave_details"
            },
            {
                "fieldname": "years_of_service",
                "fieldtype": "Int",
                "label": "Years of Service",
                "read_only": 1,
                "insert_after": "phr_leave_management_section"
            },
            {
                "fieldname": "testing_period_end_date",
                "fieldtype": "Date",
                "label": "Testing Period End Date",
                "insert_after": "years_of_service"
            },
            {
                "fieldname": "remaining_testing_days",
                "fieldtype": "Int",
                "label": "Remaining Testing Days",
                "read_only": 1,
                "insert_after": "testing_period_end_date"
            },
            {
                "fieldname": "contract_end_date",
                "fieldtype": "Date",
                "label": "Contract End Date",
                "insert_after": "remaining_testing_days"
            },
            {
                "fieldname": "remaining_contract_days",
                "fieldtype": "Int",
                "label": "Remaining Contract Days",
                "read_only": 1,
                "insert_after": "contract_end_date"
            },
            {
                "fieldname": "is_muslim",
                "fieldtype": "Check",
                "label": "Is Muslim",
                "default": 0,
                "insert_after": "remaining_contract_days"
            },
            {
                "fieldname": "is_female",
                "fieldtype": "Check",
                "label": "Is Female",
                "default": 0,
                "insert_after": "is_muslim"
            },
            {
                "fieldname": "annual_leave_balance",
                "fieldtype": "Float",
                "label": "Annual Leave Balance",
                "read_only": 1,
                "precision": 1,
                "insert_after": "is_female"
            },
            {
                "fieldname": "annual_leave_used",
                "fieldtype": "Float",
                "label": "Annual Leave Used",
                "read_only": 1,
                "precision": 1,
                "insert_after": "annual_leave_balance"
            },
            {
                "fieldname": "annual_leave_remaining",
                "fieldtype": "Float",
                "label": "Annual Leave Remaining",
                "read_only": 1,
                "precision": 1,
                "insert_after": "annual_leave_used"
            },
            {
                "fieldname": "sick_leave_balance",
                "fieldtype": "Float",
                "label": "Sick Leave Balance",
                "read_only": 1,
                "precision": 1,
                "insert_after": "annual_leave_remaining"
            },
            {
                "fieldname": "sick_leave_used",
                "fieldtype": "Float",
                "label": "Sick Leave Used",
                "read_only": 1,
                "precision": 1,
                "insert_after": "sick_leave_balance"
            },
            {
                "fieldname": "sick_leave_remaining",
                "fieldtype": "Float",
                "label": "Sick Leave Remaining",
                "read_only": 1,
                "precision": 1,
                "insert_after": "sick_leave_used"
            },
            {
                "fieldname": "total_leave_balance",
                "fieldtype": "Float",
                "label": "Total Leave Balance",
                "read_only": 1,
                "precision": 1,
                "insert_after": "sick_leave_remaining"
            },
            {
                "fieldname": "notification_sent_90_days",
                "fieldtype": "Check",
                "label": "90 Days Notification Sent",
                "default": 0,
                "insert_after": "total_leave_balance"
            },
            {
                "fieldname": "notification_sent_30_days",
                "fieldtype": "Check",
                "label": "30 Days Notification Sent",
                "default": 0,
                "insert_after": "notification_sent_90_days"
            },
            {
                "fieldname": "notification_sent_7_days",
                "fieldtype": "Check",
                "label": "7 Days Notification Sent",
                "default": 0,
                "insert_after": "notification_sent_30_days"
            }
        ]
    }
    
    # Custom fields for Leave Type doctype
    leave_type_custom_fields = {
        "Leave Type": [
            {
                "fieldname": "phr_leave_categorization_section",
                "fieldtype": "Section Break",
                "label": "PHR Leave Categorization",
                "insert_after": "is_optional_leave"
            },
            {
                "fieldname": "is_annual_leave",
                "fieldtype": "Check",
                "label": "Is Annual Leave",
                "default": 0,
                "insert_after": "phr_leave_categorization_section"
            },
            {
                "fieldname": "is_sick_leave",
                "fieldtype": "Check",
                "label": "Is Sick Leave",
                "default": 0,
                "insert_after": "is_annual_leave"
            },
            {
                "fieldname": "is_muslim",
                "fieldtype": "Check",
                "label": "Is Muslim Leave",
                "default": 0,
                "insert_after": "is_sick_leave"
            },
            {
                "fieldname": "is_female",
                "fieldtype": "Check",
                "label": "Is Female Leave",
                "default": 0,
                "insert_after": "is_muslim"
            },
            {
                "fieldname": "days_per_year_under_5_years",
                "fieldtype": "Int",
                "label": "Days Per Year (Under 5 Years)",
                "default": 21,
                "insert_after": "is_female"
            },
            {
                "fieldname": "days_per_year_over_5_years",
                "fieldtype": "Int",
                "label": "Days Per Year (Over 5 Years)",
                "default": 30,
                "insert_after": "days_per_year_under_5_years"
            }
        ]
    }
    
    # Custom fields for Leave Allocation doctype
    leave_allocation_custom_fields = {
        "Leave Allocation": [
            {
                "fieldname": "phr_allocation_details_section",
                "fieldtype": "Section Break",
                "label": "PHR Allocation Details",
                "insert_after": "leave_policy_assignment"
            },
            {
                "fieldname": "years_of_service_at_allocation",
                "fieldtype": "Int",
                "label": "Years of Service at Allocation",
                "read_only": 1,
                "insert_after": "phr_allocation_details_section"
            },
            {
                "fieldname": "is_dynamic_allocation",
                "fieldtype": "Check",
                "label": "Is Dynamic Allocation",
                "default": 0,
                "insert_after": "years_of_service_at_allocation"
            }
        ]
    }
    
    # Custom fields for Leave Application doctype
    leave_application_custom_fields = {
        "Leave Application": [
            {
                "fieldname": "phr_leave_details_section",
                "fieldtype": "Section Break",
                "label": "PHR Leave Details",
                "insert_after": "half_day_date"
            },
            {
                "fieldname": "is_sick_leave_deduction_applicable",
                "fieldtype": "Check",
                "label": "Sick Leave Deduction Applicable",
                "read_only": 1,
                "insert_after": "phr_leave_details_section"
            },
            {
                "fieldname": "sick_leave_deduction_amount",
                "fieldtype": "Currency",
                "label": "Sick Leave Deduction Amount",
                "read_only": 1,
                "insert_after": "is_sick_leave_deduction_applicable"
            }
        ]
    }
    
    # Create all custom fields
    try:
        create_custom_fields(employee_custom_fields, update=True)
        create_custom_fields(leave_type_custom_fields, update=True)
        create_custom_fields(leave_allocation_custom_fields, update=True)
        create_custom_fields(leave_application_custom_fields, update=True)
        
        frappe.msgprint("Custom fields created successfully for dynamic leave management system")
        
    except Exception as e:
        frappe.log_error(f"Error creating custom fields: {str(e)}", "PHR Setup")
        frappe.msgprint(f"Error creating custom fields: {str(e)}", alert=True)

def create_leave_types():
    """Create default leave types for the system"""
    
    leave_types = [
        {
            "name": "Annual Leave",
            "leave_type_name": "Annual Leave",
            "is_annual_leave": 1,
            "is_sick_leave": 0,
            "is_muslim": 0,
            "is_female": 0,
            "days_per_year_under_5_years": 21,
            "days_per_year_over_5_years": 30,
            "max_continuous_days_allowed": 30,
            "is_optional_leave": 1,
            "is_compensatory": 0,
            "is_carry_forward": 1,
            "is_lwp": 0,
            "is_ppl": 0,
            "allow_negative": 0,
            "include_holiday": 0,
            "is_encash": 1,
            "is_earned_leave": 1
        },
        {
            "name": "Sick Leave",
            "leave_type_name": "Sick Leave",
            "is_annual_leave": 0,
            "is_sick_leave": 1,
            "is_muslim": 0,
            "is_female": 0,
            "days_per_year_under_5_years": 21,
            "days_per_year_over_5_years": 30,
            "max_continuous_days_allowed": 90,
            "is_optional_leave": 0,
            "is_compensatory": 0,
            "is_carry_forward": 0,
            "is_lwp": 0,
            "is_ppl": 0,
            "allow_negative": 0,
            "include_holiday": 0,
            "is_encash": 0,
            "is_earned_leave": 1
        },
        {
            "name": "Maternity Leave",
            "leave_type_name": "Maternity Leave",
            "is_annual_leave": 0,
            "is_sick_leave": 0,
            "is_muslim": 0,
            "is_female": 1,
            "days_per_year_under_5_years": 90,
            "days_per_year_over_5_years": 90,
            "max_continuous_days_allowed": 90,
            "is_optional_leave": 0,
            "is_compensatory": 0,
            "is_carry_forward": 0,
            "is_lwp": 0,
            "is_ppl": 0,
            "allow_negative": 0,
            "include_holiday": 0,
            "is_encash": 0,
            "is_earned_leave": 0
        },
        {
            "name": "Hajj Leave",
            "leave_type_name": "Hajj Leave",
            "is_annual_leave": 0,
            "is_sick_leave": 0,
            "is_muslim": 1,
            "is_female": 0,
            "days_per_year_under_5_years": 15,
            "days_per_year_over_5_years": 15,
            "max_continuous_days_allowed": 15,
            "is_optional_leave": 0,
            "is_compensatory": 0,
            "is_carry_forward": 0,
            "is_lwp": 0,
            "is_ppl": 0,
            "allow_negative": 0,
            "include_holiday": 0,
            "is_encash": 0,
            "is_earned_leave": 0
        }
    ]
    
    for leave_type_data in leave_types:
        if not frappe.db.exists("Leave Type", leave_type_data["name"]):
            try:
                leave_type = frappe.new_doc("Leave Type")
                for key, value in leave_type_data.items():
                    setattr(leave_type, key, value)
                leave_type.insert(ignore_permissions=True)
                frappe.msgprint(f"Created Leave Type: {leave_type_data['name']}")
            except Exception as e:
                frappe.log_error(f"Error creating leave type {leave_type_data['name']}: {str(e)}", "PHR Setup")
        else:
            frappe.msgprint(f"Leave Type {leave_type_data['name']} already exists")

def create_salary_components():
    """Create salary components for sick leave deduction"""
    
    salary_components = [
        {
            "name": "Sick Leave Deduction",
            "salary_component": "Sick Leave Deduction",
            "type": "Deduction",
            "is_tax_applicable": 0,
            "is_flexible_benefit": 0,
            "variable_based_on_taxable_salary": 0,
            "do_not_include_in_total": 0,
            "remove_if_zero_valued": 1,
            "statistical_component": 0,
            "depends_on_payment_days": 0,
            "exempted_from_income_tax": 0
        }
    ]
    
    for component_data in salary_components:
        if not frappe.db.exists("Salary Component", component_data["name"]):
            try:
                component = frappe.new_doc("Salary Component")
                for key, value in component_data.items():
                    setattr(component, key, value)
                component.insert(ignore_permissions=True)
                frappe.msgprint(f"Created Salary Component: {component_data['name']}")
            except Exception as e:
                frappe.log_error(f"Error creating salary component {component_data['name']}: {str(e)}", "PHR Setup")
        else:
            frappe.msgprint(f"Salary Component {component_data['name']} already exists")

if __name__ == "__main__":
    setup_dynamic_leave_system()
    create_leave_types()
    create_salary_components()
    frappe.db.commit()
    frappe.msgprint("Dynamic leave management system setup completed successfully!")

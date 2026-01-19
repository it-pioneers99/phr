"""
Server Script to Add PHR Custom Fields
This script can be executed via bench console or as a server script
Uses consolidated configuration file for all employee custom fields
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Import from same directory
try:
    from phr.phr.server_scripts.phr_employee_custom_fields_config import EMPLOYEE_CUSTOM_FIELDS
except ImportError:
    # Fallback: direct import from same directory
    import importlib.util
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'phr_employee_custom_fields_config.py')
    spec = importlib.util.spec_from_file_location("phr_employee_custom_fields_config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    EMPLOYEE_CUSTOM_FIELDS = config_module.EMPLOYEE_CUSTOM_FIELDS


@frappe.whitelist()
def add_phr_custom_fields():
    """
    Main function to add all PHR custom fields for Employee and Leave Type doctypes
    """
    try:
        frappe.msgprint(_("Starting PHR custom fields setup..."))
        
        # Add Employee custom fields (from consolidated config)
        setup_employee_fields()
        
        # Add Leave Type custom fields  
        setup_leave_type_fields()
        
        frappe.msgprint(_("PHR custom fields setup completed successfully!"))
        return {
            "status": "success", 
            "message": "PHR custom fields added successfully",
            "fields_added": {
                "employee_fields": len(EMPLOYEE_CUSTOM_FIELDS),
                "leave_type_fields": 7  # Update if Leave Type fields change
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in add_phr_custom_fields: {str(e)}", "PHR Custom Fields")
        frappe.msgprint(_("Error setting up PHR custom fields: {0}").format(str(e)))
        return {"status": "error", "message": str(e)}


def _field_exists(dt: str, fieldname: str) -> bool:
    """
    Helper function to check if a field already exists in a doctype
    Checks both custom fields and standard fields
    """
    try:
        # Check in Custom Field
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
            return True
        # Check in DocType (standard fields)
        meta = frappe.get_meta(dt)
        return bool(meta.get_field(fieldname))
    except Exception:
        return False


def setup_employee_fields():
    """
    Setup custom fields for Employee doctype
    Uses consolidated configuration from phr_employee_custom_fields_config.py
    """
    try:
        # Filter out fields that already exist to avoid ValidationError
        fields_to_create = [
            f for f in EMPLOYEE_CUSTOM_FIELDS 
            if not _field_exists("Employee", f["fieldname"])
        ]
        
        if not fields_to_create:
            frappe.msgprint(_("All Employee custom fields already exist. Skipping creation."))
            return
        
        # Create fields using consolidated configuration
        custom_fields = {"Employee": fields_to_create}
        create_custom_fields(custom_fields, update=True)
        
        created_count = len(fields_to_create)
        total_count = len(EMPLOYEE_CUSTOM_FIELDS)
        
        frappe.msgprint(_(
            "Employee custom fields: {0} new fields created, {1} fields already existed (total: {2})"
        ).format(created_count, total_count - created_count, total_count))
        
    except Exception as e:
        frappe.log_error(f"Error creating Employee custom fields: {str(e)}", "Employee Custom Fields")
        raise


def setup_leave_type_fields():
    """
    Setup custom fields for Leave Type doctype
    """
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
        # Filter out fields that already exist
        fields_to_create = [
            f for f in custom_fields["Leave Type"]
            if not _field_exists("Leave Type", f["fieldname"])
        ]
        
        if not fields_to_create:
            frappe.msgprint(_("All Leave Type custom fields already exist. Skipping creation."))
            return
        
        to_create = {"Leave Type": fields_to_create}
        create_custom_fields(to_create, update=True)
        
        created_count = len(fields_to_create)
        total_count = len(custom_fields["Leave Type"])
        
        frappe.msgprint(_(
            "Leave Type custom fields: {0} new fields created, {1} fields already existed (total: {2})"
        ).format(created_count, total_count - created_count, total_count))
        
    except Exception as e:
        frappe.log_error(f"Error creating Leave Type custom fields: {str(e)}", "Leave Type Custom Fields")
        raise


@frappe.whitelist()
def get_employee_custom_fields():
    """
    Get all custom fields for Employee doctype
    Returns both configured fields and existing fields in the system
    """
    try:
        # Get all custom fields from database
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Employee"},
            fields=["fieldname", "label", "fieldtype", "options", "default", "reqd", "read_only", "hidden", "description"],
            order_by="idx"
        )
        
        # Get configured fields from config file
        configured_fields = []
        try:
            from phr.phr.server_scripts.phr_employee_custom_fields_config import EMPLOYEE_CUSTOM_FIELDS
            configured_fields = EMPLOYEE_CUSTOM_FIELDS
        except ImportError:
            pass
        
        return {
            "status": "success",
            "custom_fields": custom_fields,
            "configured_fields": configured_fields,
            "total_custom_fields": len(custom_fields),
            "total_configured_fields": len(configured_fields)
        }
    except Exception as e:
        frappe.log_error(f"Error getting Employee custom fields: {str(e)}", "Get Employee Custom Fields")
        return {"status": "error", "message": str(e)}

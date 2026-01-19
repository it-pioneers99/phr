import frappe
from frappe import _
from phr.phr.phr.utils.leave_allocation import create_automatic_leave_allocation
from phr.phr.phr.doc_events.employee_leave_events import update_annual_leave_for_additional_flag

def on_update(doc, method):
    """Automatically create leave allocations when employee is created or joining date is updated"""
    # Check if is_additional_annual_leave flag changed
    if doc.has_value_changed('is_additional_annual_leave'):
        try:
            update_annual_leave_for_additional_flag(doc.name)
        except Exception as e:
            frappe.log_error(f"Error updating annual leave for additional flag for {doc.name}: {str(e)}")
    
    # Check if years of service would change (joining date changed)
    if doc.has_value_changed('date_of_joining') and doc.date_of_joining:
        try:
            # Update annual leave if additional flag is set
            is_additional_annual_leave = doc.get('is_additional_annual_leave', 0)
            if is_additional_annual_leave:
                update_annual_leave_for_additional_flag(doc.name)
            
            # Create automatic leave allocation
            result = create_automatic_leave_allocation(
                employee=doc.name,
                date_of_joining=doc.date_of_joining,
                is_female=doc.get('is_female', 0),
                is_muslim=doc.get('is_muslim', 0)
            )
            
            if result:
                frappe.msgprint(
                    _("Leave allocations have been automatically created for this employee"),
                    title=_("Success"),
                    indicator="green"
                )
            else:
                frappe.msgprint(
                    _("Some leave allocations could not be created. Please check the error log and use the 'Sync Leave Allocation' button to create them manually."),
                    title=_("Warning"),
                    indicator="orange"
                )
            
        except Exception as e:
            frappe.log_error(f"Error creating automatic leave allocation for {doc.name}: {str(e)}")
            frappe.msgprint(
                _("Error creating leave allocations. Please use the 'Sync Leave Allocation' button to create them manually."),
                title=_("Warning"),
                indicator="orange"
            )

def after_insert(doc, method):
    """Create leave allocations for new employees"""
    if doc.date_of_joining:
        try:
            # Create automatic leave allocation
            result = create_automatic_leave_allocation(
                employee=doc.name,
                date_of_joining=doc.date_of_joining,
                is_female=doc.get('is_female', 0),
                is_muslim=doc.get('is_muslim', 0)
            )
            
            if not result:
                frappe.msgprint(
                    _("Some leave allocations could not be created automatically. Please use the 'Sync Leave Allocation' button to create them manually."),
                    title=_("Warning"),
                    indicator="orange"
                )
            
        except Exception as e:
            frappe.log_error(f"Error creating automatic leave allocation for new employee {doc.name}: {str(e)}")
            frappe.msgprint(
                _("Error creating leave allocations. Please use the 'Sync Leave Allocation' button to create them manually."),
                title=_("Warning"),
                indicator="orange"
            )

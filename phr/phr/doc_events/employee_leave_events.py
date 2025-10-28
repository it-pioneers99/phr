import frappe
from frappe.utils import getdate, add_days, date_diff, nowdate
from frappe import _
from phr.phr.utils.leave_management import (
    calculate_years_of_service,
    calculate_testing_period_end_date,
    calculate_remaining_testing_days,
    calculate_remaining_contract_days,
    update_employee_leave_balances,
    create_dynamic_leave_allocation
)

@frappe.whitelist()
def after_insert(doc, method=None):
    """Handle employee creation"""
    try:
        frappe.msgprint(f"Employee {doc.employee_name} created. Initializing leave management...")
        
        # Update leave balances and contract details
        update_employee_leave_balances(doc.name)
        
        # Create initial leave allocations for current year
        create_initial_leave_allocations(doc.name)
        
        
        frappe.msgprint(f"Leave management initialized for {doc.employee_name}")
        
    except Exception as e:
        frappe.log_error(f"Error in employee after_insert for {doc.name}: {str(e)}", "PHR Employee Events")

@frappe.whitelist()
def on_update(doc, method=None):
    """Handle employee updates"""
    try:
        # Check if joining date or contract end date changed
        if doc.has_value_changed("date_of_joining") or doc.has_value_changed("contract_end_date"):
            frappe.msgprint(f"Employee {doc.employee_name} updated. Recalculating leave management...")
            update_employee_leave_balances(doc.name)
        
        # Check if demographic fields changed
        if (doc.has_value_changed("is_muslim") or doc.has_value_changed("is_female")):
            frappe.msgprint(f"Employee demographics updated. Updating leave allocations...")
            update_leave_allocations_for_demographics(doc.name)
        
        # Check if Is Additional Annual Leave field changed
        if doc.has_value_changed("is_additional_annual_leave"):
            frappe.msgprint(f"Employee additional annual leave status updated. Updating annual leave allocation...")
            update_annual_leave_for_additional_flag(doc.name)
        
        
    except Exception as e:
        frappe.log_error(f"Error in employee on_update for {doc.name}: {str(e)}", "PHR Employee Events")

@frappe.whitelist()
def on_cancel(doc, method=None):
    """Handle employee cancellation"""
    try:
        frappe.msgprint(f"Employee {doc.employee_name} cancelled. Updating leave management...")
        update_employee_leave_balances(doc.name)
        
    except Exception as e:
        frappe.log_error(f"Error in employee on_cancel for {doc.name}: {str(e)}", "PHR Employee Events")

def create_initial_leave_allocations(employee):
    """Create initial leave allocations for new employee"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        years_of_service = calculate_years_of_service(employee_doc.date_of_joining)
        
        # Get current year for leave period
        current_year = getdate(nowdate()).year
        leave_period_start = getdate(f"{current_year}-01-01")
        leave_period_end = getdate(f"{current_year}-12-31")
        
        # Get all leave types that should be allocated
        leave_types = frappe.get_list(
            "Leave Type",
            filters={
                "is_annual_leave": 1,
                "is_sick_leave": 1
            },
            fields=["name", "is_annual_leave", "is_sick_leave", "is_muslim", "is_female"]
        )
        
        for leave_type in leave_types:
            # Check demographic compatibility
            if is_leave_type_compatible(employee_doc, leave_type):
                # Use standard allocation
                create_dynamic_leave_allocation(
                    employee, 
                    leave_type.name, 
                    leave_period_start, 
                    leave_period_end
                )
        
    except Exception as e:
        frappe.log_error(f"Error creating initial leave allocations for {employee}: {str(e)}", "PHR Employee Events")

def is_leave_type_compatible(employee_doc, leave_type):
    """Check if leave type is compatible with employee demographics based on specific rules"""
    
    # Rule 1: If leave type has is_muslim == TRUE, allocate to employee which have is_female == TRUE && is_muslim == TRUE
    if leave_type.is_muslim == 1:
        if not (employee_doc.is_female == 1 and employee_doc.is_muslim == 1):
            return False
    
    # Rule 2: If leave type has is_female == TRUE && is_muslim == FALSE, allocate to employee which have is_female == TRUE && is_muslim == FALSE
    elif leave_type.is_female == 1 and leave_type.is_muslim == 0:
        if not (employee_doc.is_female == 1 and employee_doc.is_muslim == 0):
            return False
    
    # Rule 3: If leave type has is_female == TRUE (regardless of is_muslim), allocate to employee which have is_female == TRUE
    elif leave_type.is_female == 1:
        if not (employee_doc.is_female == 1):
            return False
    
    # Rule 4: Employee which have is_female == TRUE don't allocate to leave types which have is_female != TRUE
    # (This means if employee is female, they should only get leave types that are specifically for females)
    if employee_doc.is_female == 1 and leave_type.is_female != 1:
        return False
    
    return True

def update_leave_allocations_for_demographics(employee):
    """Update leave allocations when employee demographics change"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        
        # Get current year allocations
        current_year = getdate(nowdate()).year
        leave_period_start = getdate(f"{current_year}-01-01")
        leave_period_end = getdate(f"{current_year}-12-31")
        
        # Get all leave types (exclude Online Present as it's allocated separately)
        leave_types = frappe.get_list(
            "Leave Type",
            filters={
                "is_online_present": 0  # Exclude Online Present from automatic allocation
            },
            fields=["name", "is_muslim", "is_female"]
        )
        
        for leave_type in leave_types:
            # Check if allocation exists
            existing_allocation = frappe.db.exists(
                "Leave Allocation",
                {
                    "employee": employee,
                    "leave_type": leave_type.name,
                    "from_date": [">=", leave_period_start],
                    "to_date": ["<=", leave_period_end],
                    "docstatus": 1
                }
            )
            
            # Check compatibility
            is_compatible = is_leave_type_compatible(employee_doc, leave_type)
            
            if existing_allocation and not is_compatible:
                # Cancel incompatible allocation
                allocation_doc = frappe.get_doc("Leave Allocation", existing_allocation)
                allocation_doc.cancel()
                frappe.msgprint(f"Cancelled incompatible leave allocation: {leave_type.name}")
                
            elif not existing_allocation and is_compatible:
                # Create compatible allocation
                create_dynamic_leave_allocation(
                    employee, 
                    leave_type.name, 
                    leave_period_start, 
                    leave_period_end
                )
                frappe.msgprint(f"Created compatible leave allocation: {leave_type.name}")
        
    except Exception as e:
        frappe.log_error(f"Error updating leave allocations for demographics {employee}: {str(e)}", "PHR Employee Events")

def update_annual_leave_for_additional_flag(employee):
    """Update annual leave allocation when Is Additional Annual Leave flag changes"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        current_year = getdate(nowdate()).year
        
        # Calculate years of service
        if not employee_doc.date_of_joining:
            frappe.msgprint("Cannot calculate leave allocation: Employee joining date is required", alert=True)
            return
            
        joining_date = getdate(employee_doc.date_of_joining)
        current_date = getdate(nowdate())
        years_of_service = date_diff(current_date, joining_date) / 365.25
        
        # Get is_additional_annual_leave value from database (custom field)
        is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        # Determine annual leave days based on years of service and additional flag
        if is_additional_annual_leave:
            # If additional annual leave is checked, always give 30 days
            annual_leave_days = 30
        elif years_of_service < 5:
            # Less than 5 years = 21 days
            annual_leave_days = 21
        else:
            # 5+ years = 30 days
            annual_leave_days = 30
        
        # Get annual leave types
        annual_leave_types = frappe.get_all(
            "Leave Type",
            filters={"is_annual_leave": 1},
            fields=["name"]
        )
        
        for leave_type in annual_leave_types:
            # Get leave type details to check max_leaves_allowed
            leave_type_doc = frappe.get_doc("Leave Type", leave_type.name)
            max_allowed = leave_type_doc.get("max_leaves_allowed", 0)
            
            # Find existing allocation for current year
            existing_allocation = frappe.get_all(
                "Leave Allocation",
                filters={
                    "employee": employee,
                    "leave_type": leave_type.name,
                    "from_date": [">=", f"{current_year}-01-01"],
                    "to_date": ["<=", f"{current_year}-12-31"],
                    "docstatus": 1
                },
                fields=["name", "new_leaves_allocated"],
                limit=1
            )
            
            # Calculate the final allocation considering max_leaves_allowed
            final_allocation = annual_leave_days
            if max_allowed and final_allocation > max_allowed:
                final_allocation = max_allowed
                frappe.msgprint(f"Annual leave allocation capped at {max_allowed} days due to leave type limit for {leave_type.name}", alert=True)
            
            if existing_allocation:
                allocation_doc = frappe.get_doc("Leave Allocation", existing_allocation[0].name)
                current_allocation = allocation_doc.new_leaves_allocated or 0
                
                # Update allocation if it's different
                if current_allocation != final_allocation:
                    allocation_doc.new_leaves_allocated = final_allocation
                    allocation_doc.save()
                    
                    if is_additional_annual_leave:
                        reason = "Additional Annual Leave"
                        years_text = f"({years_of_service:.1f} years, {final_allocation} days)"
                    elif years_of_service < 5:
                        reason = "Standard Rate"
                        years_text = f"({years_of_service:.1f} years, {final_allocation} days)"
                    else:
                        reason = "5+ Years Service"
                        years_text = f"({years_of_service:.1f} years, {final_allocation} days)"
                    
                    frappe.msgprint(f"Updated {leave_type.name} allocation to {final_allocation} days {reason} {years_text}")
            else:
                # Create new allocation if none exists
                create_annual_leave_allocation(employee, leave_type.name, final_allocation, current_year)
                
                if is_additional_annual_leave:
                    reason = "Additional Annual Leave"
                    years_text = f"({years_of_service:.1f} years, {final_allocation} days)"
                elif years_of_service < 5:
                    reason = "Standard Rate"
                    years_text = f"({years_of_service:.1f} years, {final_allocation} days)"
                else:
                    reason = "5+ Years Service"
                    years_text = f"({years_of_service:.1f} years, {final_allocation} days)"
                
                frappe.msgprint(f"Created {leave_type.name} allocation with {final_allocation} days {reason} {years_text}")
        
    except Exception as e:
        frappe.log_error(f"Error updating annual leave for additional flag {employee}: {str(e)}", "PHR Employee Events")

def create_annual_leave_allocation(employee, leave_type, days, year):
    """Create annual leave allocation for employee"""
    try:
        # Get leave type details to check max_leaves_allowed
        leave_type_doc = frappe.get_doc("Leave Type", leave_type)
        max_allowed = leave_type_doc.get("max_leaves_allowed", 0)
        
        # Respect max_leaves_allowed limit
        final_days = days
        if max_allowed and final_days > max_allowed:
            final_days = max_allowed
            frappe.msgprint(f"Annual leave allocation capped at {max_allowed} days due to leave type limit for {leave_type}", alert=True)
        
        allocation_doc = frappe.new_doc("Leave Allocation")
        allocation_doc.employee = employee
        allocation_doc.leave_type = leave_type
        allocation_doc.from_date = f"{year}-01-01"
        allocation_doc.to_date = f"{year}-12-31"
        allocation_doc.new_leaves_allocated = final_days
        allocation_doc.carry_forward = 0
        allocation_doc.insert()
        allocation_doc.submit()
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating annual leave allocation for {employee}: {str(e)}", "PHR Employee Events")

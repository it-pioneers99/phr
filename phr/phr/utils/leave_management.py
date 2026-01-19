import frappe
from frappe.utils import getdate, add_days, date_diff, nowdate, add_months, add_years
from frappe import _
from datetime import datetime, timedelta

def calculate_years_of_service(joining_date):
    """Calculate years of service from joining date"""
    if not joining_date:
        return 0
    
    joining = getdate(joining_date)
    today = getdate(nowdate())
    
    years = today.year - joining.year
    if (today.month, today.day) < (joining.month, joining.day):
        years -= 1
    
    return max(0, years)

def calculate_testing_period_end_date(joining_date, testing_period_months=6):
    """Calculate testing period end date (default 6 months)"""
    if not joining_date:
        return None
    
    joining = getdate(joining_date)
    return add_months(joining, testing_period_months)

def calculate_remaining_testing_days(testing_end_date):
    """Calculate remaining days in testing period"""
    if not testing_end_date:
        return 0
    
    end_date = getdate(testing_end_date)
    today = getdate(nowdate())
    
    remaining = date_diff(end_date, today)
    return max(0, remaining)

def calculate_remaining_contract_days(contract_end_date):
    """Calculate remaining days until contract end"""
    if not contract_end_date:
        return 0
    
    end_date = getdate(contract_end_date)
    today = getdate(nowdate())
    
    remaining = date_diff(end_date, today)
    return max(0, remaining)

def get_leave_allocation_days(leave_type, years_of_service):
    """Get leave allocation days based on years of service"""
    if not leave_type:
        return 0
    
    leave_type_doc = frappe.get_doc("Leave Type", leave_type)
    
    # Check if this is Online Present leave type - use max_leaves_allowed
    if hasattr(leave_type_doc, 'is_online_present') and leave_type_doc.is_online_present:
        return leave_type_doc.get("max_leaves_allowed", 12)
    
    # For other leave types, use the standard logic
    if years_of_service >= 5:
        days = leave_type_doc.get("days_per_year_over_5_years", 30)
    else:
        days = leave_type_doc.get("days_per_year_under_5_years", 21)
    
    # Ensure we don't exceed max_leaves_allowed if it's set
    max_allowed = leave_type_doc.get("max_leaves_allowed")
    if max_allowed and days > max_allowed:
        days = max_allowed
    
    return days

def create_dynamic_leave_allocation(employee, leave_type, from_date, to_date):
    """Create dynamic leave allocation for employee"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        years_of_service = calculate_years_of_service(employee_doc.date_of_joining)
        
        # Get allocation days based on years of service
        allocation_days = get_leave_allocation_days(leave_type, years_of_service)
        
        # Check if allocation already exists for this period
        existing_allocation = frappe.db.exists(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "docstatus": 1
            }
        )
        
        if existing_allocation:
            # Update existing allocation
            allocation_doc = frappe.get_doc("Leave Allocation", existing_allocation)
            allocation_doc.new_leaves_allocated = allocation_days
            allocation_doc.years_of_service_at_allocation = years_of_service
            allocation_doc.is_dynamic_allocation = 1
            allocation_doc.save(ignore_permissions=True)
            frappe.msgprint(f"Updated leave allocation for {employee} - {allocation_days} days")
        else:
            # Create new allocation
            allocation_doc = frappe.new_doc("Leave Allocation")
            allocation_doc.employee = employee
            allocation_doc.leave_type = leave_type
            allocation_doc.from_date = from_date
            allocation_doc.to_date = to_date
            allocation_doc.new_leaves_allocated = allocation_days
            allocation_doc.years_of_service_at_allocation = years_of_service
            allocation_doc.is_dynamic_allocation = 1
            allocation_doc.save(ignore_permissions=True)
            frappe.msgprint(f"Created leave allocation for {employee} - {allocation_days} days")
        
        return allocation_doc.name
        
    except Exception as e:
        frappe.log_error(f"Error creating leave allocation for {employee}: {str(e)}", "PHR Leave Management")
        return None

def update_employee_leave_balances(employee):
    """Update all leave balances for an employee"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        years_of_service = calculate_years_of_service(employee_doc.date_of_joining)
        
        # Update years of service
        employee_doc.years_of_service = years_of_service
        
        # Update testing period details
        if employee_doc.date_of_joining:
            testing_end_date = calculate_testing_period_end_date(employee_doc.date_of_joining)
            employee_doc.testing_period_end_date = testing_end_date
            employee_doc.remaining_testing_days = calculate_remaining_testing_days(testing_end_date)
        
        # Update contract details
        if employee_doc.contract_end_date:
            employee_doc.remaining_contract_days = calculate_remaining_contract_days(employee_doc.contract_end_date)
        
        # Get current year for leave period
        current_year = getdate(nowdate()).year
        leave_period_start = getdate(f"{current_year}-01-01")
        leave_period_end = getdate(f"{current_year}-12-31")
        
        # Update annual leave balance
        annual_leave_type = frappe.db.get_value("Leave Type", {"is_annual_leave": 1})
        if annual_leave_type:
            annual_allocation = frappe.db.get_value(
                "Leave Allocation",
                {
                    "employee": employee,
                    "leave_type": annual_leave_type,
                    "from_date": [">=", leave_period_start],
                    "to_date": ["<=", leave_period_end],
                    "docstatus": 1
                },
                ["total_leaves_allocated", "leaves_taken"],
                as_dict=True
            )
            
            if annual_allocation:
                employee_doc.annual_leave_balance = annual_allocation.total_leaves_allocated or 0
                employee_doc.annual_leave_used = annual_allocation.leaves_taken or 0
                employee_doc.annual_leave_remaining = (annual_allocation.total_leaves_allocated or 0) - (annual_allocation.leaves_taken or 0)
            else:
                # Create annual leave allocation if it doesn't exist
                create_dynamic_leave_allocation(employee, annual_leave_type, leave_period_start, leave_period_end)
                employee_doc.annual_leave_balance = get_leave_allocation_days(annual_leave_type, years_of_service)
                employee_doc.annual_leave_used = 0
                employee_doc.annual_leave_remaining = employee_doc.annual_leave_balance
        
        # Update sick leave balance
        sick_leave_type = frappe.db.get_value("Leave Type", {"is_sick_leave": 1})
        if sick_leave_type:
            sick_allocation = frappe.db.get_value(
                "Leave Allocation",
                {
                    "employee": employee,
                    "leave_type": sick_leave_type,
                    "from_date": [">=", leave_period_start],
                    "to_date": ["<=", leave_period_end],
                    "docstatus": 1
                },
                ["total_leaves_allocated", "leaves_taken"],
                as_dict=True
            )
            
            if sick_allocation:
                employee_doc.sick_leave_balance = sick_allocation.total_leaves_allocated or 0
                employee_doc.sick_leave_used = sick_allocation.leaves_taken or 0
                employee_doc.sick_leave_remaining = (sick_allocation.total_leaves_allocated or 0) - (sick_allocation.leaves_taken or 0)
            else:
                # Create sick leave allocation if it doesn't exist
                create_dynamic_leave_allocation(employee, sick_leave_type, leave_period_start, leave_period_end)
                employee_doc.sick_leave_balance = get_leave_allocation_days(sick_leave_type, years_of_service)
                employee_doc.sick_leave_used = 0
                employee_doc.sick_leave_remaining = employee_doc.sick_leave_balance
        
        # Calculate total leave balance
        employee_doc.total_leave_balance = (employee_doc.annual_leave_remaining or 0) + (employee_doc.sick_leave_remaining or 0)
        
        # Save employee document
        employee_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error updating leave balances for {employee}: {str(e)}", "PHR Leave Management")
        return False

def calculate_sick_leave_deduction(employee, total_sick_days, basic_salary):
    """Calculate sick leave deduction based on Saudi Labor Law"""
    if not basic_salary or total_sick_days <= 0:
        return 0
    
    daily_salary = basic_salary / 30  # Assuming 30 days in a month
    deduction_amount = 0
    
    if total_sick_days <= 30:
        # First 30 days: No deduction (fully paid)
        deduction_amount = 0
    elif total_sick_days <= 90:
        # Days 31-90: 25% deduction (75% paid)
        deduction_days = total_sick_days - 30
        deduction_amount = deduction_days * daily_salary * 0.25
    else:
        # Days 91+: 100% deduction (unpaid)
        deduction_days_75_percent = 60  # Days 31-90
        deduction_days_100_percent = total_sick_days - 90  # Days 91+
        
        deduction_amount = (deduction_days_75_percent * daily_salary * 0.25) + (deduction_days_100_percent * daily_salary)
    
    return deduction_amount

def get_employee_leave_summary(employee):
    """Get comprehensive leave summary for an employee"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        
        # Get all leave allocations for current year
        current_year = getdate(nowdate()).year
        leave_period_start = getdate(f"{current_year}-01-01")
        leave_period_end = getdate(f"{current_year}-12-31")
        
        allocations = frappe.get_list(
            "Leave Allocation",
            filters={
                "employee": employee,
                "from_date": [">=", leave_period_start],
                "to_date": ["<=", leave_period_end],
                "docstatus": 1
            },
            fields=["leave_type", "total_leaves_allocated", "leaves_taken", "leaves_taken"],
            order_by="leave_type"
        )
        
        # Get leave types with their categories
        leave_types = frappe.get_list(
            "Leave Type",
            fields=["name", "leave_type_name", "is_annual_leave", "is_sick_leave", "is_muslim", "is_female"],
            order_by="leave_type_name"
        )
        
        # Create summary
        summary = {
            "employee": employee,
            "employee_name": employee_doc.employee_name,
            "years_of_service": employee_doc.years_of_service,
            "remaining_testing_days": employee_doc.remaining_testing_days,
            "remaining_contract_days": employee_doc.remaining_contract_days,
            "allocations": [],
            "leave_types": leave_types
        }
        
        # Process allocations
        for allocation in allocations:
            leave_type_info = next((lt for lt in leave_types if lt.name == allocation.leave_type), None)
            if leave_type_info:
                summary["allocations"].append({
                    "leave_type": allocation.leave_type,
                    "leave_type_name": leave_type_info.leave_type_name,
                    "allocated": allocation.total_leaves_allocated or 0,
                    "used": allocation.leaves_taken or 0,
                    "remaining": (allocation.total_leaves_allocated or 0) - (allocation.leaves_taken or 0),
                    "is_annual_leave": leave_type_info.is_annual_leave,
                    "is_sick_leave": leave_type_info.is_sick_leave,
                    "is_muslim": leave_type_info.is_muslim,
                    "is_female": leave_type_info.is_female
                })
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Error getting leave summary for {employee}: {str(e)}", "PHR Leave Management")
        return None

def update_leave_balances_daily():
    """
    Daily task to update leave balances for all employees
    This function:
    1. Updates annual leave balances based on months of service
    2. Syncs leave allocations with actual usage
    3. Updates employee leave balance fields
    """
    try:
        # Get all active employees
        employees = frappe.get_list(
            "Employee",
            filters={"status": "Active", "date_of_joining": ["is", "set"]},
            fields=["name", "date_of_joining"]
        )
        
        updated_count = 0
        errors = []
        
        for employee in employees:
            try:
                # Update employee leave balances
                result = update_employee_leave_balances(employee.name)
                if result:
                    updated_count += 1
        
                # Also sync annual leave allocation based on months of service
                sync_annual_leave_allocation_daily(employee.name)
                
            except Exception as e:
                error_msg = f"Error updating leave balance for {employee.name}: {str(e)}"
                errors.append(error_msg)
                frappe.log_error(error_msg, "PHR Daily Leave Balance Sync")
        
        # Log summary
        if updated_count > 0:
            frappe.logger().info(f"Daily leave balance sync: Updated {updated_count} employees")
        
        if errors:
            frappe.logger().warning(f"Daily leave balance sync: {len(errors)} errors occurred")
        
        return {
            "status": "success",
            "updated_count": updated_count,
            "errors": len(errors)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in daily leave balance update: {str(e)}", "PHR Leave Management")
        return {"status": "error", "message": str(e)}

def sync_annual_leave_allocation_daily(employee):
    """
    Sync annual leave allocation daily based on months of service
    This ensures the allocation matches the actual months worked
    """
    try:
        from phr.phr.utils.leave_balance_calculation import (
            calculate_months_of_service,
            calculate_annual_leave_balance
        )
        from phr.phr.utils.leave_allocation_utils import get_or_create_leave_type
        
        employee_doc = frappe.get_doc("Employee", employee)
        
        if not employee_doc.date_of_joining:
            return False
        
        # Calculate months and years of service
        joining_date = getdate(employee_doc.date_of_joining)
        current_date = getdate(nowdate())
        months_of_service = calculate_months_of_service(joining_date, current_date)
        years_of_service = months_of_service / 12
        
        # Get annual leave type
        annual_leave_type = frappe.db.get_value("Leave Type", {"is_annual_leave": 1}, "name")
        if not annual_leave_type:
            # Try to get or create it
            annual_leave_type = get_or_create_leave_type("Annual Leave", is_annual_leave=True)
        
        # Calculate expected annual leave balance based on months of service
        is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            # 2.5 days per month = 30 days per year
            expected_balance = months_of_service * 2.5
        elif years_of_service < 5:
            # 1.75 days per month = 21 days per year
            expected_balance = months_of_service * 1.75
        else:
            # 2.5 days per month = 30 days per year
            expected_balance = months_of_service * 2.5
        
        # Get current year allocation
        current_year = current_date.year
        leave_period_start = getdate(f"{current_year}-01-01")
        leave_period_end = getdate(f"{current_year}-12-31")
        
        # Find existing allocation
        existing_allocation = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": annual_leave_type,
                "from_date": [">=", leave_period_start],
                "to_date": ["<=", leave_period_end],
                "docstatus": 1
            },
            fields=["name", "total_leaves_allocated"],
            limit=1
        )
        
        # Calculate expected allocation for the year (capped at annual limit)
        if is_additional_annual_leave:
            annual_limit = 30
        elif years_of_service < 5:
            annual_limit = 21
        else:
            annual_limit = 30
        
        # For current year, calculate based on months worked this year
        months_this_year = calculate_months_of_service(
            max(joining_date, leave_period_start),
            min(current_date, leave_period_end)
        )
        
        if is_additional_annual_leave:
            expected_allocation = min(months_this_year * 2.5, annual_limit)
        elif years_of_service < 5:
            expected_allocation = min(months_this_year * 1.75, annual_limit)
        else:
            expected_allocation = min(months_this_year * 2.5, annual_limit)
        
        # Update allocation if it exists and needs adjustment
        if existing_allocation:
            allocation_doc = frappe.get_doc("Leave Allocation", existing_allocation[0].name)
            current_allocation = allocation_doc.total_leaves_allocated or 0
            
            # Only update if there's a significant difference (more than 0.1 days)
            if abs(current_allocation - expected_allocation) > 0.1:
                allocation_doc.total_leaves_allocated = expected_allocation
                allocation_doc.save()
                frappe.db.commit()
                return True
        
        return False
        
    except Exception as e:
        frappe.log_error(f"Error syncing annual leave allocation for {employee}: {str(e)}", "PHR Daily Leave Balance Sync")
        return False

def check_contract_expiration_notifications():
    """Check and send contract expiration notifications"""
    try:
        today = getdate(nowdate())
        
        # 90 days notification
        employees_90_days = frappe.get_list(
            "Employee",
            filters={
                "contract_end_date": ["between", (add_days(today, 89), add_days(today, 91))],
                "notification_sent_90_days": 0,
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date"]
        )
        
        for employee in employees_90_days:
            send_contract_notification(employee.name, 90)
            frappe.db.set_value("Employee", employee.name, "notification_sent_90_days", 1)
        
        # 30 days notification
        employees_30_days = frappe.get_list(
            "Employee",
            filters={
                "contract_end_date": ["between", (add_days(today, 29), add_days(today, 31))],
                "notification_sent_30_days": 0,
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date"]
        )
        
        for employee in employees_30_days:
            send_contract_notification(employee.name, 30)
            frappe.db.set_value("Employee", employee.name, "notification_sent_30_days", 1)
        
        # 7 days notification
        employees_7_days = frappe.get_list(
            "Employee",
            filters={
                "contract_end_date": ["between", (add_days(today, 6), add_days(today, 8))],
                "notification_sent_7_days": 0,
                "status": "Active"
            },
            fields=["name", "employee_name", "contract_end_date"]
        )
        
        for employee in employees_7_days:
            send_contract_notification(employee.name, 7)
            frappe.db.set_value("Employee", employee.name, "notification_sent_7_days", 1)
        
        frappe.db.commit()
        frappe.msgprint(f"Contract notifications sent: 90 days ({len(employees_90_days)}), 30 days ({len(employees_30_days)}), 7 days ({len(employees_7_days)})")
        
    except Exception as e:
        frappe.log_error(f"Error in contract notification check: {str(e)}", "PHR Leave Management")

def send_contract_notification(employee, days_left):
    """Send contract expiration notification"""
    try:
        employee_doc = frappe.get_doc("Employee", employee)
        
        subject = f"Contract Expiration Alert: {days_left} days left for {employee_doc.employee_name}"
        message = f"""
        Dear HR Team,
        
        The contract for employee {employee_doc.employee_name} (ID: {employee}) 
        is expiring in {days_left} days on {employee_doc.contract_end_date}.
        
        Please take necessary action to renew or terminate the contract.
        
        Best regards,
        PHR System
        """
        
        # Send email to HR users
        hr_users = frappe.get_list(
            "User",
            filters={"roles": ["in", ["HR User", "System Manager"]]},
            fields=["email"]
        )
        
        recipients = [user.email for user in hr_users if user.email]
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message,
                doctype="Employee",
                name=employee
            )
        
        frappe.msgprint(f"Contract notification sent for {employee_doc.employee_name} ({days_left} days left)")
        
    except Exception as e:
        frappe.log_error(f"Error sending contract notification for {employee}: {str(e)}", "PHR Leave Management")

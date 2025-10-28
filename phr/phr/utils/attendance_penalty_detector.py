# -*- coding: utf-8 -*-
# Copyright (c) 2025, Pioneers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, get_time, time_diff_in_seconds, flt
from datetime import datetime, timedelta

def get_employee_shift(employee, checkin_time):
    """
    Get employee's shift assignment for a specific date
    
    Args:
        employee: Employee ID
        checkin_time: Checkin datetime
    
    Returns:
        Shift Type document or None
    """
    try:
        # Get employee's shift assignment
        shift_assignment = frappe.db.get_value(
            "Shift Assignment",
            filters={
                "employee": employee,
                "start_date": ["<=", getdate(checkin_time)],
                "end_date": [">=", getdate(checkin_time)],
                "docstatus": 1
            },
            fieldname="shift_type",
            order_by="start_date desc"
        )
        
        if shift_assignment:
            return frappe.get_doc("Shift Type", shift_assignment)
        
        # If no shift assignment, try to get from employee's default shift
        employee_doc = frappe.get_doc("Employee", employee)
        if employee_doc.default_shift:
            return frappe.get_doc("Shift Type", employee_doc.default_shift)
            
        return None
        
    except Exception as e:
        frappe.log_error(f"Error getting shift for employee {employee}: {str(e)}", "Shift Assignment")
        return None

def process_checkin_for_penalties(checkin_doc):
    """
    Process an Employee Checkin to detect and create penalties
    This function checks all penalty types and creates penalty records with penalty level rows
    
    Args:
        checkin_doc: Employee Checkin document
    """
    if not checkin_doc.employee:
        return
    
    # Get employee's shift assignment
    shift = get_employee_shift(checkin_doc.employee, checkin_doc.time)
    if not shift:
        return
    
    # Check for attendance-related penalties
    if checkin_doc.log_type == "IN":
        check_late_arrival(checkin_doc, shift)
    elif checkin_doc.log_type == "OUT":
        check_early_departure(checkin_doc, shift)
    
    # Check for other penalty types that might apply to this checkin
    check_other_penalty_types(checkin_doc, shift)


def check_late_arrival(checkin_doc, shift):
    """
    Check if employee arrived late and create penalty if needed
    
    Args:
        checkin_doc: Employee Checkin document
        shift: Shift Type document
    """
    if not shift.start_time:
        return
    
    checkin_time = get_time(checkin_doc.time)
    shift_start = get_time(shift.start_time)
    
    # Calculate lateness in minutes
    time_diff_seconds = time_diff_in_seconds(checkin_time, shift_start)
    lateness_minutes = time_diff_seconds / 60
    
    # Only process if actually late (positive minutes)
    if lateness_minutes <= 0:
        return
    
    # Determine penalty type based on lateness
    penalty_type_name = None
    violation_description = None
    
    if 15 <= lateness_minutes < 30:
        penalty_type_name = "Late Arrival 15-30 Minutes"
        violation_description = f"Arrived {int(lateness_minutes)} minutes late (15-30 min range)"
    
    elif 30 <= lateness_minutes < 45:
        penalty_type_name = "Late Arrival 30-45 Minutes"
        violation_description = f"Arrived {int(lateness_minutes)} minutes late (30-45 min range)"
    
    elif 45 <= lateness_minutes < 75:
        penalty_type_name = "Late Arrival 45-75 Minutes"
        violation_description = f"Arrived {int(lateness_minutes)} minutes late (45-75 min range)"
    
    elif lateness_minutes >= 75:
        penalty_type_name = "Late Arrival Over 75 Minutes"
        violation_description = f"Arrived {int(lateness_minutes)} minutes late (over 75 min)"
    
    if penalty_type_name:
        create_penalty_record(
            employee=checkin_doc.employee,
            violation_date=getdate(checkin_doc.time),
            penalty_type_name=penalty_type_name,
            violation_description=violation_description,
            checkin_reference=checkin_doc.name,
            lateness_minutes=lateness_minutes
        )


def check_early_departure(checkin_doc, shift):
    """
    Check if employee left early and create penalty if needed
    
    Args:
        checkin_doc: Employee Checkin document
        shift: Shift Type document
    """
    if not shift.end_time:
        return
    
    checkout_time = get_time(checkin_doc.time)
    shift_end = get_time(shift.end_time)
    
    # Calculate early leave in minutes (negative means left early)
    time_diff_seconds = time_diff_in_seconds(checkout_time, shift_end)
    early_minutes = abs(time_diff_seconds / 60)
    
    # Only process if left early (before shift end)
    if time_diff_seconds >= 0:  # Left on time or after
        return
    
    # Check if left more than 15 minutes early
    if early_minutes >= 15:
        penalty_type_name = "Early Departure Before 15 Minutes"
        violation_description = f"Left {int(early_minutes)} minutes early (before 15 min)"
        
        create_penalty_record(
            employee=checkin_doc.employee,
            violation_date=getdate(checkin_doc.time),
            penalty_type_name=penalty_type_name,
            violation_description=violation_description,
            checkin_reference=checkin_doc.name,
            early_minutes=early_minutes
        )


def check_other_penalty_types(checkin_doc, shift):
    """
    Check for other penalty types that might apply to this checkin
    This allows for custom penalty types beyond just attendance violations
    
    Args:
        checkin_doc: Employee Checkin document
        shift: Shift Type document
    """
    try:
        # Get all active penalty types
        penalty_types = frappe.get_all(
            "Penalty Type",
            filters={"docstatus": 1},  # Only submitted penalty types
            fields=["name", "penalty_type"]
        )
        
        for penalty_type in penalty_types:
            # Check if this penalty type should be applied to this checkin
            if should_apply_penalty_type(checkin_doc, shift, penalty_type):
                create_penalty_record(
                    employee=checkin_doc.employee,
                    violation_date=getdate(checkin_doc.time),
                    penalty_type_name=penalty_type.penalty_type,
                    violation_description=f"Penalty applied based on checkin at {checkin_doc.time}",
                    checkin_reference=checkin_doc.name
                )
                
    except Exception as e:
        frappe.log_error(
            f"Error checking other penalty types for checkin {checkin_doc.name}: {str(e)}",
            "Penalty Type Checker"
        )


def should_apply_penalty_type(checkin_doc, shift, penalty_type):
    """
    Determine if a penalty type should be applied to this checkin
    This can be customized based on business rules
    
    Args:
        checkin_doc: Employee Checkin document
        shift: Shift Type document
        penalty_type: Penalty Type document
    
    Returns:
        bool: True if penalty should be applied
    """
    # For now, only apply attendance-related penalty types
    # This can be extended to include other business rules
    
    penalty_name = penalty_type.penalty_type.lower()
    
    # Only apply if it's an attendance-related penalty
    if any(keyword in penalty_name for keyword in ['late', 'early', 'attendance', 'arrival', 'departure']):
        return True
    
    return False


def create_penalty_record(employee, violation_date, penalty_type_name, violation_description, 
                         checkin_reference=None, lateness_minutes=0, early_minutes=0):
    """
    Create a Penalty Record for attendance violation with penalty level rows in child table
    Penalty records are created with monthly cycles (day 21 to day 20 of next month)
    
    Args:
        employee: Employee ID
        violation_date: Date of violation
        penalty_type_name: Name of the Penalty Type
        violation_description: Description of the violation
        checkin_reference: Employee Checkin reference
        lateness_minutes: Minutes late
        early_minutes: Minutes early
    """
    print(f"DEBUG: Creating penalty record for {employee} - {penalty_type_name} - {checkin_reference}")
    frappe.logger().info(f"Creating penalty record for {employee} - {penalty_type_name} - {checkin_reference}")
    # Check if penalty type exists by penalty_type field
    penalty_type_name_doc = frappe.db.exists("Penalty Type", {"penalty_type": penalty_type_name})
    print(f"DEBUG: Penalty type lookup result: {penalty_type_name_doc}")
    frappe.logger().info(f"Penalty type lookup result: {penalty_type_name_doc}")
    if not penalty_type_name_doc:
        print(f"DEBUG: Penalty type not found: {penalty_type_name}")
        frappe.log_error(
            f"Penalty Type '{penalty_type_name}' not found. Please create attendance penalty types.",
            "Attendance Penalty Detector"
        )
        return
    
    # Get penalty type with levels
    penalty_type = frappe.get_doc("Penalty Type", penalty_type_name_doc)
    print(f"DEBUG: Found penalty type: {penalty_type_name_doc} with {len(penalty_type.penalty_levels)} levels")
    frappe.logger().info(f"Found penalty type: {penalty_type_name_doc} with {len(penalty_type.penalty_levels)} levels")
    
    if not penalty_type.penalty_levels:
        print(f"DEBUG: No penalty levels found")
        frappe.log_error(
            f"Penalty Type '{penalty_type_name}' has no penalty levels defined.",
            "Attendance Penalty Detector"
        )
        return
    
    # Get the current penalty period (day 21 to day 20 of next month)
    penalty_period = get_penalty_period(violation_date)
    print(f"DEBUG: Penalty period: {penalty_period}")
    
    # Count previous occurrences within the current penalty period
    occurrence_count = count_previous_violations_in_period(
        employee=employee,
        violation_type=penalty_type_name,
        penalty_period=penalty_period
    )
    print(f"DEBUG: Occurrence count: {occurrence_count}")
    
    # Determine current occurrence number (1st, 2nd, 3rd, 4th+)
    current_occurrence = occurrence_count + 1
    print(f"DEBUG: Current occurrence: {current_occurrence}")
    
    # Get the appropriate penalty level
    penalty_level = get_penalty_level_for_occurrence(penalty_type, current_occurrence)
    print(f"DEBUG: Penalty level: {penalty_level}")
    
    if not penalty_level:
        print(f"DEBUG: No penalty level found for occurrence {current_occurrence}")
        frappe.log_error(
            f"No penalty level found for occurrence {current_occurrence} in '{penalty_type_name}'",
            "Attendance Penalty Detector"
        )
        return
    
    # Calculate penalty amount
    penalty_amount = calculate_penalty_amount(
        employee=employee,
        penalty_level=penalty_level
    )
    print(f"DEBUG: Calculated penalty amount: {penalty_amount}")
    frappe.logger().info(f"Calculated penalty amount: {penalty_amount} for employee {employee}")
    
    # Check if penalty record already exists for this checkin
    print(f"DEBUG: Checking for existing penalty record...")
    existing = frappe.db.exists(
        "Penalty Record",
        {
            "employee": employee,
            "violation_date": violation_date,
            "violation_type": penalty_type_name_doc,  # Use document name for consistency
            "checkin_reference": checkin_reference
        }
    )
    print(f"DEBUG: Existing penalty record check result: {existing}")
    
    if existing:
        print(f"DEBUG: Penalty record already exists for checkin {checkin_reference}")
        frappe.logger().info(f"Penalty record already exists for checkin {checkin_reference}")
        return
    
    # Check if we need to create a new penalty record for this period
    print(f"DEBUG: Checking for existing period record...")
    existing_period_record = get_existing_penalty_record_for_period(
        employee=employee,
        violation_type=penalty_type_name,
        penalty_period=penalty_period
    )
    print(f"DEBUG: Existing period record: {existing_period_record}")
    frappe.logger().info(f"Existing period record: {existing_period_record}")
    
    if existing_period_record:
        # Update existing penalty record for this period
        print(f"DEBUG: Updating existing penalty record: {existing_period_record}")
        frappe.logger().info(f"Updating existing penalty record: {existing_period_record}")
        update_penalty_record_for_violation(
            penalty_record_name=existing_period_record,
            violation_description=violation_description,
            checkin_reference=checkin_reference,
            occurrence_number=current_occurrence,
            penalty_amount=penalty_amount,
            lateness_minutes=lateness_minutes,
            early_minutes=early_minutes
        )
        return
    
    # Create new Penalty Record for this period
    print(f"DEBUG: Creating new penalty record for period")
    frappe.logger().info(f"Creating new penalty record for period")
    penalty_record = frappe.new_doc("Penalty Record")
    penalty_record.employee = employee
    penalty_record.violation_date = violation_date
    penalty_record.violation_type = penalty_type_name_doc  # Use document name instead of penalty type name
    penalty_record.checkin_reference = checkin_reference
    penalty_record.violation_description = violation_description
    penalty_record.occurrence_number = current_occurrence
    penalty_record.penalty_amount = penalty_amount
    penalty_record.penalty_status = "Draft"
    print(f"DEBUG: Penalty record created with basic fields")
    
    # Add penalty period information
    penalty_record.penalty_period_start = penalty_period['start_date']
    penalty_record.penalty_period_end = penalty_period['end_date']
    
    # Add lateness/early minutes as custom fields if they exist
    if hasattr(penalty_record, 'lateness_minutes'):
        penalty_record.lateness_minutes = lateness_minutes
    if hasattr(penalty_record, 'early_minutes'):
        penalty_record.early_minutes = early_minutes
    
    # Add ALL penalty levels from the penalty type to the child table
    print(f"DEBUG: Adding penalty levels to child table...")
    for level in penalty_type.penalty_levels:
        penalty_record.append("penalty_levels", {
            "occurrence_number": level.occurrence_number,
            "penalty_type_level": "Percentage Deduction",  # All our penalties are percentage deductions
            "penalty_value_level": level.penalty_value_level,
            "is_percentage_level": level.is_percentage_level
        })
    print(f"DEBUG: Added {len(penalty_type.penalty_levels)} penalty levels")
    
    try:
        print(f"DEBUG: Inserting penalty record...")
        penalty_record.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"DEBUG: Penalty record inserted successfully: {penalty_record.name}")
        
        frappe.logger().info(
            f"Penalty Record created: {penalty_record.name} for {employee} - "
            f"{penalty_type_name} (Occurrence {current_occurrence}, Amount: {penalty_amount}) "
            f"with {len(penalty_type.penalty_levels)} penalty level rows"
        )
    except Exception as e:
        print(f"DEBUG: Error inserting penalty record: {str(e)}")
        frappe.log_error(
            f"Error creating penalty record for {employee}: {str(e)}",
            "Attendance Penalty Detector"
        )


def count_previous_violations(employee, violation_type, days_back=180):
    """
    Count how many times this violation occurred in the last N days
    
    Args:
        employee: Employee ID
        violation_type: Penalty Type name
        days_back: Number of days to look back (default 180)
    
    Returns:
        int: Count of previous violations
    """
    cutoff_date = frappe.utils.add_days(frappe.utils.today(), -days_back)
    
    count = frappe.db.count(
        "Penalty Record",
        filters={
            "employee": employee,
            "violation_type": violation_type,
            "violation_date": [">=", cutoff_date],
            "docstatus": ["!=", 2]  # Exclude cancelled
        }
    )
    
    return count


def get_penalty_level_for_occurrence(penalty_type, occurrence_number):
    """
    Get the penalty level for a specific occurrence number
    
    Args:
        penalty_type: Penalty Type document
        occurrence_number: Occurrence number (1, 2, 3, 4+)
    
    Returns:
        dict: Penalty level details or None
    """
    # Get penalty levels sorted by occurrence number
    levels = sorted(penalty_type.penalty_levels, key=lambda x: x.occurrence_number)
    
    # Find exact match or highest available level
    matching_level = None
    for level in levels:
        if level.occurrence_number == occurrence_number:
            matching_level = level
            break
        elif level.occurrence_number < occurrence_number:
            matching_level = level  # Use this if no exact match
    
    # If occurrence is higher than defined, use the highest level
    if not matching_level and levels:
        matching_level = levels[-1]
    
    return matching_level


def calculate_penalty_amount(employee, penalty_level):
    """
    Calculate penalty amount based on penalty level
    
    Args:
        employee: Employee ID
        penalty_level: Penalty Level row
    
    Returns:
        float: Penalty amount
    """
    # Get employee's daily wage
    daily_wage = get_employee_daily_wage(employee)
    
    if not daily_wage:
        frappe.log_error(
            f"Could not calculate daily wage for employee {employee}",
            "Attendance Penalty Calculator"
        )
        return 0
    
    # Calculate penalty based on type
    # For our penalty system, all penalties are percentage deductions
    if penalty_level.is_percentage_level:
        return (penalty_level.penalty_value_level / 100) * daily_wage
    else:
        return penalty_level.penalty_value_level


def get_employee_daily_wage(employee):
    """
    Get employee's daily wage for penalty calculation
    
    Args:
        employee: Employee ID
    
    Returns:
        float: Daily wage
    """
    # Try to get from latest salary structure assignment
    salary_structure_assignment = frappe.db.get_value(
        "Salary Structure Assignment",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fieldname="base",
        order_by="from_date desc"
    )
    
    if salary_structure_assignment:
        # Assuming 30 days per month
        return flt(salary_structure_assignment) / 30
    
    # Try to get from latest salary slip
    salary_slip = frappe.db.get_value(
        "Salary Slip",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fieldname=["gross_pay", "total_working_days"],
        order_by="posting_date desc",
        as_dict=1
    )
    
    if salary_slip and salary_slip.total_working_days:
        return flt(salary_slip.gross_pay) / flt(salary_slip.total_working_days)
    
    # Default calculation: assume basic salary and 30 days
    frappe.logger().warning(f"Using default daily wage calculation for {employee}")
    return 0


@frappe.whitelist()
def setup_attendance_penalty_types():
    """
    Create predefined attendance penalty types based on Saudi Labor Law
    
    This function creates 5 penalty types with progressive levels:
    1. Late Arrival 15-30 Minutes
    2. Late Arrival 30-45 Minutes
    3. Late Arrival 45-75 Minutes
    4. Late Arrival Over 75 Minutes
    5. Early Departure Before 15 Minutes
    """
    penalty_definitions = [
        {
            "name": "Late Arrival 15-30 Minutes",
            "description": "Being late to work shift from 15 up to 30 minutes without permission",
            "levels": [
                {"occurrence": 1, "type": "Warning", "value": 0, "is_percentage": True},
                {"occurrence": 2, "type": "Percentage Deduction", "value": 5, "is_percentage": True},
                {"occurrence": 3, "type": "Percentage Deduction", "value": 10, "is_percentage": True},
                {"occurrence": 4, "type": "Percentage Deduction", "value": 20, "is_percentage": True},
            ]
        },
        {
            "name": "Late Arrival 30-45 Minutes",
            "description": "Being late to work shift from 30 up to 45 minutes without permission",
            "levels": [
                {"occurrence": 1, "type": "Percentage Deduction", "value": 10, "is_percentage": True},
                {"occurrence": 2, "type": "Percentage Deduction", "value": 20, "is_percentage": True},
                {"occurrence": 3, "type": "Percentage Deduction", "value": 30, "is_percentage": True},
                {"occurrence": 4, "type": "Percentage Deduction", "value": 50, "is_percentage": True},
            ]
        },
        {
            "name": "Late Arrival 45-75 Minutes",
            "description": "Being late to work shift from 45 up to 75 minutes without permission",
            "levels": [
                {"occurrence": 1, "type": "Percentage Deduction", "value": 30, "is_percentage": True},
                {"occurrence": 2, "type": "Percentage Deduction", "value": 50, "is_percentage": True},
                {"occurrence": 3, "type": "Percentage Deduction", "value": 50, "is_percentage": True},
                {"occurrence": 4, "type": "Percentage Deduction", "value": 100, "is_percentage": True},
            ]
        },
        {
            "name": "Late Arrival Over 75 Minutes",
            "description": "Being late to work shift over 75 minutes without permission",
            "levels": [
                {"occurrence": 1, "type": "Warning", "value": 0, "is_percentage": True},
                {"occurrence": 2, "type": "Percentage Deduction", "value": 100, "is_percentage": True},
                {"occurrence": 3, "type": "Percentage Deduction", "value": 150, "is_percentage": True},
                {"occurrence": 4, "type": "Percentage Deduction", "value": 200, "is_percentage": True},
            ]
        },
        {
            "name": "Early Departure Before 15 Minutes",
            "description": "Being early to leave work shift before 15 minutes without permission",
            "levels": [
                {"occurrence": 1, "type": "Warning", "value": 0, "is_percentage": True},
                {"occurrence": 2, "type": "Percentage Deduction", "value": 5, "is_percentage": True},
                {"occurrence": 3, "type": "Percentage Deduction", "value": 15, "is_percentage": True},
                {"occurrence": 4, "type": "Percentage Deduction", "value": 50, "is_percentage": True},
            ]
        }
    ]
    
    created = []
    updated = []
    
    for penalty_def in penalty_definitions:
        # Check if penalty type already exists
        if frappe.db.exists("Penalty Type", penalty_def["name"]):
            # Update existing
            penalty_type = frappe.get_doc("Penalty Type", penalty_def["name"])
            updated.append(penalty_def["name"])
        else:
            # Create new
            penalty_type = frappe.new_doc("Penalty Type")
            penalty_type.penalty_type = penalty_def["name"]
            penalty_type.penalty_value = 0  # Default value, actual values in penalty_levels
            penalty_type.is_percentage = 1
            created.append(penalty_def["name"])
        
        # Clear existing levels and add new ones
        penalty_type.penalty_levels = []
        
        for level in penalty_def["levels"]:
            penalty_type.append("penalty_levels", {
                "occurrence_number": level["occurrence"],
                "penalty_type_level": level["type"],
                "penalty_value_level": level["value"],
                "is_percentage_level": level["is_percentage"]
            })
        
        penalty_type.save(ignore_permissions=True)
        frappe.db.commit()
    
    frappe.msgprint(
        _("Attendance Penalty Types Setup Complete<br>Created: {0}<br>Updated: {1}").format(
            ", ".join(created) if created else "None",
            ", ".join(updated) if updated else "None"
        ),
        title=_("Success"),
        indicator="green"
    )
    
    return {
        "created": created,
        "updated": updated
    }


def get_penalty_period(violation_date):
    """
    Get the penalty period (day 21 to day 20 of next month) for a given date
    
    Args:
        violation_date: Date of violation
    
    Returns:
        dict: {'start_date': date, 'end_date': date}
    """
    from frappe.utils import add_days, add_months, getdate
    
    violation_date = getdate(violation_date)
    year = violation_date.year
    month = violation_date.month
    day = violation_date.day
    
    # If day is 21 or later, current period started on 21st of current month
    if day >= 21:
        start_date = violation_date.replace(day=21)
        # End date is 20th of next month
        if month == 12:
            end_date = violation_date.replace(year=year+1, month=1, day=20)
        else:
            end_date = violation_date.replace(month=month+1, day=20)
    else:
        # If day is before 21st, current period started on 21st of previous month
        if month == 1:
            start_date = violation_date.replace(year=year-1, month=12, day=21)
        else:
            start_date = violation_date.replace(month=month-1, day=21)
        end_date = violation_date.replace(day=20)
    
    return {
        'start_date': start_date,
        'end_date': end_date
    }


def count_previous_violations_in_period(employee, violation_type, penalty_period):
    """
    Count how many times this violation occurred in the current penalty period
    
    Args:
        employee: Employee ID
        violation_type: Penalty Type name
        penalty_period: dict with start_date and end_date
    
    Returns:
        int: Count of previous violations in this period
    """
    # Get the penalty type document name
    penalty_type_doc = frappe.db.exists("Penalty Type", {"penalty_type": violation_type})
    if not penalty_type_doc:
        return 0
    
    count = frappe.db.count(
        "Penalty Record",
        filters={
            "employee": employee,
            "violation_type": penalty_type_doc,  # Use document name
            "violation_date": [">=", penalty_period['start_date']],
            "violation_date": ["<=", penalty_period['end_date']],
            "docstatus": ["!=", 2]  # Exclude cancelled
        }
    )
    
    return count


def get_existing_penalty_record_for_period(employee, violation_type, penalty_period):
    """
    Get existing penalty record for this employee, violation type, and period
    
    Args:
        employee: Employee ID
        violation_type: Penalty Type name
        penalty_period: dict with start_date and end_date
    
    Returns:
        str: Name of existing penalty record or None
    """
    # Get the penalty type document name
    penalty_type_doc = frappe.db.exists("Penalty Type", {"penalty_type": violation_type})
    if not penalty_type_doc:
        return None
    
    existing = frappe.db.get_value(
        "Penalty Record",
        filters={
            "employee": employee,
            "violation_type": penalty_type_doc,  # Use document name
            "penalty_period_start": penalty_period['start_date'],
            "penalty_period_end": penalty_period['end_date'],
            "docstatus": ["!=", 2]  # Exclude cancelled
        },
        fieldname="name"
    )
    
    return existing


def update_penalty_record_for_violation(penalty_record_name, violation_description, 
                                      checkin_reference, occurrence_number, penalty_amount,
                                      lateness_minutes=0, early_minutes=0):
    """
    Update existing penalty record with new violation information
    
    Args:
        penalty_record_name: Name of existing penalty record
        violation_description: Description of new violation
        checkin_reference: Employee Checkin reference
        occurrence_number: Current occurrence number
        penalty_amount: Penalty amount for this occurrence
        lateness_minutes: Minutes late
        early_minutes: Minutes early
    """
    try:
        penalty_record = frappe.get_doc("Penalty Record", penalty_record_name)
        
        # Update violation description to include new violation
        if penalty_record.violation_description:
            penalty_record.violation_description += f"\n{getdate().strftime('%Y-%m-%d')}: {violation_description}"
        else:
            penalty_record.violation_description = f"{getdate().strftime('%Y-%m-%d')}: {violation_description}"
        
        # Update occurrence number and penalty amount
        penalty_record.occurrence_number = occurrence_number
        penalty_record.penalty_amount = penalty_amount
        
        # Update lateness/early minutes if fields exist
        if hasattr(penalty_record, 'lateness_minutes'):
            penalty_record.lateness_minutes = max(penalty_record.lateness_minutes or 0, lateness_minutes)
        if hasattr(penalty_record, 'early_minutes'):
            penalty_record.early_minutes = max(penalty_record.early_minutes or 0, early_minutes)
        
        penalty_record.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.logger().info(
            f"Updated penalty record {penalty_record_name} for occurrence {occurrence_number}"
        )
        
    except Exception as e:
        frappe.log_error(
            f"Error updating penalty record {penalty_record_name}: {str(e)}",
            "Penalty Record Update"
        )


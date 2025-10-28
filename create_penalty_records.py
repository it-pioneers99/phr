#!/usr/bin/env python3
"""
Script to create 5 sample penalty records and submit them
"""

import frappe
from frappe import _


def create_penalty_records():
    """Create 5 sample penalty records with shift types"""
    
    # Get available shift types
    shift_types = frappe.get_all("Shift Type", fields=["name", "start_time", "end_time"], limit=5)
    
    if not shift_types:
        print("No shift types found. Creating sample shift types first...")
        # Create sample shift types
        sample_shifts = [
            {"name": "Morning Shift", "start_time": "08:00:00", "end_time": "16:00:00"},
            {"name": "Evening Shift", "start_time": "16:00:00", "end_time": "00:00:00"},
            {"name": "Night Shift", "start_time": "00:00:00", "end_time": "08:00:00"},
            {"name": "Day Shift", "start_time": "09:00:00", "end_time": "17:00:00"},
            {"name": "Afternoon Shift", "start_time": "14:00:00", "end_time": "22:00:00"}
        ]
        
        for shift_data in sample_shifts:
            if not frappe.db.exists("Shift Type", shift_data["name"]):
                shift_doc = frappe.get_doc({
                    "doctype": "Shift Type",
                    "name": shift_data["name"],
                    "start_time": shift_data["start_time"],
                    "end_time": shift_data["end_time"]
                })
                shift_doc.insert()
                print(f"Created shift type: {shift_data['name']}")
        
        shift_types = sample_shifts
    
    # Get available employees
    employees = frappe.get_all("Employee", fields=["name", "employee_name"], limit=5)
    
    if not employees:
        print("No employees found. Creating sample employees first...")
        # Create sample employees
        sample_employees = [
            {"name": "EMP-001", "employee_name": "Ahmed Ali"},
            {"name": "EMP-002", "employee_name": "Sara Mohamed"},
            {"name": "EMP-003", "employee_name": "Omar Hassan"},
            {"name": "EMP-004", "employee_name": "Fatima Ahmed"},
            {"name": "EMP-005", "employee_name": "Khalid Ibrahim"}
        ]
        
        for emp_data in sample_employees:
            if not frappe.db.exists("Employee", emp_data["name"]):
                employee_doc = frappe.get_doc({
                    "doctype": "Employee",
                    "name": emp_data["name"],
                    "employee_name": emp_data["employee_name"],
                    "status": "Active",
                    "company": frappe.get_value("Company", {"is_group": 0}, "name") or "Test Company"
                })
                employee_doc.insert()
                print(f"Created employee: {emp_data['employee_name']}")
        
        employees = sample_employees
    
    # Create penalty types for each shift
    penalty_types = []
    for i, shift in enumerate(shift_types[:5]):
        penalty_type_name = f"Late Arrival - {shift['name']}"
        
        # Check if penalty type already exists
        if not frappe.db.exists("Penalty Type", penalty_type_name):
            penalty_type_doc = frappe.get_doc({
                "doctype": "Penalty Type",
                "penalty_type": penalty_type_name,
                "shift_type": shift['name'],
                "penalty_value": 50.0,
                "is_percentage": 1,
                "time_from": shift['start_time'],
                "time_to": shift['end_time']
            })
            penalty_type_doc.insert()
            penalty_types.append(penalty_type_name)
            print(f"Created penalty type: {penalty_type_name}")
        else:
            penalty_types.append(penalty_type_name)
            print(f"Penalty type already exists: {penalty_type_name}")
    
    # Create penalty records
    for i in range(5):
        employee = employees[i % len(employees)]
        penalty_type = penalty_types[i % len(penalty_types)]
        
        penalty_record = frappe.get_doc({
            "doctype": "Penalty Record",
            "employee": employee['name'],
            "violation_date": frappe.utils.today(),
            "violation_type": penalty_type,
            "violation_description": f"Late arrival violation for {employee['employee_name']}",
            "lateness_minutes": 30 + (i * 10),  # Different lateness minutes for each record
            "penalty_status": "Draft"
        })
        
        penalty_record.insert()
        print(f"Created penalty record for {employee['employee_name']}")
        
        # Submit the record
        penalty_record.submit()
        print(f"Submitted penalty record for {employee['employee_name']}")
    
    print("Successfully created and submitted 5 penalty records!")
    
    # Show summary
    total_records = frappe.db.count("Penalty Record", {"docstatus": 1})
    print(f"Total submitted penalty records in system: {total_records}")


if __name__ == "__main__":
    create_penalty_records()

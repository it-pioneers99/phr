#!/usr/bin/env python3
"""
Import Biometric Backup Data to ERPNext Employee Checkin Records
"""

import csv
from datetime import datetime
import frappe

def import_attendance_data():
    """Import attendance data from CSV to ERPNext"""
    
    print("🔄 Starting attendance data import...")
    
    # Backup file path
    backup_file = "/home/gadallah/frappe-bench/biometric-attendance-sync-tool/logs/backups/biometric_backup_20251021_160829.csv"
    
    success_count = 0
    error_count = 0
    employee_cache = {}
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
        
        print(f"📊 Loaded {len(records)} records from backup file")
        
        # Process first 20 records as test
        test_records = records[:20]
        print(f"🧪 Processing first {len(test_records)} records as test...")
        
        for i, record in enumerate(test_records, 1):
            try:
                user_id = record['user_id']
                
                # Get or create employee
                if user_id not in employee_cache:
                    employee = get_or_create_employee(user_id)
                    if employee:
                        employee_cache[user_id] = employee
                    else:
                        error_count += 1
                        print(f"❌ Error processing record {i}: Could not create employee for user_id {user_id}")
                        continue
                else:
                    employee = employee_cache[user_id]
                
                # Create checkin record
                if create_checkin_record(record, employee):
                    success_count += 1
                    print(f"✅ Created checkin for employee {employee.name} at {record['timestamp']}")
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing record {i}: {str(e)}")
        
        print(f"📊 Test Import Summary:")
        print(f"   ✅ Successfully imported: {success_count} records")
        print(f"   ❌ Errors: {error_count} records")
        if success_count + error_count > 0:
            print(f"   📈 Success rate: {(success_count/(success_count+error_count)*100):.1f}%")
        
        return success_count, error_count
        
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        return 0, 0

def get_or_create_employee(user_id):
    """Get or create employee by biometric user ID"""
    try:
        # Try to find employee by biometric_id field
        employees = frappe.get_all("Employee", 
                                 filters={"biometric_id": str(user_id)}, 
                                 fields=["name"])
        
        if employees:
            return frappe.get_doc("Employee", employees[0].name)
        
        # Try to find by employee ID
        employees = frappe.get_all("Employee", 
                                 filters={"employee": str(user_id)}, 
                                 fields=["name"])
        
        if employees:
            return frappe.get_doc("Employee", employees[0].name)
        
        # Create a basic employee record
        print(f"⚠️  Employee not found for user_id {user_id}, creating basic record")
        return create_basic_employee(user_id)
        
    except Exception as e:
        print(f"❌ Error getting employee for user_id {user_id}: {str(e)}")
        return None

def create_basic_employee(user_id):
    """Create a basic employee record for unknown user_id"""
    try:
        employee_doc = frappe.new_doc("Employee")
        employee_doc.employee = f"EMP-{user_id}"
        employee_doc.first_name = f"Employee {user_id}"
        employee_doc.biometric_id = str(user_id)
        employee_doc.status = "Active"
        employee_doc.date_of_joining = datetime.now().date()
        employee_doc.insert(ignore_permissions=True)
        print(f"✅ Created employee record for user_id {user_id}")
        return employee_doc
    except Exception as e:
        print(f"❌ Error creating employee for user_id {user_id}: {str(e)}")
        return None

def create_checkin_record(record, employee):
    """Create Employee Checkin record"""
    try:
        # Parse the timestamp
        timestamp = datetime.fromisoformat(record['timestamp'])
        
        # Convert punch value to log type
        punch = int(record['punch'])
        log_type = "IN" if punch in [0, 4] else "OUT"
        
        # Check if record already exists
        existing = frappe.get_all("Employee Checkin", 
                                filters={
                                    "employee": employee.name,
                                    "time": timestamp,
                                    "log_type": log_type
                                })
        
        if existing:
            print(f"⚠️  Record already exists for employee {employee.name} at {timestamp}")
            return True  # Already exists, skip
        
        # Create Employee Checkin record
        checkin_doc = frappe.new_doc("Employee Checkin")
        checkin_doc.employee = employee.name
        checkin_doc.time = timestamp
        checkin_doc.log_type = log_type
        checkin_doc.device_id = record.get('device_id', '15')
        checkin_doc.source = "Biometric Restore"
        
        # Use original log_type if available
        if 'log_type' in record:
            checkin_doc.log_type = record['log_type']
        
        checkin_doc.insert(ignore_permissions=True)
        return True
        
    except Exception as e:
        print(f"❌ Error creating checkin for employee {employee.name}: {str(e)}")
        return False

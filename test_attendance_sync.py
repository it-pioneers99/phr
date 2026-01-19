#!/usr/bin/env python3
"""
Test script for Attendance Sync API
Run this script using: bench --site [site-name] execute phr.test_attendance_sync.test_sync
"""

import frappe
from frappe.utils import now_datetime, add_days, getdate


def test_sync():
    """Test the attendance sync functionality"""
    
    print("\n" + "="*60)
    print("Testing Attendance Sync API")
    print("="*60)
    
    # Test 1: Get a few Employee Checkin records
    print("\n1. Fetching Employee Checkin records...")
    checkins = frappe.get_all(
        "Employee Checkin",
        fields=["name", "employee", "time", "log_type"],
        limit=5,
        order_by="time desc"
    )
    
    if not checkins:
        print("   ⚠️  No Employee Checkin records found")
        return
    
    print(f"   ✅ Found {len(checkins)} Employee Checkin records")
    for checkin in checkins[:3]:
        print(f"      - {checkin.name}: {checkin.employee} at {checkin.time}")
    
    # Test 2: Test sync API method
    print("\n2. Testing sync API method...")
    try:
        from phr.phr.api.attendance_sync import sync_employee_checkins
        
        # Test with first checkin
        test_names = [checkins[0].name]
        
        print(f"   Testing sync for checkin: {test_names[0]}")
        result = sync_employee_checkins(checkin_names=test_names)
        
        if result.get("success"):
            print(f"   ✅ Sync API call successful")
            print(f"      - Synced: {result.get('synced', 0)}")
            print(f"      - Failed: {result.get('failed', 0)}")
            print(f"      - Message: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ Sync API call failed")
            print(f"      - Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error testing sync: {str(e)}")
        frappe.log_error(f"Test sync error: {str(e)}", "Attendance Sync Test")
    
    # Test 3: Test Attendance sync
    print("\n3. Fetching Attendance records...")
    attendances = frappe.get_all(
        "Attendance",
        fields=["name", "employee", "attendance_date", "status"],
        limit=5,
        order_by="attendance_date desc"
    )
    
    if attendances:
        print(f"   ✅ Found {len(attendances)} Attendance records")
        for att in attendances[:3]:
            print(f"      - {att.name}: {att.employee} on {att.attendance_date}")
    else:
        print("   ⚠️  No Attendance records found")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60 + "\n")


def test_remote_connection():
    """Test connection to remote server"""
    
    print("\n" + "="*60)
    print("Testing Remote Server Connection")
    print("="*60)
    
    try:
        from phr.phr.api.attendance_sync import send_to_remote_server, REMOTE_SERVER_URL
        
        print(f"\nRemote Server: {REMOTE_SERVER_URL}")
        print("Testing connection...")
        
        # Test with minimal data
        test_data = {
            "employee": "TEST001",
            "time": str(now_datetime()),
            "log_type": "IN",
            "device_id": "TEST-DEVICE"
        }
        
        result = send_to_remote_server(
            doctype="Employee Checkin",
            data=test_data,
            method="add_log_based_on_employee_field"
        )
        
        if result.get("success"):
            print("   ✅ Connection successful!")
            print(f"   Remote ID: {result.get('name', 'N/A')}")
        else:
            print("   ⚠️  Connection test failed (may be expected if employee doesn't exist)")
            print(f"   Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        frappe.log_error(f"Remote connection test error: {str(e)}", "Attendance Sync Test")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # This can be run via: bench --site [site] console
    # Then: exec(open('apps/phr/test_attendance_sync.py').read())
    # Or: bench --site [site] execute phr.test_attendance_sync.test_sync
    pass


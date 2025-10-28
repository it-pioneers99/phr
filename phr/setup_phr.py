#!/usr/bin/env python3
"""
PHR System Setup Script
This script initializes the PHR system with all required components
"""

import frappe
from frappe.utils import getdate, today

def setup_phr_system():
    """
    Setup PHR system with all required components
    """
    try:
        print("Setting up PHR system...")
        
        # Create salary components
        from phr.phr.phr.utils.salary_components import create_salary_components
        salary_result = create_salary_components()
        print(f"Salary components: {salary_result}")
        
        # Create default leave types
        leave_types = [
            {
                "name": "Annual Leave",
                "is_annual": True,
                "is_sick": False,
                "max_leaves": 30
            },
            {
                "name": "Sick Leave", 
                "is_annual": False,
                "is_sick": True,
                "max_leaves": 365
            },
            {
                "name": "Female Leave",
                "is_annual": False,
                "is_sick": False,
                "is_female": True,
                "max_leaves": 7
            },
            {
                "name": "Muslim Leave",
                "is_annual": False,
                "is_sick": False,
                "is_muslim": True,
                "max_leaves": 7
            }
        ]
        
        created_types = []
        for lt in leave_types:
            if not frappe.db.exists("Leave Type", lt["name"]):
                leave_type = frappe.get_doc({
                    "doctype": "Leave Type",
                    "leave_type_name": lt["name"],
                    "max_leaves_allowed": lt["max_leaves"],
                    "is_annual_leave": 1 if lt.get("is_annual") else 0,
                    "is_sick_leave": 1 if lt.get("is_sick") else 0,
                    "is_female": 1 if lt.get("is_female") else 0,
                    "is_muslim": 1 if lt.get("is_muslim") else 0,
                    "is_paid_leave": 1,
                    "include_holiday": 0,
                    "is_compensatory": 0
                })
                leave_type.insert()
                created_types.append(lt["name"])
                print(f"Created leave type: {lt['name']}")
            else:
                print(f"Leave type already exists: {lt['name']}")
        
        frappe.db.commit()
        
        print("PHR system setup completed successfully!")
        print(f"Created leave types: {created_types}")
        
        return {
            "status": "success",
            "message": "PHR system setup completed successfully",
            "salary_components": salary_result,
            "leave_types_created": created_types
        }
        
    except Exception as e:
        print(f"Error setting up PHR system: {str(e)}")
        frappe.log_error(f"Error in PHR setup: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # This script can be run from the bench console
    setup_phr_system()

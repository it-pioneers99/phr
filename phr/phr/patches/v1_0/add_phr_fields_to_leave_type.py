import frappe

def execute():
    """Add PHR custom fields to Leave Type doctype"""
    
    # Add is_annual_leave field
    if not frappe.db.has_column("Leave Type", "is_annual_leave"):
        frappe.db.sql("ALTER TABLE `tabLeave Type` ADD COLUMN `is_annual_leave` INT DEFAULT 0")
    
    # Add is_sick_leave field
    if not frappe.db.has_column("Leave Type", "is_sick_leave"):
        frappe.db.sql("ALTER TABLE `tabLeave Type` ADD COLUMN `is_sick_leave` INT DEFAULT 0")
    
    # Add is_female field for gender restrictions
    if not frappe.db.has_column("Leave Type", "is_female"):
        frappe.db.sql("ALTER TABLE `tabLeave Type` ADD COLUMN `is_female` INT DEFAULT 0")
    
    # Add is_muslim field for religious restrictions
    if not frappe.db.has_column("Leave Type", "is_muslim"):
        frappe.db.sql("ALTER TABLE `tabLeave Type` ADD COLUMN `is_muslim` INT DEFAULT 0")
    
    frappe.db.commit()
    print("PHR fields added to Leave Type doctype successfully")

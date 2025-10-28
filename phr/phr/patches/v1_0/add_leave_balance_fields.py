import frappe

def execute():
    """Add leave balance fields to Employee doctype"""
    
    # Add annual_leave_balance field
    if not frappe.db.has_column("Employee", "annual_leave_balance"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `annual_leave_balance` FLOAT DEFAULT 0")
    
    # Add annual_leave_used field
    if not frappe.db.has_column("Employee", "annual_leave_used"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `annual_leave_used` FLOAT DEFAULT 0")
    
    # Add annual_leave_remaining field
    if not frappe.db.has_column("Employee", "annual_leave_remaining"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `annual_leave_remaining` FLOAT DEFAULT 0")
    
    # Add sick_leave_balance field
    if not frappe.db.has_column("Employee", "sick_leave_balance"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `sick_leave_balance` FLOAT DEFAULT 0")
    
    # Add sick_leave_used field
    if not frappe.db.has_column("Employee", "sick_leave_used"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `sick_leave_used` FLOAT DEFAULT 0")
    
    # Add sick_leave_remaining field
    if not frappe.db.has_column("Employee", "sick_leave_remaining"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `sick_leave_remaining` FLOAT DEFAULT 0")
    
    # Add total_leave_balance field
    if not frappe.db.has_column("Employee", "total_leave_balance"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `total_leave_balance` FLOAT DEFAULT 0")
    
    # Add last_leave_calculation_date field
    if not frappe.db.has_column("Employee", "last_leave_calculation_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `last_leave_calculation_date` DATE")
    
    frappe.db.commit()
    print("Leave balance fields added to Employee doctype successfully")

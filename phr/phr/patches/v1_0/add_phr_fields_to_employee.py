import frappe

def execute():
    """Add PHR custom fields to Employee doctype"""
    
    # Add contract_end_date field
    if not frappe.db.has_column("Employee", "contract_end_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `contract_end_date` DATE")
    
    # Add testing_period_end_date field
    if not frappe.db.has_column("Employee", "testing_period_end_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `testing_period_end_date` DATE")
    
    # Add remaining_testing_days field
    if not frappe.db.has_column("Employee", "remaining_testing_days"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `remaining_testing_days` INT DEFAULT 0")
    
    # Add is_muslim field
    if not frappe.db.has_column("Employee", "is_muslim"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `is_muslim` INT DEFAULT 0")
    
    # Add is_female field
    if not frappe.db.has_column("Employee", "is_female"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `is_female` INT DEFAULT 0")
    
    # Add annual leave balance fields
    if not frappe.db.has_column("Employee", "annual_leave_balance"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `annual_leave_balance` DECIMAL(10,2) DEFAULT 0")
    
    if not frappe.db.has_column("Employee", "annual_leave_used"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `annual_leave_used` DECIMAL(10,2) DEFAULT 0")
    
    if not frappe.db.has_column("Employee", "annual_leave_remaining"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `annual_leave_remaining` DECIMAL(10,2) DEFAULT 0")
    
    # Add sick leave balance fields
    if not frappe.db.has_column("Employee", "sick_leave_balance"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `sick_leave_balance` DECIMAL(10,2) DEFAULT 0")
    
    if not frappe.db.has_column("Employee", "sick_leave_used"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `sick_leave_used` DECIMAL(10,2) DEFAULT 0")
    
    if not frappe.db.has_column("Employee", "sick_leave_remaining"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `sick_leave_remaining` DECIMAL(10,2) DEFAULT 0")
    
    frappe.db.commit()
    print("PHR fields added to Employee doctype successfully")

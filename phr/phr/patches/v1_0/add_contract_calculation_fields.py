import frappe

def execute():
    """Add contract calculation fields to Employee doctype"""
    
    # Add testing_period_end_date field (calculated from joining date + 180 days)
    if not frappe.db.has_column("Employee", "testing_period_end_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `testing_period_end_date` DATE")
    
    # Add contract_end_date field (calculated from joining date + 180 days)
    if not frappe.db.has_column("Employee", "contract_end_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `contract_end_date` DATE")
    
    # Add contract_start_date field (same as joining date)
    if not frappe.db.has_column("Employee", "contract_start_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `contract_start_date` DATE")
    
    # Add contract_duration_days field (calculated: 180 days)
    if not frappe.db.has_column("Employee", "contract_duration_days"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `contract_duration_days` INT DEFAULT 180")
    
    # Add remaining_contract_days field (calculated)
    if not frappe.db.has_column("Employee", "remaining_contract_days"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `remaining_contract_days` INT DEFAULT 0")
    
    # Add contract_status field
    if not frappe.db.has_column("Employee", "contract_status"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `contract_status` VARCHAR(50) DEFAULT 'Active'")
    
    # Add notification_sent_90_days field
    if not frappe.db.has_column("Employee", "notification_sent_90_days"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `notification_sent_90_days` INT DEFAULT 0")
    
    # Add notification_sent_30_days field
    if not frappe.db.has_column("Employee", "notification_sent_30_days"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `notification_sent_30_days` INT DEFAULT 0")
    
    # Add last_notification_date field
    if not frappe.db.has_column("Employee", "last_notification_date"):
        frappe.db.sql("ALTER TABLE `tabEmployee` ADD COLUMN `last_notification_date` DATE")
    
    frappe.db.commit()
    print("Contract calculation fields added to Employee doctype successfully")

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta

class ShiftPermissionRequest(Document):
    def validate(self):
        self.validate_permission_limits()
        self.validate_umrah_permissions()
    
    def validate_permission_limits(self):
        """Validate permission limits (1-4 hours per month)"""
        if not self.hours_requested:
            return
        
        # Minimum 1 hour, maximum 4 hours
        if self.hours_requested < 1:
            frappe.throw(_("Permission duration must be at least 1 hour"))
        
        if self.hours_requested > 4:
            frappe.throw(_("Permission duration cannot exceed 4 hours per month"))
        
        # Check monthly limit
        month_start = self.permission_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_permissions = frappe.db.sql("""
            SELECT SUM(hours_requested)
            FROM `tabShift Permission Request`
            WHERE employee = %s
            AND permission_date BETWEEN %s AND %s
            AND status = 'Approved'
            AND docstatus = 1
        """, (self.employee, month_start, month_end), as_list=True)
        
        total_monthly = (monthly_permissions[0][0] or 0) + self.hours_requested
        if total_monthly > 4:
            frappe.throw(_("Total monthly permissions cannot exceed 4 hours"))
    
    def validate_umrah_permissions(self):
        """Validate Umrah permission limits (half day every 3 months, max 4 times per year)"""
        if not self.permission_type or self.permission_type != "Out of Office":
            return
        
        # Check if this is an Umrah request (you might need to add a field to identify Umrah requests)
        # For now, we'll assume any "Out of Office" request for 4 hours is Umrah
        
        if self.hours_requested == 4:  # Half day
            # Check if employee had Umrah permission in last 3 months
            three_months_ago = self.permission_date - timedelta(days=90)
            
            recent_umrah = frappe.db.sql("""
                SELECT COUNT(*)
                FROM `tabShift Permission Request`
                WHERE employee = %s
                AND permission_date >= %s
                AND permission_date < %s
                AND permission_type = 'Out of Office'
                AND hours_requested = 4
                AND status = 'Approved'
                AND docstatus = 1
            """, (self.employee, three_months_ago, self.permission_date), as_list=True)
            
            if recent_umrah[0][0] > 0:
                frappe.throw(_("Umrah permission can only be taken once every 3 months"))
            
            # Check yearly limit (4 times per year)
            year_start = self.permission_date.replace(month=1, day=1)
            year_end = self.permission_date.replace(month=12, day=31)
            
            yearly_umrah = frappe.db.sql("""
                SELECT COUNT(*)
                FROM `tabShift Permission Request`
                WHERE employee = %s
                AND permission_date BETWEEN %s AND %s
                AND permission_type = 'Out of Office'
                AND hours_requested = 4
                AND status = 'Approved'
                AND docstatus = 1
            """, (self.employee, year_start, year_end), as_list=True)
            
            if yearly_umrah[0][0] >= 4:
                frappe.throw(_("Maximum 4 Umrah permissions allowed per year"))
    
    def on_submit(self):
        """Handle permission request submission"""
        if self.status == "Approved":
            self.approval_date = frappe.utils.now()
            self.approved_by = frappe.session.user
            self.save()
            
            # Check if permission should be deducted from leave balance
            self.handle_leave_deduction()
    
    def handle_leave_deduction(self):
        """Handle deduction from leave balance or salary"""
        if not self.hours_requested:
            return
        
        # Check if employee has available leave balance
        # This would need integration with HRMS leave management
        # For now, we'll just create a note
        
        if self.hours_requested >= 4:  # Half day or more
            frappe.msgprint(_("Please check if this permission should be deducted from annual leave balance"))
        
        # If no leave balance available, this would be deducted from salary
        # This would be handled in salary slip calculation

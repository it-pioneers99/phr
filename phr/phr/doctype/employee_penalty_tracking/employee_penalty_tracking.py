# Copyright (c) 2025, Pioneer Holding and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import today, getdate


class EmployeePenaltyTracking(Document):
    def validate(self):
        """Validate and auto-calculate tracking month/year based on current date"""
        if not self.tracking_month or not self.tracking_year:
            self.set_tracking_period()
    
    def set_tracking_period(self):
        """Set tracking month and year based on day 20 to day 19 rule"""
        today_date = getdate(today())
        current_day = today_date.day
        current_month = today_date.month
        current_year = today_date.year
        
        # If current day is 20 or later, use current month/year
        # If current day is before 20, use previous month/year
        if current_day >= 20:
            self.tracking_month = current_month
            self.tracking_year = current_year
        else:
            # Previous month
            if current_month == 1:
                self.tracking_month = 12
                self.tracking_year = current_year - 1
            else:
                self.tracking_month = current_month - 1
                self.tracking_year = current_year
    
    def get_tracking_period_start(self):
        """Get the start date of the current tracking period (day 20)"""
        if self.tracking_month == 12:
            next_year = self.tracking_year + 1
            next_month = 1
        else:
            next_year = self.tracking_year
            next_month = self.tracking_month + 1
        
        # Start date is day 20 of tracking month
        start_date = datetime(self.tracking_year, self.tracking_month, 20).date()
        return start_date
    
    def get_tracking_period_end(self):
        """Get the end date of the current tracking period (day 19 of next month)"""
        if self.tracking_month == 12:
            next_year = self.tracking_year + 1
            next_month = 1
        else:
            next_year = self.tracking_year
            next_month = self.tracking_month + 1
        
        # End date is day 19 of next month
        end_date = datetime(next_year, next_month, 19).date()
        return end_date
    
    def increment_occurrence(self, penalty_date=None):
        """Increment the occurrence count for this penalty type"""
        if penalty_date is None:
            penalty_date = today()
        
        self.occurrence_count += 1
        self.last_penalty_date = penalty_date
        self.save()
    
    def get_current_penalty_level(self):
        """Get the current penalty level based on occurrence count"""
        penalty_type_doc = frappe.get_doc("Penalty Type", self.penalty_type)
        
        for level in penalty_type_doc.penalty_levels:
            if level.occurrence_number == self.occurrence_count:
                return level
        
        # If occurrence count exceeds available levels, return the highest level
        if penalty_type_doc.penalty_levels:
            return penalty_type_doc.penalty_levels[-1]
        
        return None
    
    def should_reset_tracking(self):
        """Check if tracking should be reset for new month"""
        today_date = getdate(today())
        current_day = today_date.day
        current_month = today_date.month
        current_year = today_date.year
        
        # If it's day 20 or later and we're in a new month/year
        if current_day >= 20:
            if (current_month != self.tracking_month or 
                current_year != self.tracking_year):
                return True
        else:
            # If it's before day 20, check if we need to reset for previous month
            if self.tracking_month == 12:
                expected_month = 1
                expected_year = current_year
            else:
                expected_month = current_month + 1
                expected_year = current_year
            
            if (expected_month != self.tracking_month or 
                expected_year != self.tracking_year):
                return True
        
        return False
    
    def reset_for_new_period(self):
        """Reset occurrence count for new tracking period"""
        self.occurrence_count = 0
        self.last_penalty_date = None
        self.set_tracking_period()
        self.save()


@frappe.whitelist()
def get_or_create_tracking(employee, penalty_type):
    """Get or create penalty tracking for employee and penalty type"""
    # Check if tracking exists for current period
    tracking_doc = frappe.db.get_value(
        "Employee Penalty Tracking",
        {
            "employee": employee,
            "penalty_type": penalty_type
        },
        "name"
    )
    
    if tracking_doc:
        tracking_doc = frappe.get_doc("Employee Penalty Tracking", tracking_doc)
        
        # Check if we need to reset for new period
        if tracking_doc.should_reset_tracking():
            tracking_doc.reset_for_new_period()
        
        return tracking_doc
    else:
        # Create new tracking record
        tracking_doc = frappe.new_doc("Employee Penalty Tracking")
        tracking_doc.employee = employee
        tracking_doc.penalty_type = penalty_type
        tracking_doc.occurrence_count = 0
        tracking_doc.insert()
        return tracking_doc


@frappe.whitelist()
def process_attendance_penalty(employee, checkin_time, log_type, shift_type):
    """Process attendance penalty based on checkin time and log type"""
    from datetime import datetime, time
    
    # Get shift details
    shift_doc = frappe.get_doc("Shift Type", shift_type)
    shift_start = shift_doc.start_time
    shift_end = shift_doc.end_time
    
    # Parse checkin time
    if isinstance(checkin_time, str):
        checkin_datetime = datetime.fromisoformat(checkin_time.replace('Z', '+00:00'))
    else:
        checkin_datetime = checkin_time
    
    checkin_time_only = checkin_datetime.time()
    
    penalty_type = None
    penalty_reason = ""
    
    if log_type == "IN":
        # Check for late arrival
        if checkin_time_only > shift_start:
            late_minutes = (datetime.combine(checkin_datetime.date(), checkin_time_only) - 
                          datetime.combine(checkin_datetime.date(), shift_start)).total_seconds() / 60
            
            if 15 <= late_minutes < 30:
                penalty_type = "Late Arrival 15-30 Minutes"
                penalty_reason = f"Late arrival by {int(late_minutes)} minutes"
            elif 30 <= late_minutes < 45:
                penalty_type = "Late Arrival 30-45 Minutes"
                penalty_reason = f"Late arrival by {int(late_minutes)} minutes"
            elif 45 <= late_minutes < 75:
                penalty_type = "Late Arrival 45-75 Minutes"
                penalty_reason = f"Late arrival by {int(late_minutes)} minutes"
            elif late_minutes >= 75:
                penalty_type = "Late Arrival above 75 Minutes"
                penalty_reason = f"Late arrival by {int(late_minutes)} minutes"
    
    elif log_type == "OUT":
        # Check for early departure
        if checkin_time_only < shift_end:
            early_minutes = (datetime.combine(checkin_datetime.date(), shift_end) - 
                           datetime.combine(checkin_datetime.date(), checkin_time_only)).total_seconds() / 60
            
            if early_minutes > 15:
                penalty_type = "Early Left above 15 Minutes"
                penalty_reason = f"Early departure by {int(early_minutes)} minutes"
    
    if penalty_type:
        # Get or create tracking record
        tracking_doc = get_or_create_tracking(employee, penalty_type)
        
        # Increment occurrence
        tracking_doc.increment_occurrence(checkin_datetime.date())
        
        # Get current penalty level
        penalty_level = tracking_doc.get_current_penalty_level()
        
        if penalty_level:
            # Create penalty record
            penalty_record = frappe.new_doc("Penalty Record")
            penalty_record.employee = employee
            penalty_record.penalty_type = penalty_type
            penalty_record.penalty_date = checkin_datetime.date()
            penalty_record.penalty_reason = penalty_reason
            penalty_record.penalty_level = penalty_level.level
            penalty_record.penalty_percentage = penalty_level.penalty_percentage
            penalty_record.occurrence_number = tracking_doc.occurrence_count
            penalty_record.insert()
            penalty_record.submit()
            
            return {
                "penalty_created": True,
                "penalty_type": penalty_type,
                "penalty_reason": penalty_reason,
                "penalty_level": penalty_level.level,
                "penalty_percentage": penalty_level.penalty_percentage,
                "occurrence_count": tracking_doc.occurrence_count
            }
    
    return {"penalty_created": False}

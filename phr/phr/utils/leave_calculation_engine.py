import frappe
from frappe.utils import getdate, date_diff, add_days, today, add_months
from frappe import _

class LeaveCalculationEngine:
    """
    Enhanced leave calculation engine for PHR system
    Now depends on leave type, leave allocation, and leave period
    """
    
    def __init__(self, employee_id):
        self.employee_id = employee_id
        self.employee = frappe.get_doc("Employee", employee_id)
        self.working_years = self.calculate_working_years()
        self.working_months = self.calculate_working_months()
    
    def calculate_working_years(self):
        """Calculate years of service from joining date"""
        if not self.employee.date_of_joining:
            return 0
        
        joining_date = getdate(self.employee.date_of_joining)
        current_date = getdate()
        years = date_diff(current_date, joining_date) / 365.25
        return round(years, 2)
    
    def calculate_working_months(self):
        """Calculate months of service from joining date"""
        if not self.employee.date_of_joining:
            return 0
        
        joining_date = getdate(self.employee.date_of_joining)
        current_date = getdate()
        months = (current_date.year - joining_date.year) * 12 + (current_date.month - joining_date.month)
        return months
    
    def is_eligible_for_30_days_annual_leave(self):
        """Check if employee is eligible for 30 days annual leave (5+ years or 60+ months)"""
        return self.working_months >= 60 or self.working_years >= 5
    
    def get_annual_leave_days(self):
        """Get annual leave days based on years of service and additional annual leave flag"""
        # Check if employee has additional annual leave flag
        is_additional_annual_leave = frappe.db.get_value("Employee", self.employee_id, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            # If additional annual leave is checked, always give 30 days
            return 30
        elif self.is_eligible_for_30_days_annual_leave():
            # 30 days for 60+ months (5+ years) without additional flag
            return 30
        else:
            # 21 days for less than 60 months (less than 5 years)
            return 21
    
    def get_annual_leave_days_per_month(self):
        """Get annual leave days per month based on years of service and additional annual leave flag"""
        # Check if employee has additional annual leave flag
        is_additional_annual_leave = frappe.db.get_value("Employee", self.employee_id, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            # If additional annual leave is checked, always give 2.5 days per month
            return 2.5
        elif self.is_eligible_for_30_days_annual_leave():
            # 2.5 days per month for 60+ months (5+ years) without additional flag
            return 2.5
        else:
            # 1.75 days per month for less than 60 months (less than 5 years)
            return 1.75

    def get_sick_leave_daily_rate(self):
        """Get daily sick leave accumulation rate based on service period and additional annual leave flag"""
        # Check if employee has additional annual leave flag
        is_additional_annual_leave = frappe.db.get_value("Employee", self.employee_id, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave or self.is_eligible_for_30_days_annual_leave():
            return 0.0821917808  # 30 days / 365 days
        else:
            return 0.0575342466  # 21 days / 365 days
    
    def get_leave_analysis_by_type_and_period(self, leave_type=None, start_date=None, end_date=None):
        """
        Enhanced leave analysis that depends on leave type, allocation, and period
        """
        try:
            analysis = {
                "employee_info": {
                    "name": self.employee.name,
                    "employee_name": self.employee.employee_name,
                    "date_of_joining": self.employee.date_of_joining,
                    "working_years": self.working_years,
                    "working_months": self.working_months,
                    "is_eligible_30_days": self.is_eligible_for_30_days_annual_leave()
                },
                "leave_types": {},
                "allocations": {},
                "applications": {},
                "period_analysis": {}
            }
            
            # Get all leave types
            leave_types = frappe.get_all("Leave Type", 
                filters={},
                fields=["name", "is_annual_leave", "is_sick_leave", "is_female", "is_muslim", "max_leaves_allowed"]
            )
            
            for lt in leave_types:
                analysis["leave_types"][lt.name] = {
                    "is_annual_leave": lt.is_annual_leave,
                    "is_sick_leave": lt.is_sick_leave,
                    "is_female": lt.is_female,
                    "is_muslim": lt.is_muslim,
                    "max_leaves_allowed": lt.max_leaves_allowed
                }
            
            # Get leave allocations for the period
            allocation_filters = {
                "employee": self.employee_id,
                "docstatus": 1
            }
            
            if start_date and end_date:
                allocation_filters.update({
                    "from_date": ["<=", end_date],
                    "to_date": [">=", start_date]
                })
            
            allocations = frappe.get_all("Leave Allocation",
                filters=allocation_filters,
                fields=["name", "leave_type", "from_date", "to_date", "total_leaves_allocated", "unused_leaves", "new_leaves_allocated"]
            )
            
            for alloc in allocations:
                analysis["allocations"][alloc.name] = {
                    "leave_type": alloc.leave_type,
                    "from_date": alloc.from_date,
                    "to_date": alloc.to_date,
                    "total_leaves_allocated": alloc.total_leaves_allocated,
                    "unused_leaves": alloc.unused_leaves,
                    "new_leaves_allocated": alloc.new_leaves_allocated,
                    "used_leaves": alloc.total_leaves_allocated - alloc.unused_leaves
                }
            
            # Get leave applications for the period
            application_filters = {
                "employee": self.employee_id,
                "docstatus": 1
            }
            
            if start_date and end_date:
                application_filters.update({
                    "from_date": ["<=", end_date],
                    "to_date": [">=", start_date]
                })
            
            applications = frappe.get_all("Leave Application",
                filters=application_filters,
                fields=["name", "leave_type", "from_date", "to_date", "total_leave_days", "status", "half_day", "half_day_date"]
            )
            
            for app in applications:
                analysis["applications"][app.name] = {
                    "leave_type": app.leave_type,
                    "from_date": app.from_date,
                    "to_date": app.to_date,
                    "total_leave_days": app.total_leave_days,
                    "status": app.status,
                    "half_day": app.half_day,
                    "half_day_date": app.half_day_date
                }
            
            # Calculate period-specific analysis
            if start_date and end_date:
                analysis["period_analysis"] = self.calculate_period_analysis(start_date, end_date, leave_type)
            
            # Calculate leave balances by type
            analysis["leave_balances"] = self.calculate_leave_balances_by_type(leave_type)
            
            return analysis
            
        except Exception as e:
            frappe.log_error(f"Error in leave analysis: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def calculate_period_analysis(self, start_date, end_date, leave_type=None):
        """Calculate detailed analysis for a specific period"""
        try:
            period_analysis = {
                "period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_days": date_diff(end_date, start_date) + 1
                },
                "leave_type_breakdown": {},
                "allocation_summary": {},
                "application_summary": {},
                "balance_changes": {}
            }
            
            # Filter allocations for the period
            period_allocations = frappe.get_all("Leave Allocation",
                filters={
                    "employee": self.employee_id,
                    "from_date": ["<=", end_date],
                    "to_date": [">=", start_date],
                    "docstatus": 1
                },
                fields=["leave_type", "total_leaves_allocated", "unused_leaves", "new_leaves_allocated"]
            )
            
            # Filter applications for the period
            period_applications = frappe.get_all("Leave Application",
                filters={
                    "employee": self.employee_id,
                    "from_date": ["<=", end_date],
                    "to_date": [">=", start_date],
                    "docstatus": 1
                },
                fields=["leave_type", "total_leave_days", "status"]
            )
            
            # Group by leave type
            for alloc in period_allocations:
                lt = alloc.leave_type
                if lt not in period_analysis["leave_type_breakdown"]:
                    period_analysis["leave_type_breakdown"][lt] = {
                        "allocated": 0,
                        "used": 0,
                        "remaining": 0,
                        "applications_count": 0,
                        "total_days_applied": 0
                    }
                
                period_analysis["leave_type_breakdown"][lt]["allocated"] += alloc.total_leaves_allocated
                period_analysis["leave_type_breakdown"][lt]["remaining"] += alloc.unused_leaves
                period_analysis["leave_type_breakdown"][lt]["used"] += (alloc.total_leaves_allocated - alloc.unused_leaves)
            
            for app in period_applications:
                lt = app.leave_type
                if lt not in period_analysis["leave_type_breakdown"]:
                    period_analysis["leave_type_breakdown"][lt] = {
                        "allocated": 0,
                        "used": 0,
                        "remaining": 0,
                        "applications_count": 0,
                        "total_days_applied": 0
                    }
                
                period_analysis["leave_type_breakdown"][lt]["applications_count"] += 1
                period_analysis["leave_type_breakdown"][lt]["total_days_applied"] += app.total_leave_days
            
            return period_analysis
            
        except Exception as e:
            frappe.log_error(f"Error calculating period analysis: {str(e)}")
            return {}
    
    def calculate_leave_balances_by_type(self, leave_type=None):
        """Calculate leave balances grouped by leave type"""
        try:
            balances = {}
            
            # Get all leave types
            leave_types = frappe.get_all("Leave Type", 
                filters={} if not leave_type else {"name": leave_type},
                fields=["name", "is_annual_leave", "is_sick_leave"]
            )
            
            for lt in leave_types:
                lt_name = lt.name
                
                # Get current allocations
                allocations = frappe.get_all("Leave Allocation",
                    filters={
                        "employee": self.employee_id,
                        "leave_type": lt_name,
                        "docstatus": 1
                    },
                    fields=["total_leaves_allocated", "new_leaves_allocated", "unused_leaves", "from_date", "to_date"]
                )
                
                # Use new_leaves_allocated if available, otherwise total_leaves_allocated
                total_allocated = sum([alloc.new_leaves_allocated or alloc.total_leaves_allocated for alloc in allocations])
                total_remaining = sum([alloc.unused_leaves for alloc in allocations])
                total_used = total_allocated - total_remaining
                
                # If no allocations exist or allocation is too small, calculate theoretical allocation
                if lt.is_annual_leave:
                    theoretical_allocation = self.get_annual_leave_days()
                    # If no allocation or allocation is significantly less than theoretical, use theoretical
                    if total_allocated == 0 or total_allocated < theoretical_allocation * 0.5:
                        total_allocated = theoretical_allocation
                        total_remaining = theoretical_allocation - total_used
                
                # For sick leave, calculate daily accumulation
                daily_rate = 0
                accumulated_this_year = 0
                
                if lt.is_sick_leave:
                    daily_rate = self.get_sick_leave_daily_rate()
                    accumulated_this_year = self.calculate_sick_leave_accumulation()
                    total_remaining += accumulated_this_year
                
                balances[lt_name] = {
                    "allocated": total_allocated,
                    "used": total_used,
                    "remaining": total_remaining,
                    "is_annual_leave": lt.is_annual_leave,
                    "is_sick_leave": lt.is_sick_leave,
                    "daily_rate": daily_rate,
                    "accumulated_this_year": accumulated_this_year
                }
            
            return balances
            
        except Exception as e:
            frappe.log_error(f"Error calculating leave balances by type: {str(e)}")
            return {}
    
    def calculate_sick_leave_accumulation(self):
        """Calculate sick leave accumulated this year"""
        try:
            current_year = getdate().year
            year_start = getdate(f"{current_year}-01-01")
            year_end = getdate(f"{current_year}-12-31")
            
            # If employee joined this year, calculate from joining date
            if self.employee.date_of_joining and getdate(self.employee.date_of_joining).year == current_year:
                start_date = getdate(self.employee.date_of_joining)
            else:
                start_date = year_start
            
            # Calculate working days (excluding weekends)
            working_days = 0
            current_date = start_date
            
            while current_date <= year_end:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    working_days += 1
                current_date = add_days(current_date, 1)
            
            daily_rate = self.get_sick_leave_daily_rate()
            return working_days * daily_rate
            
        except Exception as e:
            frappe.log_error(f"Error calculating sick leave accumulation: {str(e)}")
            return 0
    
    def create_automatic_allocations(self):
        """Create automatic leave allocations based on 60-month threshold"""
        try:
            current_year = getdate().year
            allocations_created = []
            
            # Determine annual leave days based on 60-month threshold
            annual_days = self.get_annual_leave_days()
            eligibility_status = "30 days" if self.is_eligible_for_30_days_annual_leave() else "21 days"
            
            frappe.msgprint(f"Employee has {self.working_months} months of service. Eligible for {eligibility_status} annual leave.")
            
            # Annual Leave Allocation
            annual_leave_type = self.get_or_create_leave_type("Annual Leave", is_annual=True)
            
            annual_allocation = self.create_leave_allocation(
                annual_leave_type, 
                annual_days, 
                current_year,
                f"Automatic allocation based on {self.working_months} months of service"
            )
            if annual_allocation:
                allocations_created.append(annual_allocation)
            
            # Sick Leave Allocation (unlimited but tracked)
            sick_leave_type = self.get_or_create_leave_type("Sick Leave", is_sick=True)
            
            sick_allocation = self.create_leave_allocation(
                sick_leave_type, 
                365,  # Maximum allowed
                current_year,
                f"Sick leave allocation with daily rate: {self.get_sick_leave_daily_rate():.6f}"
            )
            if sick_allocation:
                allocations_created.append(sick_allocation)
            
            return allocations_created
            
        except Exception as e:
            frappe.log_error(f"Error creating automatic allocations: {str(e)}")
            return []
    
    def get_or_create_leave_type(self, leave_type_name, is_annual=False, is_sick=False):
        """Get existing leave type or create new one"""
        try:
            if frappe.db.exists("Leave Type", leave_type_name):
                return leave_type_name
            
            # Create new leave type
            leave_type = frappe.get_doc({
                "doctype": "Leave Type",
                "leave_type_name": leave_type_name,
                "max_leaves_allowed": 365 if is_sick else 30,
                "is_annual_leave": 1 if is_annual else 0,
                "is_sick_leave": 1 if is_sick else 0,
                "is_paid_leave": 1,
                "include_holiday": 0,
                "is_compensatory": 0
            })
            leave_type.insert()
            frappe.db.commit()
            
            return leave_type.name
            
        except Exception as e:
            frappe.log_error(f"Error creating leave type: {str(e)}")
            return leave_type_name
    
    def create_leave_allocation(self, leave_type, days, year, description=""):
        """Create leave allocation record with description"""
        try:
            # Check if allocation already exists
            existing = frappe.db.exists("Leave Allocation", {
                "employee": self.employee_id,
                "leave_type": leave_type,
                "from_date": f"{year}-01-01",
                "to_date": f"{year}-12-31"
            })
            
            if existing:
                # Update existing allocation
                allocation_doc = frappe.get_doc("Leave Allocation", existing)
                allocation_doc.new_leaves_allocated = days
                if description:
                    allocation_doc.description = description
                allocation_doc.save()
                return allocation_doc.name
            else:
                # Create new allocation
                allocation_doc = frappe.get_doc({
                    "doctype": "Leave Allocation",
                    "employee": self.employee_id,
                    "leave_type": leave_type,
                    "from_date": f"{year}-01-01",
                    "to_date": f"{year}-12-31",
                    "new_leaves_allocated": days,
                    "carry_forward": 0,
                    "description": description
                })
                allocation_doc.insert()
                allocation_doc.submit()
                frappe.db.commit()
                return allocation_doc.name
                
        except Exception as e:
            frappe.log_error(f"Error creating leave allocation: {str(e)}")
            return None
    
    def update_employee_leave_balances(self):
        """Update employee leave balance fields"""
        try:
            # Calculate balances by type
            balances = self.calculate_leave_balances_by_type()
            
            # Update annual leave balances
            annual_leave_balance = balances.get("Annual Leave", {})
            self.employee.annual_leave_balance = annual_leave_balance.get("allocated", 0)
            self.employee.annual_leave_used = annual_leave_balance.get("used", 0)
            self.employee.annual_leave_remaining = annual_leave_balance.get("remaining", 0)
            
            # Update sick leave balances
            sick_leave_balance = balances.get("Sick Leave", {})
            self.employee.sick_leave_balance = sick_leave_balance.get("remaining", 0)
            self.employee.sick_leave_used = sick_leave_balance.get("used", 0)
            self.employee.sick_leave_remaining = sick_leave_balance.get("remaining", 0)
            
            self.employee.save()
            frappe.db.commit()
            
            return {
                "annual_leave": annual_leave_balance,
                "sick_leave": sick_leave_balance,
                "working_months": self.working_months,
                "is_eligible_30_days": self.is_eligible_for_30_days_annual_leave()
            }
            
        except Exception as e:
            frappe.log_error(f"Error updating employee balances: {str(e)}")
            return None

@frappe.whitelist()
def get_enhanced_leave_analysis(employee_id, leave_type=None, start_date=None, end_date=None):
    """Get enhanced leave analysis based on type, allocation, and period"""
    try:
        engine = LeaveCalculationEngine(employee_id)
        return engine.get_leave_analysis_by_type_and_period(leave_type, start_date, end_date)
    except Exception as e:
        frappe.log_error(f"Error getting enhanced leave analysis: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def calculate_employee_leave_balances(employee_id):
    """Calculate and update leave balances for an employee"""
    try:
        engine = LeaveCalculationEngine(employee_id)
        return engine.update_employee_leave_balances()
    except Exception as e:
        frappe.log_error(f"Error calculating leave balances: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_automatic_leave_allocations(employee_id):
    """Create automatic leave allocations for an employee based on 60-month threshold"""
    try:
        engine = LeaveCalculationEngine(employee_id)
        return engine.create_automatic_allocations()
    except Exception as e:
        frappe.log_error(f"Error creating automatic allocations: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def check_employee_eligibility(employee_id):
    """Check employee eligibility for 30 days annual leave"""
    try:
        engine = LeaveCalculationEngine(employee_id)
        return {
            "working_years": engine.working_years,
            "working_months": engine.working_months,
            "is_eligible_30_days": engine.is_eligible_for_30_days_annual_leave(),
            "annual_leave_days": engine.get_annual_leave_days(),
            "sick_leave_daily_rate": engine.get_sick_leave_daily_rate()
        }
    except Exception as e:
        frappe.log_error(f"Error checking employee eligibility: {str(e)}")
        return {"status": "error", "message": str(e)}

def update_employee_leave_balance_fields(employee_id, leave_data):
    """Update Employee form fields with leave balance data"""
    
    try:
        employee = frappe.get_doc('Employee', employee_id)
        
        # Update annual leave fields
        if 'annual_leave' in leave_data:
            annual_data = leave_data['annual_leave']
            employee.annual_leave_balance = annual_data.get('allocated', 0)
            employee.annual_leave_used = annual_data.get('used', 0)
            employee.annual_leave_remaining = annual_data.get('remaining', 0)
        
        # Update sick leave fields
        if 'sick_leave' in leave_data:
            sick_data = leave_data['sick_leave']
            employee.sick_leave_balance = sick_data.get('total_remaining', 0)
            employee.sick_leave_used = sick_data.get('used', 0)
            employee.sick_leave_remaining = sick_data.get('total_remaining', 0)
        
        # Calculate total leave balance
        total_balance = 0
        if 'annual_leave' in leave_data:
            total_balance += leave_data['annual_leave'].get('remaining', 0)
        if 'sick_leave' in leave_data:
            total_balance += leave_data['sick_leave'].get('total_remaining', 0)
        
        employee.total_leave_balance = total_balance
        employee.last_leave_calculation_date = frappe.utils.today()
        
        employee.save()
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': 'Employee leave balance fields updated successfully'
        }
    
    except Exception as e:
        frappe.log_error(f"Error updating employee leave balance fields: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

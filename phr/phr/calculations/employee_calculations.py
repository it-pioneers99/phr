# -*- coding: utf-8 -*-
# Copyright (c) 2025, Pioneers and contributors
# For license information, please see license.txt
"""
Employee Calculations - Consolidated Python Functions
All employee calculation functions consolidated in one file
"""

import frappe
from frappe import _
from frappe.utils import getdate, flt, add_days, add_months, today, nowdate, date_diff
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


# ============================================================================
# END OF SERVICE (EOS) CALCULATIONS
# ============================================================================

@frappe.whitelist()
def calculate_eos_for_employee(employee, end_date=None, termination_reason="Resignation", basic_salary=None):
    """
    Calculate EOS Settlement for an employee without creating a document.
    This is for preview/calculation purposes only.
    
    Args:
        employee: Employee ID
        end_date: End of service date (defaults to today)
        termination_reason: Resignation, Contract Expiry, or Termination by Employer
        basic_salary: Optional manual basic salary override (float)
    
    Returns:
        dict: Calculated settlement details
    """
    if not employee:
        frappe.throw(_("Employee is required"))
    
    emp_doc = frappe.get_doc("Employee", employee)
    
    if not emp_doc.date_of_joining:
        frappe.throw(_("Employee {0} does not have a Date of Joining").format(employee))
    
    if not end_date:
        end_date = getdate()
    else:
        end_date = getdate(end_date)
    
    appointment_date = getdate(emp_doc.date_of_joining)
    
    if basic_salary is not None:
        last_basic_salary = flt(basic_salary)
        salary_source = "manual"
    else:
        last_basic_salary, salary_source = get_employee_basic_salary(employee)
    
    delta = end_date - appointment_date
    years_of_service = round(delta.days / 365.25, 2)
    
    gratuity_amount = calculate_gratuity(
        years_of_service, 
        last_basic_salary, 
        termination_reason
    )
    
    vacation_allowance = calculate_vacation_allowance(
        years_of_service, 
        last_basic_salary,
        employee
    )
    
    loan_data = calculate_loan_details(employee)
    
    total_before_loan = gratuity_amount + vacation_allowance
    loan_deduction = min(loan_data['outstanding_balance'], total_before_loan) if loan_data['outstanding_balance'] > 0 else 0
    net_payable = total_before_loan - loan_deduction
    
    return {
        'employee': employee,
        'employee_name': emp_doc.employee_name,
        'appointment_date': appointment_date,
        'end_of_service_date': end_date,
        'termination_reason': termination_reason,
        'last_basic_salary': last_basic_salary,
        'salary_source': salary_source,
        'years_of_service': years_of_service,
        'eligible_for_gratuity': gratuity_amount > 0,
        'gratuity_amount': gratuity_amount,
        'vacation_allowance': vacation_allowance,
        'has_outstanding_loan': loan_data['has_loan'],
        'outstanding_loan_balance': loan_data['outstanding_balance'],
        'loan_deduction': loan_deduction,
        'total_settlement_before_loan': total_before_loan,
        'net_payable_amount': net_payable,
        'loan_details': loan_data['loans']
    }


def get_employee_basic_salary(employee):
    """
    Get the employee's current basic salary
    
    Returns:
        tuple: (salary_amount, source) where source is 'salary_structure', 'salary_slip', or 'not_found'
    """
    salary_structure_assignment = frappe.db.get_value(
        "Salary Structure Assignment",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fieldname="base",
        order_by="from_date desc"
    )
    
    if salary_structure_assignment:
        return flt(salary_structure_assignment), 'salary_structure'
    
    salary_slip = frappe.db.get_value(
        "Salary Slip",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fieldname="gross_pay",
        order_by="posting_date desc"
    )
    
    if salary_slip:
        return flt(salary_slip), 'salary_slip'
    
    return 0, 'not_found'


def calculate_gratuity(years_of_service, last_basic_salary, termination_reason):
    """Calculate gratuity based on Saudi Labor Law Articles 84/85"""
    if not last_basic_salary or not years_of_service:
        return 0
    
    years = int(years_of_service)
    partial_year = years_of_service - years
    
    if termination_reason == "Termination by Employer":
        gratuity = 0
        first_5_years = min(years, 5)
        gratuity += (first_5_years * last_basic_salary * 0.5)
        
        if years > 5:
            remaining_years = years - 5
            gratuity += (remaining_years * last_basic_salary)
        
        if partial_year > 0:
            if years < 5:
                gratuity += (partial_year * last_basic_salary * 0.5)
            else:
                gratuity += (partial_year * last_basic_salary)
    
    elif termination_reason == "Resignation":
        if years < 2:
            gratuity = 0
        elif years < 5:
            base_gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
            gratuity = base_gratuity * (1/3)
        elif years < 10:
            base_gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
            gratuity = base_gratuity * (2/3)
        else:
            gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
    else:
        gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
    
    return round(gratuity, 2)


def calculate_article_84_gratuity(years_of_service, last_basic_salary):
    """Calculate gratuity according to Article 84"""
    years = int(years_of_service)
    partial_year = years_of_service - years
    
    gratuity = 0
    first_5_years = min(years, 5)
    gratuity += (first_5_years * last_basic_salary * 0.5)
    
    if years > 5:
        remaining_years = years - 5
        gratuity += (remaining_years * last_basic_salary)
    
    if partial_year > 0:
        if years < 5:
            gratuity += (partial_year * last_basic_salary * 0.5)
        else:
            gratuity += (partial_year * last_basic_salary)
    
    return gratuity


def calculate_vacation_allowance(years_of_service, last_basic_salary, employee=None):
    """Calculate vacation allowance for unused vacation days"""
    if not last_basic_salary or not years_of_service:
        return 0
    
    is_additional_annual_leave = False
    if employee:
        is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
    
    if is_additional_annual_leave:
        vacation_allowance = int(years_of_service) * last_basic_salary
        if years_of_service > int(years_of_service):
            partial_year = years_of_service - int(years_of_service)
            vacation_allowance += partial_year * last_basic_salary
    else:
        first_5_years = min(int(years_of_service), 5)
        vacation_allowance = first_5_years * (last_basic_salary * 0.5)
        
        if years_of_service > 5:
            remaining_years = int(years_of_service) - 5
            vacation_allowance += remaining_years * last_basic_salary
        
        if years_of_service > int(years_of_service):
            partial_year = years_of_service - int(years_of_service)
            if int(years_of_service) < 5:
                vacation_allowance += partial_year * (last_basic_salary * 0.5)
            else:
                vacation_allowance += partial_year * last_basic_salary
    
    return round(vacation_allowance, 2)


def calculate_loan_details(employee):
    """Calculate loan details for an employee"""
    try:
        loans = frappe.get_all(
            'Loan',
            filters={
                'applicant': employee,
                'docstatus': 1,
                'status': ['in', ['Sanctioned', 'Partially Disbursed', 'Disbursed']]
            },
            fields=['name', 'loan_amount', 'total_payment', 'total_amount_paid', 'status']
        )
        
        total_outstanding = 0
        loan_list = []
        
        for loan in loans:
            outstanding = flt(loan.total_payment) - flt(loan.total_amount_paid or 0)
            if outstanding > 0:
                total_outstanding += outstanding
                loan_list.append({
                    'loan_id': loan.name,
                    'loan_amount': loan.loan_amount,
                    'total_payment': loan.total_payment,
                    'paid': loan.total_amount_paid or 0,
                    'outstanding': outstanding,
                    'status': loan.status
                })
        
        return {
            'has_loan': total_outstanding > 0,
            'outstanding_balance': total_outstanding,
            'loan_count': len(loan_list),
            'loans': loan_list
        }
    
    except Exception as e:
        frappe.log_error(f"Error calculating loan details: {str(e)}", "EOS Calculator")
        return {
            'has_loan': False,
            'outstanding_balance': 0,
            'loan_count': 0,
            'loans': []
        }


@frappe.whitelist()
def create_eos_from_calculation(employee, calculation_data):
    """
    Create an EOS Settlement document from calculated data
    
    Args:
        employee: Employee ID
        calculation_data: JSON string with calculation results
    
    Returns:
        str: Name of created EOS Settlement document
    """
    import json
    
    if isinstance(calculation_data, str):
        calculation_data = json.loads(calculation_data)
    
    try:
        if not frappe.db.exists("DocType", "EOS Settlement"):
            frappe.throw(
                _("EOS Settlement DocType is not installed. Please contact your system administrator."),
                title=_("DocType Not Found")
            )
        
        eos_doc = None
        
        try:
            from phr.phr.doctype.eos_settlement.eos_settlement import EOSSettlement
            eos_doc = EOSSettlement({
                "doctype": "EOS Settlement",
                "employee": employee,
                "appointment_date": calculation_data.get('appointment_date'),
                "end_of_service_date": calculation_data.get('end_of_service_date'),
                "termination_reason": calculation_data.get('termination_reason'),
                "last_basic_salary": calculation_data.get('last_basic_salary')
            })
        except (ImportError, Exception) as e:
            frappe.log_error(f"Error importing EOSSettlement: {str(e)}", "EOS Settlement Import")
            pass
        
        if not eos_doc:
            try:
                eos_doc = frappe.get_doc({
                    "doctype": "EOS Settlement",
                    "employee": employee,
                    "appointment_date": calculation_data.get('appointment_date'),
                    "end_of_service_date": calculation_data.get('end_of_service_date'),
                    "termination_reason": calculation_data.get('termination_reason'),
                    "last_basic_salary": calculation_data.get('last_basic_salary')
                })
            except Exception:
                pass
        
        if not eos_doc:
            eos_doc = frappe.new_doc("EOS Settlement")
            eos_doc.employee = employee
            eos_doc.appointment_date = calculation_data.get('appointment_date')
            eos_doc.end_of_service_date = calculation_data.get('end_of_service_date')
            eos_doc.termination_reason = calculation_data.get('termination_reason')
            eos_doc.last_basic_salary = calculation_data.get('last_basic_salary')
        
        if eos_doc:
            eos_doc.insert()
            
            frappe.msgprint(
                _("EOS Settlement {0} created successfully").format(
                    frappe.bold(eos_doc.name)
                ),
                indicator='green',
                title=_('Success')
            )
            
            return eos_doc.name
        else:
            frappe.throw(
                _("Unable to create EOS Settlement document. Please contact your system administrator."),
                title=_("Document Creation Failed")
            )
        
    except Exception as e:
        frappe.log_error(
            f"Error creating EOS Settlement: {str(e)}",
            "EOS Settlement Creation"
        )
        
        frappe.throw(
            _("EOS Settlement DocType is not available. Please contact your system administrator to install the PHR app properly."),
            title=_("DocType Not Available")
        )


# ============================================================================
# LEAVE BALANCE CALCULATIONS
# ============================================================================

@frappe.whitelist()
def calculate_employee_leave_balance(employee, date_of_joining):
    """Calculate employee leave balance based on months of service with different rates for <5 and >=5 years"""
    try:
        if isinstance(date_of_joining, str):
            date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
        
        current_date = date.today()
        
        months_of_service = calculate_months_of_service(date_of_joining, current_date)
        years_of_service = months_of_service / 12
        
        annual_leave_balance = calculate_annual_leave_balance(months_of_service, years_of_service, employee)
        annual_leave_used = get_used_annual_leave(employee, date_of_joining)
        annual_leave_remaining = annual_leave_balance - annual_leave_used
        
        sick_leave_balance = calculate_sick_leave_balance(date_of_joining, current_date)
        sick_leave_used = get_used_sick_leave(employee, date_of_joining)
        sick_leave_remaining = sick_leave_balance - sick_leave_used
        
        return {
            'annual_leave_balance': round(annual_leave_balance, 2),
            'annual_leave_used': round(annual_leave_used, 2),
            'annual_leave_remaining': round(annual_leave_remaining, 2),
            'sick_leave_balance': round(sick_leave_balance, 2),
            'sick_leave_used': round(sick_leave_used, 2),
            'sick_leave_remaining': round(sick_leave_remaining, 2),
            'months_of_service': months_of_service,
            'years_of_service': round(years_of_service, 2),
            'calculation_rate': get_calculation_rate(years_of_service, employee)
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating leave balance for {employee}: {str(e)}")
        return None


def get_calculation_rate(years_of_service, employee=None):
    """Get calculation rate based on years of service and additional annual leave flag"""
    try:
        is_additional_annual_leave = False
        if employee:
            is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            return '2.5 days/month'
        elif years_of_service >= 5:
            return '2.5 days/month'
        else:
            return '1.75 days/month'
            
    except Exception as e:
        frappe.log_error(f"Error getting calculation rate: {str(e)}")
        return '1.75 days/month'


def calculate_annual_leave_balance(months_of_service, years_of_service, employee=None):
    """Calculate annual leave balance with different rates based on years of service and additional annual leave flag"""
    try:
        is_additional_annual_leave = False
        if employee:
            is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        if is_additional_annual_leave:
            return months_of_service * 2.5
        elif years_of_service < 5:
            return months_of_service * 1.75
        else:
            return months_of_service * 2.5
            
    except Exception as e:
        frappe.log_error(f"Error calculating annual leave balance: {str(e)}")
        return 0


def calculate_months_of_service(joining_date, current_date):
    """Calculate months of service from joining date to current date"""
    try:
        months = (current_date.year - joining_date.year) * 12 + (current_date.month - joining_date.month)
        
        if current_date.day < joining_date.day:
            months -= 1
        
        return max(0, months)
        
    except Exception as e:
        frappe.log_error(f"Error calculating months of service: {str(e)}")
        return 0


def get_used_annual_leave(employee, joining_date):
    """Get used annual leave from leave applications since joining date"""
    try:
        leave_applications = frappe.get_all('Leave Application',
            fields=['total_leave_days'],
            filters={
                'employee': employee,
                'leave_type': 'Annual Leave',
                'status': 'Approved',
                'from_date': ['>=', joining_date]
            }
        )
        
        total_used = sum(app['total_leave_days'] or 0 for app in leave_applications)
        return total_used
        
    except Exception as e:
        frappe.log_error(f"Error getting used annual leave for {employee}: {str(e)}")
        return 0


def get_used_sick_leave(employee, joining_date):
    """Get used sick leave from leave applications since joining date"""
    try:
        leave_applications = frappe.get_all('Leave Application',
            fields=['total_leave_days'],
            filters={
                'employee': employee,
                'leave_type': 'Sick Leave',
                'status': 'Approved',
                'from_date': ['>=', joining_date]
            }
        )
        
        total_used = sum(app['total_leave_days'] or 0 for app in leave_applications)
        return total_used
        
    except Exception as e:
        frappe.log_error(f"Error getting used sick leave for {employee}: {str(e)}")
        return 0


def calculate_sick_leave_balance(joining_date, current_date):
    """Calculate sick leave balance based on daily accumulation"""
    try:
        years_of_service = (current_date - joining_date).days / 365.25
        
        if years_of_service < 5:
            daily_rate = 0.0575342466
        else:
            daily_rate = 0.0821917808
        
        total_days = (current_date - joining_date).days
        sick_leave_balance = total_days * daily_rate
        
        return sick_leave_balance
        
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave balance: {str(e)}")
        return 0


@frappe.whitelist()
def update_employee_leave_balance_fields(employee):
    """Update employee leave balance fields in the database"""
    try:
        employee_doc = frappe.get_doc('Employee', employee)
        
        if not employee_doc.date_of_joining:
            frappe.msgprint(f"No joining date found for employee {employee}")
            return False
        
        balance_data = calculate_employee_leave_balance(employee, employee_doc.date_of_joining)
        
        if balance_data:
            employee_doc.annual_leave_balance = balance_data['annual_leave_balance']
            employee_doc.annual_leave_used = balance_data['annual_leave_used']
            employee_doc.annual_leave_remaining = balance_data['annual_leave_remaining']
            employee_doc.sick_leave_balance = balance_data['sick_leave_balance']
            employee_doc.sick_leave_used = balance_data['sick_leave_used']
            employee_doc.sick_leave_remaining = balance_data['sick_leave_remaining']
            employee_doc.last_leave_calculation_date = datetime.now().date()
            
            employee_doc.save()
            
            return True
        
        return False
        
    except Exception as e:
        frappe.log_error(f"Error updating leave balance fields for {employee}: {str(e)}")
        return False


@frappe.whitelist()
def get_employee_leave_summary(employee_id):
    """Get comprehensive leave summary for an employee"""
    try:
        from phr.phr.utils.leave_management import get_employee_leave_summary as get_summary
        return get_summary(employee_id)
    except ImportError:
        # Fallback if the function doesn't exist
        employee_doc = frappe.get_doc("Employee", employee_id)
        if not employee_doc.date_of_joining:
            return {"status": "error", "message": "Employee has no date of joining"}
        
        balance_data = calculate_employee_leave_balance(employee_id, employee_doc.date_of_joining)
        
        if not balance_data:
            return {"status": "error", "message": "Failed to calculate leave balance"}
        
        return {
            "employee_info": {
                "name": employee_id,
                "employee_name": employee_doc.employee_name,
                "date_of_joining": str(employee_doc.date_of_joining),
                "working_years": balance_data.get('years_of_service', 0),
                "working_months": balance_data.get('months_of_service', 0),
                "contract_end_date": str(employee_doc.contract_end_date) if employee_doc.contract_end_date else None
            },
            "annual_leave": {
                "total_allocation": balance_data.get('annual_leave_balance', 0),
                "used": balance_data.get('annual_leave_used', 0),
                "remaining": balance_data.get('annual_leave_remaining', 0)
            },
            "sick_leave": {
                "total_allocation": balance_data.get('sick_leave_balance', 0),
                "used": balance_data.get('sick_leave_used', 0),
                "remaining": balance_data.get('sick_leave_remaining', 0)
            }
        }
    except Exception as e:
        frappe.log_error(f"Error getting employee leave summary: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def calculate_annual_leave_balance(employee):
    """Calculate annual leave balance for an employee"""
    try:
        from phr.phr.utils.leave_allocation_utils import calculate_annual_leave_balance as calc_annual
        return calc_annual(employee)
    except ImportError:
        employee_doc = frappe.get_doc("Employee", employee)
        if not employee_doc.date_of_joining:
            return {"status": "error", "message": "Employee has no date of joining"}
        
        balance_data = calculate_employee_leave_balance(employee, employee_doc.date_of_joining)
        
        if not balance_data:
            return {"status": "error", "message": "Failed to calculate leave balance"}
        
        is_additional = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
        
        return {
            "employee_name": employee_doc.employee_name,
            "date_of_joining": str(employee_doc.date_of_joining),
            "years_of_service": balance_data.get('years_of_service', 0),
            "is_additional_annual_leave": is_additional,
            "days_per_month": 2.5 if (is_additional or balance_data.get('years_of_service', 0) >= 5) else 1.75,
            "total_allocation": balance_data.get('annual_leave_balance', 0),
            "days_used": balance_data.get('annual_leave_used', 0),
            "days_remaining": balance_data.get('annual_leave_remaining', 0)
        }
    except Exception as e:
        frappe.log_error(f"Error calculating annual leave balance: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_annual_leave_dashboard_data(employee):
    """Get annual leave data for dashboard display"""
    try:
        from phr.phr.utils.leave_allocation_utils import get_annual_leave_dashboard_data as get_dashboard
        return get_dashboard(employee)
    except ImportError:
        employee_doc = frappe.get_doc("Employee", employee)
        if not employee_doc.date_of_joining:
            return {}
        
        balance_data = calculate_employee_leave_balance(employee, employee_doc.date_of_joining)
        
        if not balance_data:
            return {}
        
        total_allocation = balance_data.get('annual_leave_balance', 0)
        days_used = balance_data.get('annual_leave_used', 0)
        days_remaining = balance_data.get('annual_leave_remaining', 0)
        usage_percentage = (days_used / total_allocation * 100) if total_allocation > 0 else 0
        
        return {
            "total_allocation": total_allocation,
            "days_remaining": days_remaining,
            "usage_percentage": round(usage_percentage, 2),
            "days_until_expiry": 365  # Default, should be calculated from leave period
        }
    except Exception as e:
        frappe.log_error(f"Error getting annual leave dashboard data: {str(e)}")
        return {}


# ============================================================================
# SICK LEAVE CALCULATIONS
# ============================================================================

@frappe.whitelist()
def calculate_sick_leave_deduction(employee_id, start_date, end_date, monthly_salary=None):
    """Calculate sick leave deduction for an employee"""
    try:
        from phr.phr.utils.salary_components import calculate_sick_leave_deduction as calc_deduction
        return calc_deduction(employee_id, start_date, end_date, monthly_salary)
    except ImportError:
        return {"status": "error", "message": "Sick leave deduction calculation not available"}
    except Exception as e:
        frappe.log_error(f"Error calculating sick leave deduction: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# LEAVE ALLOCATION FUNCTIONS
# ============================================================================

@frappe.whitelist()
def create_employee_leave_allocations(employee_id):
    """Create automatic leave allocations for an employee"""
    try:
        from phr.phr.api.leave_management import create_employee_leave_allocations as create_allocations
        return create_allocations(employee_id)
    except ImportError:
        return {"status": "error", "message": "Leave allocation creation not available"}
    except Exception as e:
        frappe.log_error(f"Error creating leave allocations: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# YEARS OF SERVICE CALCULATIONS
# ============================================================================

def calculate_years_of_service(joining_date):
    """Calculate years of service from joining date"""
    if not joining_date:
        return 0
    
    joining = getdate(joining_date)
    today_date = getdate(nowdate())
    
    years = today_date.year - joining.year
    if (today_date.month, today_date.day) < (joining.month, joining.day):
        years -= 1
    
    return max(0, years)


# ============================================================================
# TESTING PERIOD CALCULATIONS
# ============================================================================

def calculate_testing_period_end_date(joining_date, testing_period_months=6):
    """Calculate testing period end date (default 6 months)"""
    if not joining_date:
        return None
    
    joining = getdate(joining_date)
    return add_months(joining, testing_period_months)


def calculate_remaining_testing_days(testing_end_date):
    """Calculate remaining days in testing period"""
    if not testing_end_date:
        return 0
    
    end_date = getdate(testing_end_date)
    today_date = getdate(nowdate())
    
    remaining = date_diff(end_date, today_date)
    return max(0, remaining)


# ============================================================================
# CONTRACT CALCULATIONS
# ============================================================================

def calculate_remaining_contract_days(contract_end_date):
    """Calculate remaining days until contract end"""
    if not contract_end_date:
        return 0
    
    end_date = getdate(contract_end_date)
    today_date = getdate(nowdate())
    
    remaining = date_diff(end_date, today_date)
    return max(0, remaining)


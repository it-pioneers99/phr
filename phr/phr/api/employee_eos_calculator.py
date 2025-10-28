# -*- coding: utf-8 -*-
# Copyright (c) 2025, Pioneers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, flt
from datetime import datetime

@frappe.whitelist()
def calculate_eos_for_employee(employee, end_date=None, termination_reason="Resignation"):
    """
    Calculate EOS Settlement for an employee without creating a document.
    This is for preview/calculation purposes only.
    
    Args:
        employee: Employee ID
        end_date: End of service date (defaults to today)
        termination_reason: Resignation, Contract Expiry, or Termination by Employer
    
    Returns:
        dict: Calculated settlement details
    """
    if not employee:
        frappe.throw(_("Employee is required"))
    
    # Get employee details
    emp_doc = frappe.get_doc("Employee", employee)
    
    if not emp_doc.date_of_joining:
        frappe.throw(_("Employee {0} does not have a Date of Joining").format(employee))
    
    # Use today if no end date provided
    if not end_date:
        end_date = getdate()
    else:
        end_date = getdate(end_date)
    
    appointment_date = getdate(emp_doc.date_of_joining)
    
    # Get last basic salary
    last_basic_salary = get_employee_basic_salary(employee)
    
    # Calculate years of service
    delta = end_date - appointment_date
    years_of_service = round(delta.days / 365.25, 2)
    
    # Calculate gratuity
    gratuity_amount = calculate_gratuity(
        years_of_service, 
        last_basic_salary, 
        termination_reason
    )
    
    # Calculate vacation allowance
    vacation_allowance = calculate_vacation_allowance(
        years_of_service, 
        last_basic_salary,
        employee
    )
    
    # Calculate loan details
    loan_data = calculate_loan_details(employee)
    
    # Calculate totals
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
    """Get the employee's current basic salary"""
    # Try to get from latest salary structure assignment
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
        return flt(salary_structure_assignment)
    
    # Try to get from latest salary slip
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
        return flt(salary_slip)
    
    # If nothing found, return 0
    frappe.msgprint(
        _("No salary information found for employee {0}. Please set basic salary manually.").format(employee),
        indicator='orange'
    )
    return 0


def calculate_gratuity(years_of_service, last_basic_salary, termination_reason):
    """Calculate gratuity based on Saudi Labor Law Articles 84/85"""
    if not last_basic_salary or not years_of_service:
        return 0
    
    years = int(years_of_service)
    partial_year = years_of_service - years
    
    if termination_reason == "Termination by Employer":
        # Article 84: Employer termination
        gratuity = 0
        
        # Half salary for each year of first 5 years
        first_5_years = min(years, 5)
        gratuity += (first_5_years * last_basic_salary * 0.5)
        
        # Full salary for each year after 5 years
        if years > 5:
            remaining_years = years - 5
            gratuity += (remaining_years * last_basic_salary)
        
        # Add partial year proportionally
        if partial_year > 0:
            if years < 5:
                gratuity += (partial_year * last_basic_salary * 0.5)
            else:
                gratuity += (partial_year * last_basic_salary)
    
    elif termination_reason == "Resignation":
        # Article 85: Employee resignation
        if years < 2:
            gratuity = 0  # Nothing due
        elif years < 5:
            # One-third of Article 84 calculation
            base_gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
            gratuity = base_gratuity * (1/3)
        elif years < 10:
            # Two-thirds of Article 84 calculation
            base_gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
            gratuity = base_gratuity * (2/3)
        else:
            # Full Article 84 calculation
            gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
    else:
        # Contract expiry - same as Article 84
        gratuity = calculate_article_84_gratuity(years_of_service, last_basic_salary)
    
    return round(gratuity, 2)


def calculate_article_84_gratuity(years_of_service, last_basic_salary):
    """Calculate gratuity according to Article 84"""
    years = int(years_of_service)
    partial_year = years_of_service - years
    
    gratuity = 0
    
    # Half salary for each year of first 5 years
    first_5_years = min(years, 5)
    gratuity += (first_5_years * last_basic_salary * 0.5)
    
    # Full salary for each year after 5 years
    if years > 5:
        remaining_years = years - 5
        gratuity += (remaining_years * last_basic_salary)
    
    # Add partial year proportionally
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
    
    # Check if employee has additional annual leave
    is_additional_annual_leave = False
    if employee:
        is_additional_annual_leave = frappe.db.get_value("Employee", employee, "is_additional_annual_leave") or 0
    
    if is_additional_annual_leave:
        # If additional annual leave is checked, always give full month for all years
        vacation_allowance = int(years_of_service) * last_basic_salary
        # Add partial year proportionally
        if years_of_service > int(years_of_service):
            partial_year = years_of_service - int(years_of_service)
            vacation_allowance += partial_year * last_basic_salary
    else:
        # Standard calculation: Half month for each year of first 5 years
        first_5_years = min(int(years_of_service), 5)
        vacation_allowance = first_5_years * (last_basic_salary * 0.5)
        
        # Full month for each year after 5 years
        if years_of_service > 5:
            remaining_years = int(years_of_service) - 5
            vacation_allowance += remaining_years * last_basic_salary
        
        # Add partial year proportionally
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
        # Get all active loans
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
    
    # Create new EOS Settlement document
    try:
        # Check if DocType exists first
        if not frappe.db.exists("DocType", "EOS Settlement"):
            frappe.throw(
                _("EOS Settlement DocType is not installed. Please contact your system administrator."),
                title=_("DocType Not Found")
            )
        
        # Try multiple approaches to create the document
        eos_doc = None
        
        # Method 1: Try direct import and instantiation
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
        
        # Method 2: Try frappe.get_doc
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
        
        # Method 3: Try frappe.new_doc (fallback)
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
        
        # Return a message indicating the DocType is not available
        frappe.throw(
            _("EOS Settlement DocType is not available. Please contact your system administrator to install the PHR app properly."),
            title=_("DocType Not Available")
        )


// Employee Calculations - Consolidated JavaScript Functions
// Copyright (c) 2025, Pioneers and contributors
// All employee calculation functions consolidated in one file

// ============================================================================
// END OF SERVICE (EOS) CALCULATIONS
// ============================================================================

function show_eos_calculator_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('End of Service Settlement Calculator'),
        fields: [
            {
                fieldname: 'end_date',
                label: __('End of Service Date'),
                fieldtype: 'Date',
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldname: 'termination_reason',
                label: __('Termination Reason'),
                fieldtype: 'Select',
                options: 'Resignation\nContract Expiry\nTermination by Employer',
                default: 'Resignation',
                reqd: 1
            },
            {
                fieldname: 'section_break_salary',
                fieldtype: 'Section Break',
                label: __('Basic Salary')
            },
            {
                fieldname: 'manual_basic_salary',
                label: __('Manual Basic Salary (if not found automatically)'),
                fieldtype: 'Currency',
                description: __('Enter basic salary manually if salary information is not found automatically'),
                default: 0
            },
            {
                fieldname: 'section_break_1',
                fieldtype: 'Section Break',
                label: __('Calculated Results')
            },
            {
                fieldname: 'results_html',
                fieldtype: 'HTML',
                options: '<div class="text-muted">' + __('Click "Calculate" to see results') + '</div>'
            }
        ],
        primary_action_label: __('Calculate'),
        primary_action: function() {
            let values = d.get_values();
            
            let args = {
                employee: frm.doc.name,
                end_date: values.end_date,
                termination_reason: values.termination_reason
            };
            
            if (values.manual_basic_salary && flt(values.manual_basic_salary) > 0) {
                args.basic_salary = flt(values.manual_basic_salary);
            }
            
            frappe.call({
                method: 'phr.phr.calculations.employee_calculations.calculate_eos_for_employee',
                args: args,
                freeze: true,
                freeze_message: __('Calculating...'),
                callback: function(r) {
                    if (r.message) {
                        display_eos_results(d, r.message);
                        
                        if (r.message.salary_source === 'not_found' && (!args.basic_salary || args.basic_salary === 0)) {
                            frappe.show_alert({
                                message: __('No salary information found. Please enter basic salary manually above.'),
                                indicator: 'orange'
                            }, 5);
                            setTimeout(function() {
                                d.fields_dict.manual_basic_salary.$input.focus();
                            }, 500);
                        }
                    }
                }
            });
        },
        secondary_action_label: __('Create EOS Document'),
        secondary_action: function() {
            let values = d.get_values();
            
            let args = {
                employee: frm.doc.name,
                end_date: values.end_date,
                termination_reason: values.termination_reason
            };
            
            if (values.manual_basic_salary && flt(values.manual_basic_salary) > 0) {
                args.basic_salary = flt(values.manual_basic_salary);
            }
            
            frappe.call({
                method: 'phr.phr.calculations.employee_calculations.calculate_eos_for_employee',
                args: args,
                freeze: true,
                callback: function(r) {
                    if (r.message) {
                        frappe.call({
                            method: 'phr.phr.calculations.employee_calculations.create_eos_from_calculation',
                            args: {
                                employee: frm.doc.name,
                                calculation_data: JSON.stringify(r.message)
                            },
                            callback: function(r2) {
                                if (r2.message) {
                                    d.hide();
                                    frappe.set_route('Form', 'EOS Settlement', r2.message);
                                }
                            }
                        });
                    }
                }
            });
        }
    });
    
    d.show();
}

function display_eos_results(dialog, data) {
    let currency = frappe.defaults.get_default('currency') || 'SAR';
    
    let html = `
        <div class="eos-calculation-results">
            <style>
                .eos-calculation-results { font-family: Arial, sans-serif; }
                .eos-section { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .eos-section-title { font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                .eos-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #dee2e6; }
                .eos-label { color: #495057; }
                .eos-value { font-weight: bold; color: #2c3e50; }
                .eos-total { background: #e8f4f8; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 16px; }
                .eos-warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }
                .eos-success { background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }
                .eos-info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }
            </style>
            
            <div class="eos-section">
                <div class="eos-section-title">📋 Basic Information</div>
                <div class="eos-row">
                    <span class="eos-label">Employee:</span>
                    <span class="eos-value">${data.employee_name}</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">Date of Joining:</span>
                    <span class="eos-value">${frappe.datetime.str_to_user(data.appointment_date)}</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">End of Service Date:</span>
                    <span class="eos-value">${frappe.datetime.str_to_user(data.end_of_service_date)}</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">Years of Service:</span>
                    <span class="eos-value">${data.years_of_service} years</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">Termination Reason:</span>
                    <span class="eos-value">${data.termination_reason}</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">Last Basic Salary:</span>
                    <span class="eos-value">${format_currency(data.last_basic_salary, currency)}</span>
                </div>
                ${data.salary_source === 'not_found' || data.salary_source === 'manual' ? `
                <div class="eos-warning" style="margin-top: 10px;">
                    ${data.salary_source === 'not_found' ? 
                        '⚠️ <strong>No salary information found automatically.</strong> Please enter basic salary manually above and recalculate.' :
                        'ℹ️ <strong>Using manually entered basic salary.</strong>'
                    }
                </div>
                ` : ''}
            </div>
            
            <div class="eos-section">
                <div class="eos-section-title">💰 Entitlements</div>
                <div class="eos-row">
                    <span class="eos-label">Gratuity Amount:</span>
                    <span class="eos-value">${format_currency(data.gratuity_amount, currency)}</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">Vacation Allowance:</span>
                    <span class="eos-value">${format_currency(data.vacation_allowance, currency)}</span>
                </div>
                <div class="eos-total">
                    <div class="eos-row" style="border: none;">
                        <span class="eos-label" style="font-size: 16px;">Total Before Loan:</span>
                        <span class="eos-value" style="font-size: 16px; color: #28a745;">${format_currency(data.total_settlement_before_loan, currency)}</span>
                    </div>
                </div>
            </div>
    `;
    
    if (data.has_outstanding_loan) {
        html += `
            <div class="eos-section">
                <div class="eos-section-title">🔴 Loan Deductions</div>
                <div class="eos-warning">
                    ⚠️ Employee has ${data.loan_details.length} active loan(s)
                </div>
                <div class="eos-row">
                    <span class="eos-label">Outstanding Loan Balance:</span>
                    <span class="eos-value" style="color: #dc3545;">${format_currency(data.outstanding_loan_balance, currency)}</span>
                </div>
                <div class="eos-row">
                    <span class="eos-label">Loan Deduction:</span>
                    <span class="eos-value" style="color: #dc3545;">-${format_currency(data.loan_deduction, currency)}</span>
                </div>
        `;
        
        if (data.loan_details && data.loan_details.length > 0) {
            html += '<div style="margin-top: 10px; font-size: 12px;">';
            data.loan_details.forEach(function(loan) {
                html += `
                    <div style="padding: 5px; background: #fff; margin: 5px 0; border-radius: 3px;">
                        <strong>${loan.loan_id}</strong> - Outstanding: ${format_currency(loan.outstanding, currency)}
                    </div>
                `;
            });
            html += '</div>';
        }
        
        html += '</div>';
        
        if (data.outstanding_loan_balance > data.total_settlement_before_loan) {
            html += `
                <div class="eos-warning">
                    ⚠️ <strong>Warning:</strong> Outstanding loan (${format_currency(data.outstanding_loan_balance, currency)}) 
                    exceeds total settlement (${format_currency(data.total_settlement_before_loan, currency)}). 
                    Only ${format_currency(data.loan_deduction, currency)} will be deducted.
                    <br><strong>Remaining debt: ${format_currency(data.outstanding_loan_balance - data.loan_deduction, currency)}</strong>
                </div>
            `;
        }
    } else {
        html += `
            <div class="eos-info">
                ✓ Employee has no outstanding loans
            </div>
        `;
    }
    
    html += `
        <div class="eos-section">
            <div class="eos-section-title">🎯 Final Settlement</div>
            <div class="eos-total" style="background: ${data.net_payable_amount > 0 ? '#d4edda' : '#f8d7da'}; border: 2px solid ${data.net_payable_amount > 0 ? '#28a745' : '#dc3545'};">
                <div class="eos-row" style="border: none;">
                    <span class="eos-label" style="font-size: 18px; font-weight: bold;">NET PAYABLE AMOUNT:</span>
                    <span class="eos-value" style="font-size: 20px; color: ${data.net_payable_amount > 0 ? '#28a745' : '#dc3545'};">
                        ${format_currency(data.net_payable_amount, currency)}
                    </span>
                </div>
            </div>
        </div>
    `;
    
    if (!data.eligible_for_gratuity) {
        html += `
            <div class="eos-warning">
                ℹ️ Employee is not eligible for gratuity based on years of service and termination reason.
            </div>
        `;
    }
    
    html += '</div>';
    
    dialog.fields_dict.results_html.$wrapper.html(html);
    dialog.get_primary_btn().text(__('Recalculate'));
}

function calculate_and_update_eos(frm) {
    if (!frm.doc.eos_end_date || !frm.doc.eos_termination_reason) {
        frappe.msgprint(__('Please set End of Service Date and Termination Reason first'));
        return;
    }
    
    let args = {
        employee: frm.doc.name,
        end_date: frm.doc.eos_end_date,
        termination_reason: frm.doc.eos_termination_reason
    };
    
    if (frm.doc.eos_manual_basic_salary && flt(frm.doc.eos_manual_basic_salary) > 0) {
        args.basic_salary = flt(frm.doc.eos_manual_basic_salary);
    }
    
    frappe.call({
        method: 'phr.phr.calculations.employee_calculations.calculate_eos_for_employee',
        args: args,
        freeze: true,
        freeze_message: __('Calculating...'),
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                
                if (data.salary_source === 'not_found' && (!args.basic_salary || args.basic_salary === 0)) {
                    frappe.msgprint({
                        title: __('Salary Information Not Found'),
                        message: __('No salary information found for employee {0}. Please set basic salary manually in the form or use the calculator dialog.').format(frm.doc.name),
                        indicator: 'orange'
                    });
                }
                
                frm.set_value('eos_years_of_service', data.years_of_service);
                frm.set_value('eos_last_basic_salary', data.last_basic_salary);
                frm.set_value('eos_gratuity_amount', data.gratuity_amount);
                frm.set_value('eos_vacation_allowance', data.vacation_allowance);
                frm.set_value('eos_outstanding_loan', data.outstanding_loan_balance);
                frm.set_value('eos_loan_deduction', data.loan_deduction);
                frm.set_value('eos_total_before_loan', data.total_settlement_before_loan);
                frm.set_value('eos_net_payable_amount', data.net_payable_amount);
                
                frappe.show_alert({
                    message: __('End of Service calculation updated'),
                    indicator: 'green'
                }, 3);
            }
        }
    });
}

// ============================================================================
// LEAVE BALANCE CALCULATIONS
// ============================================================================

function calculate_all_leave_balances(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    frappe.call({
        method: 'phr.phr.calculations.employee_calculations.get_employee_leave_summary',
        args: {
            employee_id: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Calculating all leave balances...'),
        callback: function(r) {
            if (r.message && !r.message.status) {
                show_all_leave_balances_dialog(frm, r.message);
                frm.reload_doc();
            } else if (r.message && r.message.status === 'error') {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message.message || __('Failed to calculate leave balances.'),
                    indicator: 'red'
                });
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to calculate leave balances.'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to calculate leave balances: {0}', [err.message || err]),
                indicator: 'red'
            });
        }
    });
}

function show_all_leave_balances_dialog(frm, data) {
    let html = `
        <div class="all-leave-balances-results">
            <style>
                .all-leave-balances-results { font-family: Arial, sans-serif; }
                .balance-section { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .balance-section-title { font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                .balance-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #dee2e6; }
                .balance-label { color: #495057; }
                .balance-value { font-weight: bold; color: #2c3e50; }
                .balance-total { background: #e8f4f8; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 16px; }
                .balance-warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }
                .balance-success { background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }
                .balance-info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }
                .balance-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                .balance-table th, .balance-table td { padding: 8px; text-align: left; border-bottom: 1px solid #dee2e6; }
                .balance-table th { background: #e9ecef; font-weight: bold; }
            </style>
            
            <div class="balance-section">
                <div class="balance-section-title">📋 Employee Information</div>
                <div class="balance-row">
                    <span class="balance-label">Employee:</span>
                    <span class="balance-value">${data.employee_info.employee_name || data.employee_info.name}</span>
                </div>
                <div class="balance-row">
                    <span class="balance-label">Date of Joining:</span>
                    <span class="balance-value">${frappe.datetime.str_to_user(data.employee_info.date_of_joining || '')}</span>
                </div>
                <div class="balance-row">
                    <span class="balance-label">Years of Service:</span>
                    <span class="balance-value">${(data.employee_info.working_years || 0).toFixed(1)} years (${data.employee_info.working_months || 0} months)</span>
                </div>
                ${data.employee_info.contract_end_date ? `
                <div class="balance-row">
                    <span class="balance-label">Contract End Date:</span>
                    <span class="balance-value">${frappe.datetime.str_to_user(data.employee_info.contract_end_date)}</span>
                </div>
                ` : ''}
            </div>
    `;
    
    if (data.annual_leave) {
        const annual = data.annual_leave;
        html += `
            <div class="balance-section">
                <div class="balance-section-title">🏖️ Annual Leave Balance</div>
                <div class="balance-row">
                    <span class="balance-label">Calculation Rate:</span>
                    <span class="balance-value" style="color: ${annual.is_additional_annual_leave ? '#28a745' : '#2c3e50'};">
                        ${annual.days_per_month || 0} days/month
                        ${annual.is_additional_annual_leave ? ' ⭐ (Additional Annual Leave)' : ''}
                    </span>
                </div>
                ${annual.calculation_reason ? `
                <div class="balance-info">
                    ℹ️ <strong>Calculation:</strong> ${annual.calculation_reason}
                </div>
                ` : ''}
                <div class="balance-row">
                    <span class="balance-label">Total Allocated:</span>
                    <span class="balance-value">${flt(annual.total_allocated || annual.total_allocation || 0, 2)} days</span>
                </div>
                <div class="balance-row">
                    <span class="balance-label">Used:</span>
                    <span class="balance-value">${flt(annual.used || annual.total_used || 0, 2)} days</span>
                </div>
                <div class="balance-row">
                    <span class="balance-label">Remaining:</span>
                    <span class="balance-value" style="color: ${(annual.remaining || annual.days_remaining || 0) > 10 ? '#28a745' : ((annual.remaining || annual.days_remaining || 0) > 5 ? '#ffc107' : '#dc3545')}; font-size: 18px;">
                        ${flt(annual.remaining || annual.days_remaining || 0, 2)} days
                    </span>
                </div>
        `;
        
        if (annual.remaining && annual.remaining <= 5) {
            html += `
                <div class="balance-warning">
                    ⚠️ <strong>Low Balance:</strong> Only ${flt(annual.remaining, 2)} days remaining!
                </div>
            `;
        }
        
        html += `</div>`;
    }
    
    if (data.sick_leave) {
        const sick = data.sick_leave;
        html += `
            <div class="balance-section">
                <div class="balance-section-title">🏥 Sick Leave Balance</div>
                <div class="balance-row">
                    <span class="balance-label">Total Allocated:</span>
                    <span class="balance-value">${flt(sick.total_allocated || sick.total_allocation || 0, 2)} days</span>
                </div>
                <div class="balance-row">
                    <span class="balance-label">Used:</span>
                    <span class="balance-value">${flt(sick.used || sick.total_used || 0, 2)} days</span>
                </div>
                <div class="balance-row">
                    <span class="balance-label">Remaining:</span>
                    <span class="balance-value" style="color: ${(sick.remaining || sick.days_remaining || 0) > 10 ? '#28a745' : ((sick.remaining || sick.days_remaining || 0) > 5 ? '#ffc107' : '#dc3545')};">
                        ${flt(sick.remaining || sick.days_remaining || 0, 2)} days
                    </span>
                </div>
            </div>
        `;
    }
    
    html += `
            <div class="balance-success">
                ✅ <strong>Calculation Complete:</strong> All leave balances have been calculated and updated.
            </div>
        </div>
    `;
    
    const dialog = new frappe.ui.Dialog({
        title: __('All Leave Balances - {0}', [data.employee_info.employee_name || data.employee_info.name]),
        fields: [
            {
                fieldname: 'balances_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        size: 'extra-large',
        primary_action_label: __('Refresh'),
        primary_action: function() {
            dialog.hide();
            calculate_all_leave_balances(frm);
        },
        secondary_action_label: __('Close'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function calculate_annual_leave_balance(frm) {
    frappe.call({
        method: 'phr.phr.calculations.employee_calculations.calculate_annual_leave_balance',
        args: {
            employee: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Calculating annual leave balance...'),
        callback: function(r) {
            if (r.message) {
                show_annual_leave_balance_dialog(frm, r.message);
            }
        }
    });
}

function show_annual_leave_balance_dialog(frm, data) {
    let currency = frappe.defaults.get_default('currency') || 'SAR';
    let html = `
        <div class="annual-leave-balance-results">
            <style>
                .annual-leave-balance-results { font-family: Arial, sans-serif; }
                .leave-section { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .leave-section-title { font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                .leave-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #dee2e6; }
                .leave-label { color: #495057; }
                .leave-value { font-weight: bold; color: #2c3e50; }
                .leave-total { background: #e8f4f8; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 16px; }
                .leave-warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }
                .leave-success { background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }
                .leave-info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }
            </style>
            
            <div class="leave-section">
                <div class="leave-section-title">📋 Employee Information</div>
                <div class="leave-row">
                    <span class="leave-label">Employee:</span>
                    <span class="leave-value">${data.employee_name}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Date of Joining:</span>
                    <span class="leave-value">${frappe.datetime.str_to_user(data.date_of_joining)}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Years of Service:</span>
                    <span class="leave-value">${data.years_of_service} years</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Is Additional Annual Leave:</span>
                    <span class="leave-value" style="color: ${data.is_additional_annual_leave ? '#28a745' : '#6c757d'}; font-weight: bold;">
                        ${data.is_additional_annual_leave ? '✓ Yes (2.5 days/month)' : 'No (1.75 days/month)'}
                    </span>
                </div>
            </div>
            
            <div class="leave-section">
                <div class="leave-section-title">📅 Annual Leave Allocation</div>
                <div class="leave-row">
                    <span class="leave-label">Calculation Rate:</span>
                    <span class="leave-value" style="color: ${data.is_additional_annual_leave ? '#28a745' : '#2c3e50'}; font-weight: bold;">
                        ${data.days_per_month} days/month
                        ${data.is_additional_annual_leave ? ' ⭐' : ''}
                    </span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Total Allocation:</span>
                    <span class="leave-value" style="color: #28a745;">${data.total_allocation} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Days Used:</span>
                    <span class="leave-value" style="color: #dc3545;">${data.days_used} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Days Remaining:</span>
                    <span class="leave-value" style="color: #28a745;">${data.days_remaining} days</span>
                </div>
            </div>
    `;
    
    if (data.days_remaining < 5) {
        html += `
            <div class="leave-warning">
                ⚠️ <strong>Warning:</strong> Only ${data.days_remaining} days remaining! Consider planning leave carefully.
            </div>
        `;
    }
    
    html += '</div>';
    
    let dialog = new frappe.ui.Dialog({
        title: __('Annual Leave Balance - {0}', [data.employee_name]),
        fields: [
            {
                fieldname: 'balance_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        size: 'large',
        primary_action_label: __('Refresh'),
        primary_action: function() {
            dialog.hide();
            calculate_annual_leave_balance(frm);
        },
        secondary_action_label: __('Close'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

// ============================================================================
// SICK LEAVE CALCULATIONS
// ============================================================================

function calculate_sick_leave_deduction_dialog(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    let employee_ctc = frm.doc.ctc || frm.doc.cost_to_company || frm.doc.custom_ctc || 
                       frm.doc.salary || frm.doc.basic_salary || 0;
    
    if (!employee_ctc || employee_ctc === 0) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Salary Structure Assignment',
                filters: {
                    employee: frm.doc.name,
                    docstatus: 1
                },
                fields: ['base', 'from_date'],
                order_by: 'from_date desc',
                limit: 1
            },
            async: false,
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    employee_ctc = r.message[0].base || 0;
                }
            }
        });
    }
    
    const dialog = new frappe.ui.Dialog({
        title: __('Calculate Sick Leave Deduction'),
        fields: [
            {
                label: __('Select Period'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Start Date'),
                fieldtype: 'Date',
                fieldname: 'start_date',
                reqd: 1,
                default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
            },
            {
                label: __('End Date'),
                fieldtype: 'Date',
                fieldname: 'end_date',
                reqd: 1,
                default: frappe.datetime.get_today()
            },
            {
                label: __('Employee Information'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Cost to Company (CTC)'),
                fieldtype: 'Currency',
                fieldname: 'monthly_salary',
                reqd: 1,
                default: employee_ctc,
                description: __('Employee Cost to Company (CTC) used for deduction calculation.')
            }
        ],
        primary_action_label: __('Calculate'),
        primary_action: function() {
            const values = dialog.get_values();
            if (!values.start_date || !values.end_date) {
                frappe.msgprint(__('Please select both start and end dates'));
                return;
            }
            
            dialog.hide();
            perform_sick_leave_calculation(frm, values);
        },
        secondary_action_label: __('Close'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function perform_sick_leave_calculation(frm, values) {
    if (!values.monthly_salary || values.monthly_salary <= 0) {
        frappe.msgprint({
            title: __('Error'),
            message: __('Please enter a valid Cost to Company (CTC) for the employee.'),
            indicator: 'red'
        });
        return;
    }
    
    frappe.call({
        method: 'phr.phr.calculations.employee_calculations.calculate_sick_leave_deduction',
        args: {
            employee_id: frm.doc.name,
            start_date: values.start_date,
            end_date: values.end_date,
            monthly_salary: values.monthly_salary
        },
        freeze: true,
        freeze_message: __('Calculating sick leave deduction from leave applications...'),
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                let data = r.message.data || r.message;
                data.monthly_salary = values.monthly_salary;
                data.daily_salary = values.monthly_salary / 30;
                show_sick_leave_deduction_results(frm, data, values);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: (r.message && r.message.message) || __('Failed to calculate sick leave deduction.'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to calculate sick leave deduction: {0}', [err.message || err]),
                indicator: 'red'
            });
        }
    });
}

function show_sick_leave_deduction_results(frm, data, period) {
    let currency = frappe.defaults.get_default('currency') || 'SAR';
    let html = `
        <div class="sick-leave-deduction-results">
            <style>
                .sick-leave-deduction-results { font-family: Arial, sans-serif; }
                .sick-section { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .sick-section-title { font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                .sick-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #dee2e6; }
                .sick-label { color: #495057; }
                .sick-value { font-weight: bold; color: #2c3e50; }
                .sick-total { background: #e8f4f8; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 16px; }
                .sick-warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }
                .sick-info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }
            </style>
            
            <div class="sick-section">
                <div class="sick-section-title">📋 Period Information</div>
                <div class="sick-row">
                    <span class="sick-label">Start Date:</span>
                    <span class="sick-value">${frappe.datetime.str_to_user(period.start_date)}</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">End Date:</span>
                    <span class="sick-value">${frappe.datetime.str_to_user(period.end_date)}</span>
                </div>
            </div>
            
            <div class="sick-section">
                <div class="sick-section-title">💰 Cost to Company (CTC) Information</div>
                <div class="sick-row">
                    <span class="sick-label">Cost to Company (CTC):</span>
                    <span class="sick-value">${format_currency(data.monthly_salary || period.monthly_salary || 0, currency)}</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">Daily Salary Rate (CTC/30):</span>
                    <span class="sick-value">${format_currency((data.daily_salary || (data.monthly_salary || period.monthly_salary || 0) / 30), currency)}</span>
                </div>
            </div>
            
            <div class="sick-section">
                <div class="sick-section-title">🏥 Sick Leave Details</div>
                <div class="sick-row">
                    <span class="sick-label">Total Sick Days:</span>
                    <span class="sick-value">${data.sick_days_taken || data.sick_days || 0} days</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">Days 1-30 (Full Pay):</span>
                    <span class="sick-value" style="color: #28a745;">${data.days_1_30 || Math.min(data.sick_days_taken || data.sick_days || 0, 30)} days</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">Days 31-90 (75% Pay):</span>
                    <span class="sick-value" style="color: #ffc107;">${data.days_31_90 || Math.min(Math.max((data.sick_days_taken || data.sick_days || 0) - 30, 0), 60)} days</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">Days 90+ (No Pay):</span>
                    <span class="sick-value" style="color: #dc3545;">${data.days_90_plus || Math.max((data.sick_days_taken || data.sick_days || 0) - 90, 0)} days</span>
                </div>
            </div>
            
            <div class="sick-section">
                <div class="sick-section-title">💰 Deduction Calculation</div>
                <div class="sick-row">
                    <span class="sick-label">Daily Salary Rate:</span>
                    <span class="sick-value">${format_currency(data.daily_salary || 0, currency)}</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">25% Deduction (Days 31-90):</span>
                    <span class="sick-value">${format_currency(data.deduction_25_percent || 0, currency)}</span>
                </div>
                <div class="sick-row">
                    <span class="sick-label">100% Deduction (Days 90+):</span>
                    <span class="sick-value">${format_currency(data.deduction_100_percent || 0, currency)}</span>
                </div>
                <div class="sick-total">
                    <div class="sick-row" style="border: none;">
                        <span class="sick-label" style="font-size: 18px; font-weight: bold;">Total Deduction:</span>
                        <span class="sick-value" style="font-size: 20px; color: #dc3545;">
                            ${format_currency(data.total_deduction || data.deduction_amount || 0, currency)}
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="sick-info">
                <strong>Note:</strong> Sick leave deduction follows Saudi Labor Law:
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>Days 1-30: Full pay (0% deduction)</li>
                    <li>Days 31-90: 75% pay (25% deduction)</li>
                    <li>Days 90+: No pay (100% deduction)</li>
                </ul>
            </div>
        </div>
    `;
    
    const results_dialog = new frappe.ui.Dialog({
        title: __('Sick Leave Deduction - {0}', [frm.doc.employee_name || frm.doc.name]),
        fields: [
            {
                fieldname: 'results_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        size: 'large',
        primary_action_label: __('Close'),
        primary_action: function() {
            results_dialog.hide();
        }
    });
    
    results_dialog.show();
}

// ============================================================================
// TESTING PERIOD CALCULATIONS
// ============================================================================

function calculate_testing_period(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set the date of joining first.'));
        return;
    }
    
    calculate_testing_period_client_side(frm);
}

function calculate_testing_period_client_side(frm) {
    const joining_date = frappe.datetime.str_to_obj(frm.doc.date_of_joining);
    const testing_period_days = 180;
    const testing_end_date_obj = new Date(joining_date);
    testing_end_date_obj.setDate(testing_end_date_obj.getDate() + testing_period_days);
    const testing_end_date = frappe.datetime.obj_to_str(testing_end_date_obj);
    const today = frappe.datetime.get_today();
    const today_obj = frappe.datetime.str_to_obj(today);
    const testing_end_obj = frappe.datetime.str_to_obj(testing_end_date);
    const diff_time = testing_end_obj - today_obj;
    const remaining_days = Math.ceil(diff_time / (1000 * 60 * 60 * 24));
    
    let status = '';
    let status_color = '';
    let status_icon = '';
    let progress_percentage = 0;
    
    if (remaining_days > 0) {
        status = __('Active');
        status_color = remaining_days <= 30 ? 'red' : (remaining_days <= 60 ? 'orange' : 'blue');
        status_icon = remaining_days <= 30 ? '⚠️' : '⏳';
        progress_percentage = ((testing_period_days - remaining_days) / testing_period_days * 100).toFixed(1);
    } else {
        status = __('Completed');
        status_color = 'green';
        status_icon = '✅';
        progress_percentage = 100;
    }
    
    if (frm.fields_dict.testing_period_end_date) {
        frm.set_value('testing_period_end_date', frappe.datetime.obj_to_str(testing_end_date));
    }
    if (frm.fields_dict.remaining_testing_days) {
        frm.set_value('remaining_testing_days', Math.max(0, remaining_days));
    }
    
    show_testing_period_dialog(frm, {
        joining_date: frm.doc.date_of_joining,
        testing_end_date: testing_end_date,
        remaining_days: Math.max(0, remaining_days),
        status: status,
        status_color: status_color,
        status_icon: status_icon,
        progress_percentage: progress_percentage,
        testing_period_days: testing_period_days
    });
}

function show_testing_period_dialog(frm, data) {
    let html = `
        <div class="testing-period-results">
            <style>
                .testing-period-results { font-family: Arial, sans-serif; }
                .testing-section { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .testing-section-title { font-weight: bold; font-size: 14px; color: #2c3e50; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                .testing-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #dee2e6; }
                .testing-label { color: #495057; }
                .testing-value { font-weight: bold; color: #2c3e50; }
                .testing-status { padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 16px; text-align: center; }
                .testing-progress { background: #e9ecef; border-radius: 10px; height: 25px; margin: 10px 0; position: relative; overflow: hidden; }
                .testing-progress-bar { background: ${data.status_color === 'green' ? '#28a745' : (data.status_color === 'red' ? '#dc3545' : '#ffc107')}; height: 100%; transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
                .testing-info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }
                .testing-warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }
                .testing-success { background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }
            </style>
            
            <div class="testing-section">
                <div class="testing-section-title">📋 Employee Information</div>
                <div class="testing-row">
                    <span class="testing-label">Employee:</span>
                    <span class="testing-value">${frm.doc.employee_name || frm.doc.name}</span>
                </div>
                <div class="testing-row">
                    <span class="testing-label">Date of Joining:</span>
                    <span class="testing-value">${frappe.datetime.str_to_user(data.joining_date)}</span>
                </div>
            </div>
            
            <div class="testing-section">
                <div class="testing-section-title">⏱️ Testing Period Information</div>
                <div class="testing-row">
                    <span class="testing-label">Testing Period End Date:</span>
                    <span class="testing-value">${frappe.datetime.str_to_user(data.testing_end_date)}</span>
                </div>
                <div class="testing-row">
                    <span class="testing-label">Testing Period Duration:</span>
                    <span class="testing-value">${data.testing_period_days} days (6 months)</span>
                </div>
                <div class="testing-row">
                    <span class="testing-label">Remaining Days:</span>
                    <span class="testing-value" style="color: ${data.status_color === 'green' ? '#28a745' : (data.status_color === 'red' ? '#dc3545' : '#ffc107')}; font-size: 18px;">
                        ${data.remaining_days} days
                    </span>
                </div>
            </div>
            
            <div class="testing-section">
                <div class="testing-section-title">📊 Status & Progress</div>
                <div class="testing-status" style="background: ${data.status_color === 'green' ? '#d4edda' : (data.status_color === 'red' ? '#f8d7da' : '#fff3cd')}; border: 2px solid ${data.status_color === 'green' ? '#28a745' : (data.status_color === 'red' ? '#dc3545' : '#ffc107')};">
                    ${data.status_icon} <strong>${data.status}</strong>
                </div>
                <div style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span class="testing-label">Progress:</span>
                        <span class="testing-value">${data.progress_percentage}%</span>
                    </div>
                    <div class="testing-progress">
                        <div class="testing-progress-bar" style="width: ${data.progress_percentage}%;">
                            ${data.progress_percentage}%
                        </div>
                    </div>
                </div>
            </div>
    `;
    
    if (data.remaining_days > 0 && data.remaining_days <= 30) {
        html += `
            <div class="testing-warning">
                ⚠️ <strong>Warning:</strong> Testing period is ending soon! Only ${data.remaining_days} days remaining.
            </div>
        `;
    } else if (data.remaining_days > 0 && data.remaining_days <= 60) {
        html += `
            <div class="testing-info">
                ℹ️ <strong>Info:</strong> Testing period is in progress. ${data.remaining_days} days remaining.
            </div>
        `;
    } else if (data.remaining_days <= 0) {
        html += `
            <div class="testing-success">
                ✅ <strong>Completed:</strong> Testing period has been completed successfully.
            </div>
        `;
    }
    
    html += `
            <div class="testing-info">
                <strong>Note:</strong> According to Saudi Labor Law, the testing period is 180 days (6 months) from the date of joining.
            </div>
        </div>
    `;
    
    const dialog = new frappe.ui.Dialog({
        title: __('Testing Period Calculation - {0}', [frm.doc.employee_name || frm.doc.name]),
        fields: [
            {
                fieldname: 'testing_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        size: 'large',
        primary_action_label: __('Update Fields'),
        primary_action: function() {
            if (frm.fields_dict.testing_period_end_date) {
                frm.set_value('testing_period_end_date', data.testing_end_date);
            }
            if (frm.fields_dict.remaining_testing_days) {
                frm.set_value('remaining_testing_days', data.remaining_days);
            }
            frappe.show_alert({
                message: __('Testing period fields updated'),
                indicator: 'green'
            }, 3);
            dialog.hide();
        },
        secondary_action_label: __('Close'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

// ============================================================================
// LEAVE ALLOCATION FUNCTIONS
// ============================================================================

function create_automatic_leave_allocation(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    frappe.confirm(__('This will create automatic leave allocations based on the employee\'s service period. Continue?'), () => {
        frappe.call({
            method: 'phr.phr.calculations.employee_calculations.create_employee_leave_allocations',
            args: {
                employee_id: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Creating leave allocations...'),
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    frappe.msgprint({
                        title: __('Success'),
                        message: r.message.message || __('Leave allocations created successfully.'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: (r.message && r.message.message) || __('Failed to create leave allocations.'),
                        indicator: 'red'
                    });
                }
            },
            error: function(err) {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to create leave allocations: {0}', [err.message || err]),
                    indicator: 'red'
                });
            }
        });
    });
}

function sync_leave_allocation(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    frappe.call({
        method: 'phr.phr.calculations.employee_calculations.update_employee_leave_balance_fields',
        args: {
            employee: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Syncing leave allocation...'),
        callback: function(r) {
            if (r.message !== false) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Leave allocation synced successfully.'),
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to sync leave allocation.'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to sync leave allocation: {0}', [err.message || err]),
                indicator: 'red'
            });
        }
    });
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function format_currency(amount, currency) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'SAR',
        minimumFractionDigits: 2
    }).format(amount);
}

function show_annual_leave_dashboard(frm) {
    if (frm.dashboard && typeof frm.dashboard.clear === 'function') {
        frm.dashboard.clear();
    }
    
    frappe.call({
        method: 'phr.phr.calculations.employee_calculations.get_annual_leave_dashboard_data',
        args: {
            employee: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                
                if (data.total_allocation > 0) {
                    frm.dashboard.add_indicator(
                        __('Annual Leave: {0} days remaining', [data.days_remaining]),
                        data.days_remaining > 10 ? 'green' : (data.days_remaining > 5 ? 'orange' : 'red')
                    );
                    
                    frm.dashboard.add_indicator(
                        __('Usage: {0}%', [data.usage_percentage]),
                        data.usage_percentage < 50 ? 'green' : (data.usage_percentage < 80 ? 'orange' : 'red')
                    );
                    
                    if (data.days_until_expiry < 30) {
                        frm.dashboard.add_indicator(
                            __('Expires in {0} days', [data.days_until_expiry]),
                            'red'
                        );
                    }
                }
            }
        }
    });
}



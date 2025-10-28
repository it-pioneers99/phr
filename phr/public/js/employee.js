// Employee End of Service Settlement Calculator
// Copyright (c) 2025, Pioneers and contributors

frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        
        // Add EOS Calculator button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Calculate End of Service'), function() {
                show_eos_calculator_dialog(frm);
            }, __('Actions'));
        }
        
        // Add Annual Leave Balance Calculator button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Calculate Annual Leave Balance'), function() {
                calculate_annual_leave_balance(frm);
            }, __('Actions'));
        }
        
        // If EOS calculation fields are present, add calculate button
        if (frm.fields_dict.eos_net_payable_amount) {
            frm.add_custom_button(__('Refresh EOS Calculation'), function() {
                calculate_and_update_eos(frm);
            }, __('Actions'));
        }
        
        // Show annual leave balance in dashboard
        if (!frm.is_new()) {
            show_annual_leave_dashboard(frm);
        }
    }
});

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
            
            frappe.call({
                method: 'phr.phr.api.employee_eos_calculator.calculate_eos_for_employee',
                args: {
                    employee: frm.doc.name,
                    end_date: values.end_date,
                    termination_reason: values.termination_reason
                },
                freeze: true,
                freeze_message: __('Calculating...'),
                callback: function(r) {
                    if (r.message) {
                        display_eos_results(d, r.message);
                    }
                }
            });
        },
        secondary_action_label: __('Create EOS Document'),
        secondary_action: function() {
            let values = d.get_values();
            
            frappe.call({
                method: 'phr.phr.api.employee_eos_calculator.calculate_eos_for_employee',
                args: {
                    employee: frm.doc.name,
                    end_date: values.end_date,
                    termination_reason: values.termination_reason
                },
                freeze: true,
                callback: function(r) {
                    if (r.message) {
                        frappe.call({
                            method: 'phr.phr.api.employee_eos_calculator.create_eos_from_calculation',
                            args: {
                                employee: frm.doc.name,
                                calculation_data: JSON.stringify(r.message)
                            },
                            callback: function(r2) {
                                if (r2.message) {
                                    d.hide();
                                    frappe.set_route('Form', 'End of Service Settlement', r2.message);
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
    console.log(data.is_additional_annual_leave);
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
    
    // Loan section
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
        
        // Show loan details
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
        
        // Warning if loan exceeds settlement
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
    
    // Final amount
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
    console.log(frm.doc.is_additional_annual_leave);
    if (!frm.doc.eos_end_date || !frm.doc.eos_termination_reason) {
        frappe.msgprint(__('Please set End of Service Date and Termination Reason first'));
        return;
    }
    
    frappe.call({
        method: 'phr.phr.api.employee_eos_calculator.calculate_eos_for_employee',
        args: {
            employee: frm.doc.name,
            end_date: frm.doc.eos_end_date,
            termination_reason: frm.doc.eos_termination_reason
        },
        freeze: true,
        freeze_message: __('Calculating...'),
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                
                // Update fields
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

// Annual Leave Balance Calculation Functions
function calculate_annual_leave_balance(frm) {
    frappe.call({
        method: 'phr.phr.utils.leave_allocation_utils.calculate_annual_leave_balance',
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
    console.log('Annual Leave Data:', {
        is_additional_annual_leave: data.is_additional_annual_leave,
        days_per_month: data.days_per_month,
        allocation_reason: data.allocation_reason,
        total_allocation: data.total_allocation
    });
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
                    <span class="leave-label">Base Allocation:</span>
                    <span class="leave-value">${data.base_allocation} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Additional Days:</span>
                    <span class="leave-value">${data.additional_days} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Total Allocation:</span>
                    <span class="leave-value" style="color: #28a745;">${data.total_allocation} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Allocation Reason:</span>
                    <span class="leave-value">${data.allocation_reason}</span>
                </div>
            </div>
            
            <div class="leave-section">
                <div class="leave-section-title">📊 Leave Usage Summary</div>
                <div class="leave-row">
                    <span class="leave-label">Days Used:</span>
                    <span class="leave-value" style="color: #dc3545;">${data.days_used} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Days Remaining:</span>
                    <span class="leave-value" style="color: #28a745;">${data.days_remaining} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Usage Percentage:</span>
                    <span class="leave-value">${data.usage_percentage}%</span>
                </div>
            </div>
            
            <div class="leave-section">
                <div class="leave-section-title">📈 Current Year Details</div>
                <div class="leave-row">
                    <span class="leave-label">Year:</span>
                    <span class="leave-value">${data.current_year}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Allocation Start:</span>
                    <span class="leave-value">${frappe.datetime.str_to_user(data.allocation_start)}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Allocation End:</span>
                    <span class="leave-value">${frappe.datetime.str_to_user(data.allocation_end)}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Days Until Expiry:</span>
                    <span class="leave-value">${data.days_until_expiry} days</span>
                </div>
            </div>
    `;
    
    // Add warnings if applicable
    if (data.days_remaining < 5) {
        html += `
            <div class="leave-warning">
                ⚠️ <strong>Warning:</strong> Only ${data.days_remaining} days remaining! Consider planning leave carefully.
            </div>
        `;
    }
    
    if (data.usage_percentage > 80) {
        html += `
            <div class="leave-warning">
                ⚠️ <strong>High Usage:</strong> ${data.usage_percentage}% of annual leave has been used.
            </div>
        `;
    }
    
    if (data.days_remaining > 0 && data.days_until_expiry < 30) {
        html += `
            <div class="leave-warning">
                ⚠️ <strong>Expiry Warning:</strong> Annual leave expires in ${data.days_until_expiry} days. Use remaining days soon!
            </div>
        `;
    }
    
    if (data.days_remaining > 0 && data.usage_percentage < 20) {
        html += `
            <div class="leave-info">
                ℹ️ <strong>Low Usage:</strong> Only ${data.usage_percentage}% of annual leave used. Consider taking some time off!
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

function show_annual_leave_dashboard(frm) {
    // Clear existing dashboard indicators
    frm.dashboard.clear();
    
    // Add annual leave balance indicator
    frappe.call({
        method: 'phr.phr.utils.leave_allocation_utils.get_annual_leave_dashboard_data',
        args: {
            employee: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                
                // Add dashboard indicators
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


// Employee End of Service Settlement Calculator
// Copyright (c) 2025, Pioneers and contributors

frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        console.log('PHR Employee form refresh - Employee name:', frm.doc.name, 'Is new:', frm.is_new());
        
        // Always show Setup PHR Custom Fields button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Setup PHR Custom Fields'), function() {
                show_phr_fields_dialog(frm);
            }, __('Setup '));
        }
        
        // Add Loan and Custody actions - Show in all cases, grouped in dropdown
        if (!frm.is_new()) {
        try {
            const employee_name = frm.doc.name || frm.doc.employee;
            
                // Show Loans button (in PHR Calculations dropdown)
            frm.add_custom_button(__('Show Loans'), function() {
                if (!employee_name) {
                    frappe.msgprint(__('Please save the employee first.'));
                    return;
                }
                console.log('Show Loans button clicked from PHR Calculations dropdown!');
                if (typeof show_employee_loans_dialog === 'function') {
                    show_employee_loans_dialog(frm, employee_name);
                } else {
                    console.error('show_employee_loans_dialog function not found!');
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Show Loans function not found. Please check console for errors.'),
                        indicator: 'red'
                    });
                }
            }, __('PHR Calculations'));
            
                // Loan Application - Create new (in PHR Calculations dropdown)
            frm.add_custom_button(__('Loan Application'), function() {
                if (!employee_name) {
                    frappe.msgprint(__('Please save the employee first.'));
                    return;
                }
                frappe.new_doc('Loan Application', {
                    applicant_type: 'Employee',
                    applicant: employee_name,
                    applicant_name: frm.doc.employee_name,
                    company: frm.doc.company || frappe.defaults.get_default('company')
                });
                }, __('PHR Calculations'));
            
                // Show Custody Receipts for this employee (in PHR Calculations dropdown)
            frm.add_custom_button(__('Custody Receipts'), function() {
                if (!employee_name) {
                    frappe.msgprint(__('Please save the employee first.'));
                    return;
                }
                frappe.route_options = {
                    employee: employee_name
                };
                frappe.set_route('List', 'Custody Receipt');
                }, __('PHR Calculations'));
            
            console.log('PHR: Loan and Custody buttons added for employee:', employee_name);
        } catch (e) {
            console.error('PHR: Error adding Loan/Custody buttons:', e);
            frappe.show_alert({ message: __('Error adding action buttons: {0}', [e.message]), indicator: 'red' }, 5);
            }
        }

        // Check if PHR custom fields exist before showing calculation buttons
        const phrFieldsExist = check_phr_fields_exist(frm);
        
        // Only show calculation buttons if custom fields have been set up
        if (!frm.is_new() && phrFieldsExist) {
            // Leave Calculation Buttons
            frm.add_custom_button(__('Calculate Leave Balances'), function() {
                calculate_all_leave_balances(frm);
            }, __('PHR Calculations'));
            
            frm.add_custom_button(__('Calculate Annual Leave Balance'), function() {
                calculate_annual_leave_balance(frm);
            }, __('PHR Calculations'));
            
            frm.add_custom_button(__('Calculate Sick Leave Deduction'), function() {
                calculate_sick_leave_deduction_dialog(frm);
            }, __('PHR Calculations'));
            
            // Testing Period Buttons
            frm.add_custom_button(__('Calculate Testing Period'), function() {
                calculate_testing_period(frm);
            }, __('PHR Calculations'));
            
            // Leave Allocation Buttons
            frm.add_custom_button(__('Create Leave Allocations'), function() {
                create_automatic_leave_allocation(frm);
            }, __('PHR Calculations'));
            
            frm.add_custom_button(__('Sync Leave Allocation'), function() {
                sync_leave_allocation(frm);
            }, __('PHR Calculations'));
            
            // End of Service Buttons
            frm.add_custom_button(__('Calculate End of Service'), function() {
                show_eos_calculator_dialog(frm);
            }, __('PHR Calculations'));
            
            // If EOS calculation fields are present, add refresh button
            if (frm.fields_dict.eos_net_payable_amount) {
                frm.add_custom_button(__('Refresh EOS Calculation'), function() {
                    calculate_and_update_eos(frm);
                }, __('PHR Calculations'));
            }
        }
        
        // Show annual leave balance in dashboard if fields exist
        if (!frm.is_new() && phrFieldsExist) {
            show_annual_leave_dashboard(frm);
        }
    }
});

// Helper function to check if PHR custom fields exist
function check_phr_fields_exist(frm) {
    // Check for key custom fields that indicate setup was done
    const requiredFields = [
        'contract_end_date',
        'annual_leave_balance',
        'sick_leave_balance',
        'testing_period_end_date'
    ];
    
    // Check if at least 2 key fields exist
    let fieldsFound = 0;
    requiredFields.forEach(function(fieldname) {
        if (frm.fields_dict[fieldname]) {
            fieldsFound++;
        }
    });
    
    // Return true if most fields exist (at least 2 out of 4)
    return fieldsFound >= 2;
}

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
            
            // Prepare args with optional manual salary
            let args = {
                employee: frm.doc.name,
                end_date: values.end_date,
                termination_reason: values.termination_reason
            };
            
            // Only include basic_salary if it's provided and greater than 0
            if (values.manual_basic_salary && flt(values.manual_basic_salary) > 0) {
                args.basic_salary = flt(values.manual_basic_salary);
            }
            
            frappe.call({
                method: 'phr.phr.api.employee_eos_calculator.calculate_eos_for_employee',
                args: args,
                freeze: true,
                freeze_message: __('Calculating...'),
                callback: function(r) {
                    if (r.message) {
                        display_eos_results(d, r.message);
                        
                        // If salary not found and no manual salary provided, show warning and focus on field
                        if (r.message.salary_source === 'not_found' && (!args.basic_salary || args.basic_salary === 0)) {
                            frappe.show_alert({
                                message: __('No salary information found. Please enter basic salary manually above.'),
                                indicator: 'orange'
                            }, 5);
                            // Focus on the manual salary field
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
            
            // Prepare args with optional manual salary
            let args = {
                employee: frm.doc.name,
                end_date: values.end_date,
                termination_reason: values.termination_reason
            };
            
            // Only include basic_salary if it's provided and greater than 0
            if (values.manual_basic_salary && flt(values.manual_basic_salary) > 0) {
                args.basic_salary = flt(values.manual_basic_salary);
            }
            
            frappe.call({
                method: 'phr.phr.api.employee_eos_calculator.calculate_eos_for_employee',
                args: args,
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
    
    // Check if manual basic salary is set in the form
    let args = {
        employee: frm.doc.name,
        end_date: frm.doc.eos_end_date,
        termination_reason: frm.doc.eos_termination_reason
    };
    
    // If eos_manual_basic_salary field exists and has a value, use it
    if (frm.doc.eos_manual_basic_salary && flt(frm.doc.eos_manual_basic_salary) > 0) {
        args.basic_salary = flt(frm.doc.eos_manual_basic_salary);
    }
    
    frappe.call({
        method: 'phr.phr.api.employee_eos_calculator.calculate_eos_for_employee',
        args: args,
        freeze: true,
        freeze_message: __('Calculating...'),
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                
                // Show warning if salary not found
                if (data.salary_source === 'not_found' && (!args.basic_salary || args.basic_salary === 0)) {
                    frappe.msgprint({
                        title: __('Salary Information Not Found'),
                        message: __('No salary information found for employee {0}. Please set basic salary manually in the form or use the calculator dialog.').format(frm.doc.name),
                        indicator: 'orange'
                    });
                }
                
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

// Calculate all leave balances for employee
function calculate_all_leave_balances(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    frappe.call({
        method: 'phr.phr.api.leave_management.get_employee_leave_summary',
        args: {
            employee_id: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Calculating all leave balances...'),
        callback: function(r) {
            if (r.message && !r.message.status) {
                show_all_leave_balances_dialog(frm, r.message);
                // Reload form to show updated values
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

// Show comprehensive leave balances dialog
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
    
    // Annual Leave Section
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
                ${annual.expiry_date ? `
                <div class="balance-row">
                    <span class="balance-label">Expiry Date:</span>
                    <span class="balance-value">${frappe.datetime.str_to_user(annual.expiry_date)}</span>
                </div>
                ` : ''}
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
    
    // Sick Leave Section
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
    
    // Leave Allocations Section
    if (data.allocations && data.allocations.length > 0) {
        html += `
            <div class="balance-section">
                <div class="balance-section-title">📅 Active Leave Allocations</div>
                <table class="balance-table">
                    <thead>
                        <tr>
                            <th>Leave Type</th>
                            <th>Allocated</th>
                            <th>Unused</th>
                            <th>From Date</th>
                            <th>To Date</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        data.allocations.forEach(function(allocation) {
            html += `
                        <tr>
                            <td>${allocation.leave_type || ''}</td>
                            <td>${flt(allocation.total_leaves_allocated || 0, 2)} days</td>
                            <td>${flt(allocation.unused_leaves || 0, 2)} days</td>
                            <td>${frappe.datetime.str_to_user(allocation.from_date || '')}</td>
                            <td>${frappe.datetime.str_to_user(allocation.to_date || '')}</td>
                        </tr>
            `;
        });
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Recent Leave Applications Section
    if (data.applications && data.applications.length > 0) {
        html += `
            <div class="balance-section">
                <div class="balance-section-title">📝 Recent Leave Applications</div>
                <table class="balance-table">
                    <thead>
                        <tr>
                            <th>Leave Type</th>
                            <th>Days</th>
                            <th>From Date</th>
                            <th>To Date</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        // Show only last 10 applications
        const recent_apps = data.applications.slice(0, 10);
        recent_apps.forEach(function(application) {
            html += `
                        <tr>
                            <td>${application.leave_type || ''}</td>
                            <td>${flt(application.total_leave_days || 0, 2)} days</td>
                            <td>${frappe.datetime.str_to_user(application.from_date || '')}</td>
                            <td>${frappe.datetime.str_to_user(application.to_date || '')}</td>
                            <td>${application.status || 'Approved'}</td>
                        </tr>
            `;
        });
        html += `
                    </tbody>
                </table>
                ${data.applications.length > 10 ? `
                <div class="balance-info">
                    ℹ️ Showing last 10 of ${data.applications.length} applications
                </div>
                ` : ''}
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

// Create automatic leave allocations for employee
function create_automatic_leave_allocation(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    frappe.confirm(__('This will create automatic leave allocations based on the employee\'s service period. Continue?'), () => {
        frappe.call({
            method: 'phr.phr.api.leave_management.create_employee_leave_allocations',
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
                    // Reload form to show updated values
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

// Sync leave allocation for employee
function sync_leave_allocation(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    frappe.call({
        method: 'phr.phr.utils.leave_balance_calculation.update_employee_leave_balance_fields',
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
                // Reload form to show updated values
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

// Calculate sick leave deduction dialog
function calculate_sick_leave_deduction_dialog(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    // Get employee CTC (Cost to Company) - try from form first, then fetch from salary structure
    let employee_ctc = frm.doc.ctc || frm.doc.cost_to_company || frm.doc.custom_ctc || 
                       frm.doc.salary || frm.doc.basic_salary || 0;
    
    // Fetch CTC from salary structure if not in employee doc
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
                description: __('Employee Cost to Company (CTC) used for deduction calculation. Sick days will be automatically calculated from leave applications within the selected period.')
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
        secondary_action_label: __('Cancel'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

// Perform sick leave calculation
function perform_sick_leave_calculation(frm, values) {
    if (!values.monthly_salary || values.monthly_salary <= 0) {
        frappe.msgprint({
            title: __('Error'),
            message: __('Please enter a valid Cost to Company (CTC) for the employee.'),
            indicator: 'red'
        });
        return;
    }
    
    // Always calculate from leave applications based on start and end dates
    frappe.call({
        method: 'phr.phr.utils.salary_components.calculate_sick_leave_deduction',
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
                // Add salary info to the data
                let data = r.message.data || r.message;
                data.monthly_salary = values.monthly_salary;
                data.daily_salary = values.monthly_salary / 30;
                show_sick_leave_deduction_results(frm, data, values);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: (r.message && r.message.message) || __('Failed to calculate sick leave deduction. No sick leave applications found in the selected period.'),
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

// Calculate sick leave deduction with provided days
function calculate_sick_leave_with_days(frm, values) {
    if (!values.monthly_salary || values.monthly_salary <= 0) {
        frappe.msgprint({
            title: __('Error'),
            message: __('Please enter a valid monthly salary for the employee.'),
            indicator: 'red'
        });
        return;
    }
    
    frappe.call({
        method: 'phr.phr.utils.leave_allocation.calculate_sick_leave_deduction',
        args: {
            employee: frm.doc.name,
            sick_days: values.sick_days || 0,
            monthly_salary: values.monthly_salary
        },
        freeze: true,
        freeze_message: __('Calculating sick leave deduction...'),
        callback: function(r) {
            if (r.message) {
                // Ensure salary info is included
                r.message.monthly_salary = values.monthly_salary;
                if (!r.message.daily_salary) {
                    r.message.daily_salary = values.monthly_salary / 30;
                }
                show_sick_leave_deduction_results(frm, r.message, values);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to calculate sick leave deduction.'),
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

// Show sick leave deduction results
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
                    <span class="sick-label">Total Sick Days (Calculated):</span>
                    <span class="sick-value">${data.sick_days_taken || data.sick_days || 0} days</span>
                </div>
                ${data.total_leaves_count !== undefined ? `
                <div class="sick-row">
                    <span class="sick-label">Number of Leave Applications:</span>
                    <span class="sick-value">${data.total_leaves_count}</span>
                </div>
                ` : ''}
                ${data.debug_info ? `
                <div class="sick-info" style="margin-top: 10px;">
                    <strong>Debug Information:</strong><br>
                    - Sick Leave Types Found: ${data.debug_info.sick_leave_types_found || 0}<br>
                    - Total Leaves Found: ${data.debug_info.total_leaves_found || 0}<br>
                    - Leaves in Period: ${data.debug_info.leaves_in_period || 0}<br>
                    - Period: ${frappe.datetime.str_to_user(data.debug_info.period_start || '')} to ${frappe.datetime.str_to_user(data.debug_info.period_end || '')}
                </div>
                ` : ''}
                ${data.warning ? `
                <div class="sick-warning" style="margin-top: 10px;">
                    ⚠️ <strong>Warning:</strong> ${data.warning}
                </div>
                ` : ''}
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
            
            ${data.leave_details && data.leave_details.length > 0 ? `
            <div class="sick-section">
                <div class="sick-section-title">📅 Leave Applications Breakdown</div>
                <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                    <thead>
                        <tr style="background: #e9ecef;">
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">From Date</th>
                            <th style="padding: 8px; text-align: left; border-bottom: 2px solid #dee2e6;">To Date</th>
                            <th style="padding: 8px; text-align: center; border-bottom: 2px solid #dee2e6;">Calculated Days</th>
                            <th style="padding: 8px; text-align: center; border-bottom: 2px solid #dee2e6;">Stored Days</th>
                        </tr>
                    </thead>
                    <tbody>
            ` : ''}
            ${data.leave_details ? data.leave_details.map(function(leave) {
                return `
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">${frappe.datetime.str_to_user(leave.from_date)}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">${frappe.datetime.str_to_user(leave.to_date)}</td>
                            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #2c3e50;">${leave.calculated_days} days</td>
                            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #dee2e6; color: #6c757d;">${leave.stored_days} days</td>
                        </tr>
                `;
            }).join('') : ''}
            ${data.leave_details && data.leave_details.length > 0 ? `
                    </tbody>
                </table>
                <div class="sick-info" style="margin-top: 10px;">
                    ℹ️ <strong>Note:</strong> Calculated days are based on the difference between From Date and To Date (inclusive). 
                    Stored days are from the Leave Application record.
                </div>
            </div>
            ` : ''}
            
            <div class="sick-section">
                <div class="sick-section-title">💰 Deduction Calculation</div>
    `;
    
    if (data.deduction_details && data.deduction_details.length > 0) {
        html += '<div class="sick-info">';
        data.deduction_details.forEach(function(detail) {
            html += `<div>${detail}</div>`;
        });
        html += '</div>';
    }
    
    html += `
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
    `;
    
    if (data.net_salary) {
        html += `
                <div class="sick-row" style="margin-top: 10px;">
                    <span class="sick-label">Net Salary After Deduction:</span>
                    <span class="sick-value" style="color: #28a745;">${format_currency(data.net_salary, currency)}</span>
                </div>
        `;
    }
    
    html += `
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

// Calculate testing period for employee
function calculate_testing_period(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee first.'));
        return;
    }
    
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set the date of joining first.'));
        return;
    }
    
    // Calculate client-side (no server call needed)
    calculate_testing_period_client_side(frm);
}

// Calculate testing period client-side
function calculate_testing_period_client_side(frm) {
    const joining_date = frappe.datetime.str_to_obj(frm.doc.date_of_joining);
    const testing_period_days = 180; // 6 months = 180 days
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
    
    // Update form fields if they exist
    if (frm.fields_dict.testing_period_end_date) {
        frm.set_value('testing_period_end_date', frappe.datetime.obj_to_str(testing_end_date));
    }
    if (frm.fields_dict.remaining_testing_days) {
        frm.set_value('remaining_testing_days', Math.max(0, remaining_days));
    }
    
    // Show dialog with results
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

// Show testing period dialog
function show_testing_period_dialog(frm, data) {
    let currency = frappe.defaults.get_default('currency') || 'SAR';
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
    
    // Add warnings or info messages
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
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>During the testing period, either party can terminate the contract without notice</li>
                    <li>After the testing period, standard termination rules apply</li>
                </ul>
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
            // Update form fields
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

function show_annual_leave_dashboard(frm) {
    // Clear existing dashboard indicators
    if (frm.dashboard && typeof frm.dashboard.clear === 'function') {
        frm.dashboard.clear();
    }
    
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

// Function to show PHR Fields dialog with custom fields
function show_phr_fields_dialog(frm) {
    // First, get the custom fields
    frappe.call({
        method: 'phr.phr.server_scripts.add_phr_custom_fields.get_employee_custom_fields',
        callback: function(r) {
            if (r && r.message) {
                const data = r.message;
                show_phr_fields_tab_dialog(frm, data);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to fetch custom fields.'),
                    indicator: 'red'
                });
            }
        }
    });
}

// Function to show dialog with PHR Fields tab
function show_phr_fields_tab_dialog(frm, fieldsData) {
    const customFields = fieldsData.custom_fields || [];
    const configuredFields = fieldsData.configured_fields || [];
    
    // Build HTML table for custom fields
    let fieldsHtml = `
        <div class="phr-fields-container" style="max-height: 500px; overflow-y: auto;">
            <h4 style="margin-bottom: 15px;">Employee Custom Fields (${customFields.length})</h4>
            <table class="table table-bordered" style="width: 100%; font-size: 12px;">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th style="padding: 8px; width: 20%;">Field Name</th>
                        <th style="padding: 8px; width: 20%;">Label</th>
                        <th style="padding: 8px; width: 15%;">Type</th>
                        <th style="padding: 8px; width: 15%;">Options/Default</th>
                        <th style="padding: 8px; width: 10%;">Required</th>
                        <th style="padding: 8px; width: 10%;">Read Only</th>
                        <th style="padding: 8px; width: 10%;">Hidden</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    if (customFields.length === 0) {
        fieldsHtml += `
            <tr>
                <td colspan="7" style="text-align: center; padding: 20px; color: #999;">
                    No custom fields found. Click "Setup Fields" tab to create them.
                </td>
            </tr>
        `;
    } else {
        customFields.forEach(function(field) {
            const options = field.options ? (field.options.length > 50 ? field.options.substring(0, 50) + '...' : field.options) : '-';
            const defaultValue = field.default || '-';
            fieldsHtml += `
                <tr>
                    <td style="padding: 8px;">${field.fieldname || '-'}</td>
                    <td style="padding: 8px;">${field.label || '-'}</td>
                    <td style="padding: 8px;">${field.fieldtype || '-'}</td>
                    <td style="padding: 8px; font-size: 11px;">${options}<br/><small style="color: #666;">Default: ${defaultValue}</small></td>
                    <td style="padding: 8px; text-align: center;">${field.reqd ? '✓' : '-'}</td>
                    <td style="padding: 8px; text-align: center;">${field.read_only ? '✓' : '-'}</td>
                    <td style="padding: 8px; text-align: center;">${field.hidden ? '✓' : '-'}</td>
                </tr>
            `;
        });
    }
    
    fieldsHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Create dialog with tabs
    const dialog = new frappe.ui.Dialog({
        title: __('PHR Custom Fields'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'Tab Break',
                label: __('PHR Fields'),
                fieldname: 'phr_fields_tab'
            },
            {
                fieldtype: 'Section Break',
                label: __('Custom Fields List'),
                fieldname: 'fields_section'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'fields_html',
                options: fieldsHtml
            },
            {
                fieldtype: 'Tab Break',
                label: __('Setup Fields'),
                fieldname: 'setup_tab'
            },
            {
                fieldtype: 'Section Break',
                label: __('Setup Configuration'),
                fieldname: 'setup_section'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'setup_html',
                options: `
                    <div style="padding: 20px;">
                        <p>This will create/update custom fields on Employee and Leave Type doctypes.</p>
                        <p><strong>Total Configured Fields:</strong> ${configuredFields.length}</p>
                        <p><strong>Total Existing Fields:</strong> ${customFields.length}</p>
                        <button class="btn btn-primary" id="setup-phr-fields-btn" style="margin-top: 15px;">
                            ${__('Setup PHR Custom Fields')}
                        </button>
                    </div>
                `
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    // Add click handler for setup button
    dialog.$wrapper.find('#setup-phr-fields-btn').on('click', function() {
        frappe.confirm(__('This will create/update custom fields on Employee and Leave Type. Continue?'), () => {
            frappe.call({
                method: 'phr.phr.server_scripts.add_phr_custom_fields.add_phr_custom_fields',
                freeze: true,
                freeze_message: __('Setting up PHR custom fields...'),
                callback: function(r) {
                    if (r && r.message && r.message.status === 'success') {
                        frappe.msgprint({
                            title: __('Success'),
                            message: __('PHR custom fields setup completed successfully. Refreshing form...'),
                            indicator: 'green'
                        });
                        frappe.show_alert({ message: __('PHR custom fields created/updated'), indicator: 'green' }, 5);
                        dialog.hide();
                        // Refresh form to show newly created fields and buttons
                        setTimeout(function() {
                            frm.reload_doc();
                        }, 1000);
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: (r && r.message && r.message.message) || __('Unknown error'),
                            indicator: 'red'
                        });
                    }
                },
                error: function(err) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Failed to setup PHR custom fields.'),
                        indicator: 'red'
                    });
                }
            });
        });
    });
    
    dialog.show();
}

// Function to show all loans linked with employee in a dialog
function show_employee_loans_dialog(frm, employee_name) {
    console.log('show_employee_loans_dialog called for:', employee_name);
    
    if (!employee_name) {
        frappe.msgprint({
            title: __('Error'),
            message: __('Employee name is required.'),
            indicator: 'red'
        });
        return;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Loan',
            filters: {
                applicant_type: 'Employee',
                applicant: employee_name
            },
            fields: [
                'name',
                'loan_product',
                'loan_amount',
                'disbursed_amount',
                'status',
                'posting_date',
                'disbursement_date',
                'total_payment',
                'total_amount_paid',
                'total_principal_paid',
                'total_interest_payable',
                'rate_of_interest',
                'repayment_periods',
                'monthly_repayment_amount',
                'company',
                'docstatus'
            ],
            order_by: 'posting_date desc'
        },
        freeze: true,
        freeze_message: __('Loading loans...'),
        callback: function(r) {
            console.log('Loans fetched:', r.message);
            if (r.message) {
                display_loans_dialog(frm, employee_name, r.message);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to fetch loans.'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            console.error('Error fetching loans:', err);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to fetch loans: {0}', [err.message || err]),
                indicator: 'red'
            });
        }
    });
}

// Function to display loans in a dialog
function display_loans_dialog(frm, employee_name, loans) {
    console.log('display_loans_dialog called with loans:', loans);
    
    if (!loans) {
        loans = [];
    }
    
    const currency = frappe.defaults.get_default('currency') || 'SAR';
    const employee_name_display = frm.doc.employee_name || employee_name;
    
    let html = `
        <div class="employee-loans-container" style="max-height: 600px; overflow-y: auto;">
            <style>
                .employee-loans-container { font-family: Arial, sans-serif; }
                .loans-header { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
                .loans-header h4 { margin: 0 0 10px 0; color: #2c3e50; }
                .loans-summary { display: flex; gap: 20px; flex-wrap: wrap; }
                .summary-item { flex: 1; min-width: 150px; }
                .summary-label { font-size: 12px; color: #6c757d; margin-bottom: 5px; }
                .summary-value { font-size: 18px; font-weight: bold; color: #2c3e50; }
                .loan-card { 
                    margin-bottom: 15px; 
                    padding: 15px; 
                    background: #fff; 
                    border: 1px solid #dee2e6; 
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }
                .loan-card.closed { border-left-color: #95a5a6; }
                .loan-card.active { border-left-color: #27ae60; }
                .loan-card.draft { border-left-color: #f39c12; }
                .loan-header { 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center;
                    margin-bottom: 10px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e9ecef;
                }
                .loan-name { font-size: 16px; font-weight: bold; color: #2c3e50; }
                .loan-status { 
                    padding: 4px 12px; 
                    border-radius: 12px; 
                    font-size: 12px; 
                    font-weight: bold;
                    text-transform: uppercase;
                }
                .status-draft { background: #fff3cd; color: #856404; }
                .status-sanctioned { background: #d1ecf1; color: #0c5460; }
                .status-disbursed, .status-active { background: #d4edda; color: #155724; }
                .status-closed, .status-settled { background: #e2e3e5; color: #383d41; }
                .status-written-off { background: #f8d7da; color: #721c24; }
                .loan-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 10px; }
                .loan-detail-item { }
                .loan-detail-label { font-size: 11px; color: #6c757d; margin-bottom: 3px; }
                .loan-detail-value { font-size: 14px; font-weight: 600; color: #2c3e50; }
                .loan-actions { margin-top: 10px; padding-top: 10px; border-top: 1px solid #e9ecef; }
                .btn-view-loan { 
                    padding: 5px 15px; 
                    background: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 3px; 
                    cursor: pointer;
                    font-size: 12px;
                    margin-right: 5px;
                }
                .btn-view-loan:hover { background: #2980b9; }
                .no-loans { 
                    text-align: center; 
                    padding: 40px; 
                    color: #6c757d; 
                    font-size: 14px; 
                }
                .outstanding-amount { color: #dc3545; font-weight: bold; }
                .paid-amount { color: #28a745; }
            </style>
            
            <div class="loans-header">
                <h4>📋 Loans for ${employee_name_display}</h4>
                <div class="loans-summary">
                    <div class="summary-item">
                        <div class="summary-label">Total Loans</div>
                        <div class="summary-value">${loans.length}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Active Loans</div>
                        <div class="summary-value" style="color: #27ae60;">
                            ${loans.filter(l => ['Sanctioned', 'Partially Disbursed', 'Disbursed', 'Active'].includes(l.status)).length}
                        </div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Total Outstanding</div>
                        <div class="summary-value outstanding-amount">
                            ${format_currency(calculate_total_outstanding(loans), currency)}
                        </div>
                    </div>
                </div>
            </div>
    `;
    
    if (loans.length === 0) {
        html += `
            <div class="no-loans">
                <p>📭 No loans found for this employee.</p>
            </div>
        `;
    } else {
        loans.forEach(function(loan) {
            const outstanding = calculate_loan_outstanding(loan);
            const status_class = get_status_class(loan.status);
            const card_class = get_card_class(loan.status);
            
            html += `
                <div class="loan-card ${card_class}">
                    <div class="loan-header">
                        <div class="loan-name">${loan.name}</div>
                        <div class="loan-status status-${status_class}">${loan.status || 'Draft'}</div>
                    </div>
                    <div class="loan-details">
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Loan Product</div>
                            <div class="loan-detail-value">${loan.loan_product || '-'}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Loan Amount</div>
                            <div class="loan-detail-value">${format_currency(loan.loan_amount || 0, currency)}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Disbursed Amount</div>
                            <div class="loan-detail-value">${format_currency(loan.disbursed_amount || 0, currency)}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Outstanding Amount</div>
                            <div class="loan-detail-value outstanding-amount">${format_currency(outstanding, currency)}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Total Paid</div>
                            <div class="loan-detail-value paid-amount">${format_currency(loan.total_amount_paid || 0, currency)}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Interest Rate</div>
                            <div class="loan-detail-value">${loan.rate_of_interest || 0}%</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Posting Date</div>
                            <div class="loan-detail-value">${loan.posting_date ? frappe.datetime.str_to_user(loan.posting_date) : '-'}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Disbursement Date</div>
                            <div class="loan-detail-value">${loan.disbursement_date ? frappe.datetime.str_to_user(loan.disbursement_date) : '-'}</div>
                        </div>
                        ${loan.monthly_repayment_amount ? `
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Monthly Repayment</div>
                            <div class="loan-detail-value">${format_currency(loan.monthly_repayment_amount, currency)}</div>
                        </div>
                        ` : ''}
                        ${loan.repayment_periods ? `
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Repayment Periods</div>
                            <div class="loan-detail-value">${loan.repayment_periods} months</div>
                        </div>
                        ` : ''}
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Company</div>
                            <div class="loan-detail-value">${loan.company || '-'}</div>
                        </div>
                        <div class="loan-detail-item">
                            <div class="loan-detail-label">Document Status</div>
                            <div class="loan-detail-value">${loan.docstatus === 0 ? 'Draft' : (loan.docstatus === 1 ? 'Submitted' : 'Cancelled')}</div>
                        </div>
                    </div>
                    <div class="loan-actions">
                        <button class="btn-view-loan" onclick="frappe.set_route('Form', 'Loan', '${loan.name}')">
                            View Loan
                        </button>
                    </div>
                </div>
            `;
        });
    }
    
    html += '</div>';
    
    const dialog = new frappe.ui.Dialog({
        title: __('Loans - {0}', [employee_name_display]),
        fields: [
            {
                fieldname: 'loans_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        size: 'extra-large',
        primary_action_label: __('Refresh'),
        primary_action: function() {
            dialog.hide();
            show_employee_loans_dialog(frm, employee_name);
        },
        secondary_action_label: __('View All in List'),
        secondary_action: function() {
            dialog.hide();
            frappe.route_options = {
                applicant_type: 'Employee',
                applicant: employee_name
            };
            frappe.set_route('List', 'Loan');
        }
    });
    
    dialog.show();
}

// Helper function to calculate outstanding amount for a loan
function calculate_loan_outstanding(loan) {
    const total_payment = flt(loan.total_payment || 0);
    const total_paid = flt(loan.total_amount_paid || 0);
    return Math.max(0, total_payment - total_paid);
}

// Helper function to calculate total outstanding for all loans
function calculate_total_outstanding(loans) {
    let total = 0;
    loans.forEach(function(loan) {
        total += calculate_loan_outstanding(loan);
    });
    return total;
}

// Helper function to get status class for styling
function get_status_class(status) {
    if (!status) return 'draft';
    const status_lower = status.toLowerCase().replace(/\s+/g, '-');
    return status_lower;
}

// Helper function to get card class for styling
function get_card_class(status) {
    if (!status) return 'draft';
    if (['Closed', 'Settled', 'Written Off'].includes(status)) return 'closed';
    if (['Active', 'Disbursed'].includes(status)) return 'active';
    return 'draft';
}

// Helper function to format currency
function format_currency(amount, currency) {
    return frappe.format(amount, {
        fieldtype: 'Currency',
        currency: currency
    });
}

// Helper function to convert string to float
function flt(value) {
    return parseFloat(value) || 0;
}


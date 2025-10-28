frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        // Add individual calculation buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Calculate Leave Balances'), function() {
                calculate_all_leave_balances(frm);
            });
            
            frm.add_custom_button(__('Calculate Testing Period'), function() {
                calculate_testing_period(frm);
            });
            
            frm.add_custom_button(__('Create Leave Allocations'), function() {
                create_automatic_leave_allocation(frm);
            });
            
            frm.add_custom_button(__('Sync Leave Allocation'), function() {
                sync_leave_allocation(frm);
            });
            
            frm.add_custom_button(__('Calculate Sick Leave Deduction'), function() {
                calculate_sick_leave_deduction_dialog(frm);
            });
            
            frm.add_custom_button(__('Calculate End of Service'), function() {
                show_eos_calculator_dialog(frm);
            });
            
            frm.add_custom_button(__('Quick Calculations'), function() {
                show_quick_calculations_dialog(frm);
            });
        }
        
        // Show current values in dashboard
        update_dashboard_display(frm);
    },
    
    date_of_joining: function(frm) {
        if (frm.doc.date_of_joining) {
            // Calculate years of service
            calculate_years_of_service(frm);
            
            // Calculate leave balances
            calculate_all_leave_balances(frm);
            
            // Ask if user wants to create automatic leave allocations
            frappe.confirm(
                __('Would you like to create automatic leave allocations for this employee based on their joining date?'),
                function() {
                    create_automatic_leave_allocation(frm);
                }
            );
        }
    },
    
    annual_leave_balance: function(frm) {
        calculate_remaining_leave(frm);
        calculate_sick_leave_remaining(frm);
    },
    
    annual_leave_used: function(frm) {
        calculate_remaining_leave(frm);
    },
    
    sick_leave_balance: function(frm) {
        calculate_sick_leave_remaining(frm);
    },
    
    sick_leave_used: function(frm) {
        calculate_sick_leave_remaining(frm);
    },
    
    is_female: function(frm) {
        if (frm.doc.is_female && frm.doc.is_muslim) {
            frappe.msgprint(__('Employee is both Female and Muslim - can access both Female-only and Muslim-only leave types'));
        }
    },
    
    is_muslim: function(frm) {
        if (frm.doc.is_female && frm.doc.is_muslim) {
            frappe.msgprint(__('Employee is both Female and Muslim - can access both Female-only and Muslim-only leave types'));
        }
    }
});

function calculate_years_of_service(frm) {
    if (!frm.doc.date_of_joining) {
        return 0;
    }
    
    var joining_date = new Date(frm.doc.date_of_joining);
    var current_date = new Date();
    var years_of_service = (current_date - joining_date) / (1000 * 60 * 60 * 24 * 365.25);
    
    // Update years of service field if it exists
    if (frm.get_field('years_of_service')) {
        frm.set_value('years_of_service', Math.round(years_of_service * 100) / 100);
    }
    
    return years_of_service;
}

function sync_leave_allocation(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee record first'));
        return;
    }
    
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set the date of joining first'));
        return;
    }
    
    frappe.show_progress(__('Syncing Leave Allocation'), 0, 100);
    
    // Call server-side method to sync leave allocation
    frappe.call({
        method: 'phr.phr.utils.leave_allocation.sync_employee_leave_allocation',
        args: {
            employee: frm.doc.name,
            date_of_joining: frm.doc.date_of_joining,
            is_female: frm.doc.is_female || 0,
            is_muslim: frm.doc.is_muslim || 0
        },
        callback: function(r) {
            frappe.hide_progress();
            if (r.message) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Leave allocation synced successfully based on employee demographics and maximum allowed days'),
                    indicator: 'green'
                });
                frm.refresh();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to sync leave allocation'),
                    indicator: 'red'
                });
            }
        }
    });
}

function calculate_all_leave_balances(frm) {
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set the date of joining first'));
        return;
    }
    
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee record first'));
        return;
    }
    
    frappe.show_progress(__('Calculating Leave Balances'), 0, 100);
    
    // Call server-side method to calculate leave balances
    frappe.call({
        method: 'phr.phr.utils.leave_balance_calculation.calculate_employee_leave_balance',
        args: {
            employee: frm.doc.name,
            date_of_joining: frm.doc.date_of_joining
        },
        callback: function(r) {
            frappe.hide_progress();
            if (r.message) {
                // Update the form fields with calculated values
                frm.set_value('annual_leave_balance', r.message.annual_leave_balance);
                frm.set_value('annual_leave_used', r.message.annual_leave_used);
                frm.set_value('annual_leave_remaining', r.message.annual_leave_remaining);
                frm.set_value('sick_leave_balance', r.message.sick_leave_balance);
                frm.set_value('sick_leave_used', r.message.sick_leave_used);
                frm.set_value('sick_leave_remaining', r.message.sick_leave_remaining);
                
                // Show detailed calculation breakdown
                show_leave_calculation_details(r.message);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to calculate leave balances'),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_leave_calculation_details(data) {
    var message = `
        <h4>Leave Balance Calculation Details</h4>
        <p><strong>Years of Service:</strong> ${data.years_of_service} years (${data.months_of_service} months)</p>
        <p><strong>Calculation Rate:</strong> ${data.calculation_rate}</p>
        <hr>
        <h5>Annual Leave</h5>
        <p><strong>Annual Leave Balance:</strong> ${data.annual_leave_balance} days</p>
        <p><strong>Annual Leave Used:</strong> ${data.annual_leave_used} days</p>
        <p><strong>Annual Leave Remaining:</strong> ${data.annual_leave_remaining} days</p>
        <hr>
        <h5>Sick Leave</h5>
        
        <p><strong>Sick Leave Used:</strong> ${data.sick_leave_used} days</p>
        
    `;
    
    frappe.msgprint({
        title: __('Leave Balance Calculation Complete'),
        message: message,
        indicator: 'green'
    });
}

function create_automatic_leave_allocation(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee record first'));
        return;
    }
    
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set the date of joining first'));
        return;
    }
    
    frappe.show_progress(__('Creating Leave Allocations'), 50, 100);
    
    // Call server-side method to create leave allocations
    frappe.call({
        method: 'phr.phr.utils.leave_allocation.create_automatic_leave_allocation',
        args: {
            employee: frm.doc.name,
            date_of_joining: frm.doc.date_of_joining,
            is_female: frm.doc.is_female || 0,
            is_muslim: frm.doc.is_muslim || 0
        },
        callback: function(r) {
            frappe.hide_progress();
            if (r.message) {
                frappe.msgprint({
                    title: __('Success'),
                    message: __('Leave allocations created successfully based on employee demographics'),
                    indicator: 'green'
                });
                frm.refresh();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to create leave allocations'),
                    indicator: 'red'
                });
            }
        }
    });
}

function calculate_sick_leave_deduction_dialog(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__('Please save the employee record first'));
        return;
    }
    
    var dialog = new frappe.ui.Dialog({
        title: __('Calculate Sick Leave Salary Deduction'),
        fields: [
            {
                label: __('Employee'),
                fieldname: 'employee',
                fieldtype: 'Link',
                options: 'Employee',
                default: frm.doc.name,
                read_only: 1
            },
            {
                label: __('Sick Leave Days Taken'),
                fieldname: 'sick_days',
                fieldtype: 'Float',
                reqd: 1,
                description: __('Total sick leave days taken in the period')
            },
            {
                label: __('Monthly Salary'),
                fieldname: 'monthly_salary',
                fieldtype: 'Currency',
                reqd: 1,
                description: __('Employee monthly basic salary')
            }
        ],
        primary_action_label: __('Calculate Deduction'),
        primary_action: function(data) {
            calculate_sick_leave_deduction_amount(data, dialog);
        }
    });
    
    dialog.show();
}

function calculate_sick_leave_deduction_amount(data, dialog) {
    var sick_days = parseFloat(data.sick_days);
    var monthly_salary = parseFloat(data.monthly_salary);
    var daily_salary = monthly_salary / 30;
    
    var deduction_amount = 0;
    var deduction_details = [];
    
    if (sick_days <= 30) {
        // First 30 days - no deduction
        deduction_amount = 0;
        deduction_details.push(`Days 1-${Math.min(sick_days, 30)}: Full pay (0% deduction)`);
    } else if (sick_days <= 90) {
        // Days 31-90 - 25% deduction
        var days_25_percent = sick_days - 30;
        deduction_amount = daily_salary * days_25_percent * 0.25;
        deduction_details.push("Days 1-30: Full pay (0% deduction)");
        deduction_details.push(`Days 31-${sick_days}: 25% deduction`);
    } else {
        // Days 90+ - 100% deduction for excess days
        var days_25_percent = 60; // Days 31-90
        var days_100_percent = sick_days - 90;
        deduction_amount = (daily_salary * days_25_percent * 0.25) + (daily_salary * days_100_percent * 1.0);
        deduction_details.push("Days 1-30: Full pay (0% deduction)");
        deduction_details.push("Days 31-90: 25% deduction");
        deduction_details.push(`Days 91-${sick_days}: 100% deduction`);
    }
    
    dialog.hide();
    
    // Show results
    var result_dialog = new frappe.ui.Dialog({
        title: __('Sick Leave Deduction Calculation'),
        fields: [
            {
                label: __('Calculation Details'),
                fieldname: 'details',
                fieldtype: 'HTML',
                options: `
                    <div class="alert alert-info">
                        <h5>Employee: ${data.employee}</h5>
                        <p><strong>Sick Days Taken:</strong> ${sick_days} days</p>
                        <p><strong>Monthly Salary:</strong> ${monthly_salary}</p>
                        <p><strong>Daily Salary:</strong> ${daily_salary.toFixed(2)}</p>
                        <hr>
                        <h6>Deduction Breakdown:</h6>
                        ${deduction_details.map(detail => `<p>• ${detail}</p>`).join('')}
                        <hr>
                        <h5 style="color: red;"><strong>Total Deduction: ${deduction_amount.toFixed(2)}</strong></h5>
                        <h5 style="color: green;"><strong>Net Salary: ${(monthly_salary - deduction_amount).toFixed(2)}</strong></h5>
                    </div>
                `
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            result_dialog.hide();
        }
    });
    
    result_dialog.show();
}

function calculate_remaining_leave(frm) {
    var balance = parseFloat(frm.doc.annual_leave_balance || 0);
    var used = parseFloat(frm.doc.annual_leave_used || 0);
    var remaining = balance - used;
    frm.set_value('annual_leave_remaining', remaining);
}

function calculate_sick_leave_remaining(frm) {
    var balance = parseFloat(frm.doc.sick_leave_balance || 0);
    var used = parseFloat(frm.doc.sick_leave_used || 0);
    var remaining = balance - used;
    frm.set_value('sick_leave_remaining', remaining);
}

function reset_leave_balances(frm) {
    frm.set_value('annual_leave_balance', 0);
    frm.set_value('annual_leave_used', 0);
    frm.set_value('annual_leave_remaining', 0);
    frm.set_value('sick_leave_balance', 0);
    frm.set_value('sick_leave_used', 0);
    frm.set_value('sick_leave_remaining', 0);
    frappe.msgprint(__('Leave balances reset successfully'));
}

function calculate_testing_period(frm) {
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set the date of joining first'));
        return;
    }
    
    var joining_date = new Date(frm.doc.date_of_joining);
    var testing_end_date = new Date(joining_date);
    testing_end_date.setMonth(testing_end_date.getMonth() + 6); // 6 months testing period
    
    var current_date = new Date();
    var remaining_days = 0;
    var testing_status = '';
    var status_color = '';
    var status_icon = '';
    
    if (current_date < testing_end_date) {
        // Testing period is still active
        remaining_days = Math.ceil((testing_end_date - current_date) / (1000 * 60 * 60 * 24));
        testing_status = `Testing period is ACTIVE - ${remaining_days} days remaining`;
        status_color = 'orange';
        status_icon = '⏳';
    } else {
        // Testing period has passed
        remaining_days = 0;
        testing_status = 'Testing period has PASSED';
        status_color = 'green';
        status_icon = '✅';
    }
    
    // Update form fields
    frm.set_value('testing_period_end_date', testing_end_date.toISOString().split('T')[0]);
    frm.set_value('remaining_testing_days', remaining_days);
    
    // Show detailed testing period information
    var message = `
        <div class="alert alert-${status_color === 'green' ? 'success' : 'warning'}">
            <h4>${status_icon} Testing Period Status</h4>
            <p><strong>Joining Date:</strong> ${joining_date.toLocaleDateString()}</p>
            <p><strong>Testing End Date:</strong> ${testing_end_date.toLocaleDateString()}</p>
            <p><strong>Current Date:</strong> ${current_date.toLocaleDateString()}</p>
            <hr>
            <h5 style="color: ${status_color};">${testing_status}</h5>
            ${remaining_days > 0 ? 
                `<p><strong>Days Remaining:</strong> ${remaining_days} days</p>
                 <p><strong>Progress:</strong> ${Math.round(((6 * 30) - remaining_days) / (6 * 30) * 100)}% completed</p>` :
                `<p><strong>Testing Period Completed:</strong> Employee has successfully completed the 6-month testing period</p>`
            }
        </div>
    `;
    
    frappe.msgprint({
        title: __('Testing Period Calculation'),
        message: message,
        indicator: status_color
    });
}

function show_quick_calculations_dialog(frm) {
    var dialog = new frappe.ui.Dialog({
        title: __('Quick Calculations'),
        fields: [
            {
                label: __('Select Calculation'),
                fieldname: 'calculation_type',
                fieldtype: 'Select',
                options: [
                    'Show Leave Summary',
                    'Sync Leave Allocation',
                    'Calculate Sick Leave Deduction',
                    'Create New Leave Period Allocations'
                ],
                reqd: 1
            }
        ],
        primary_action_label: __('Execute'),
        primary_action: function(data) {
            dialog.hide();
            
            switch (data.calculation_type) {
                case 'Show Leave Summary':
                    show_leave_summary(frm);
                    break;
                case 'Sync Leave Allocation':
                    sync_leave_allocation(frm);
                    break;
                case 'Calculate Sick Leave Deduction':
                    calculate_sick_leave_deduction_dialog(frm);
                    break;
                case 'Create New Leave Period Allocations':
                    create_new_leave_period_allocations();
                    break;
            }
        }
    });
    
    dialog.show();
}

function create_new_leave_period_allocations() {
    frappe.confirm(
        __('This will create new leave allocations for ALL employees for the current leave period. Continue?'),
        function() {
            frappe.show_progress(__('Creating New Leave Period Allocations'), 0, 100);
            
            frappe.call({
                method: 'phr.phr.utils.leave_allocation.create_new_leave_period_allocations',
                args: {},
                callback: function(r) {
                    frappe.hide_progress();
                    if (r.message) {
                        frappe.msgprint({
                            title: __('Success'),
                            message: `New leave period allocations created successfully!<br>
                                     Allocations Created: ${r.message.allocations_created}<br>
                                     Total Employees: ${r.message.total_employees}<br>
                                     Errors: ${r.message.errors}`,
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: __('Failed to create new leave period allocations'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
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
                    <span class="leave-value">${data.days_used} days</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Days Remaining:</span>
                    <span class="leave-value" style="color: ${data.days_remaining > 0 ? '#28a745' : '#dc3545'};">
                        ${data.days_remaining} days
                    </span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Usage Percentage:</span>
                    <span class="leave-value">${data.usage_percentage}%</span>
                </div>
            </div>
            
            <div class="leave-section">
                <div class="leave-section-title">📅 Allocation Period</div>
                <div class="leave-row">
                    <span class="leave-label">Allocation Year:</span>
                    <span class="leave-value">${data.current_year}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Allocation Period:</span>
                    <span class="leave-value">${frappe.datetime.str_to_user(data.allocation_start)} to ${frappe.datetime.str_to_user(data.allocation_end)}</span>
                </div>
                <div class="leave-row">
                    <span class="leave-label">Days Until Expiry:</span>
                    <span class="leave-value">${data.days_until_expiry} days</span>
                </div>
            </div>
        </div>
    `;
    
    let dialog = new frappe.ui.Dialog({
        title: __('Annual Leave Balance - ' + data.employee_name),
        fields: [
            {
                fieldname: 'results_html',
                fieldtype: 'HTML',
                options: html
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_leave_summary(frm) {
    // Use the correct calculation function instead of old logic
    calculate_annual_leave_balance(frm);
}

function update_dashboard_display(frm) {
    // Clear existing comments
    frm.dashboard.clear_comment();
    
    
    // Show demographic info
    if (frm.doc.is_female) {
        frm.dashboard.add_comment(__('Employee is marked as Female'), 'blue', true);
    }
    if (frm.doc.is_muslim) {
        frm.dashboard.add_comment(__('Employee is marked as Muslim'), 'green', true);
    }
    
    // Show leave balances
    if (frm.doc.annual_leave_balance > 0) {
        frm.dashboard.add_comment(__('Annual Leave Balance: ' + frm.doc.annual_leave_balance + ' days'), 'info', true);
    }
    if (frm.doc.annual_leave_used > 0) {
        frm.dashboard.add_comment(__('Annual Leave Used: ' + frm.doc.annual_leave_used + ' days'), 'warning', true);
    }
    if (frm.doc.annual_leave_remaining > 0) {
        frm.dashboard.add_comment(__('Annual Leave Remaining: ' + frm.doc.annual_leave_remaining + ' days'), 'success', true);
    }
    
    if (frm.doc.sick_leave_used > 0) {
        frm.dashboard.add_comment(__('Sick Leave Used: ' + frm.doc.sick_leave_used + ' days'), 'orange', true);
    }
   
    if (frm.doc.remaining_testing_days > 0) {
        frm.dashboard.add_comment(__('Remaining Testing Days: ' + frm.doc.remaining_testing_days + ' days'), 'red', true);
    } else if (frm.doc.remaining_testing_days === 0 && frm.doc.testing_period_end_date) {
        frm.dashboard.add_comment(__('Testing Period Completed ✅'), 'green', true);
    }
}

// EOS Settlement Calculator Functions
function show_eos_calculator_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('EOS Settlement Calculator'),
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
                                    frappe.set_route('Form', 'EOS Settlement', r2.message);
                                } else if (r2.exc) {
                                    frappe.msgprint({
                                        title: __('DocType Not Available'),
                                        message: __('EOS Settlement DocType is not available. The calculation feature is working, but document creation is disabled. Please contact your system administrator.'),
                                        indicator: 'orange'
                                    });
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
                    <span class="eos-value">${frappe.datetime.str_to_user(data.date_of_joining || data.appointment_date)}</span>
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

function format_currency(amount, currency) {
    return frappe.format(amount, {
        fieldtype: 'Currency',
        options: currency
    });
}
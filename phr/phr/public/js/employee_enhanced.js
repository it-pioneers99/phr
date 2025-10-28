frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        // Add custom buttons for PHR functionality
        add_phr_buttons(frm);
        
        // Update dashboard with leave information
        update_leave_dashboard(frm);
        
        // Show employee details
        show_employee_details(frm);
    },
    
    date_of_joining: function(frm) {
        if (frm.doc.date_of_joining) {
            // Calculate working years and months
            calculate_working_period(frm);
            
            // Ask if user wants to create automatic leave allocations
            frappe.confirm(
                __('Would you like to create automatic leave allocations for this employee based on their joining date?'),
                function() {
                    create_automatic_leave_allocations(frm);
                }
            );
        }
    },
    
    contract_end_date: function(frm) {
        if (frm.doc.contract_end_date) {
            calculate_contract_days_remaining(frm);
        }
    },
    
    is_female: function(frm) {
        update_employee_restrictions(frm);
    },
    
    is_muslim: function(frm) {
        update_employee_restrictions(frm);
    }
});

function add_phr_buttons(frm) {
    // Main PHR Section
    frm.add_custom_button(__('PHR Management'), function() {
        show_phr_main_dialog(frm);
    }, __('PHR'));
    
    // Individual Action Buttons
    frm.add_custom_button(__('Calculate Annual Leave Balance'), function() {
        calculate_annual_leave_balance(frm);
    }, __('Leave Management'));
    
    frm.add_custom_button(__('Check Testing Period'), function() {
        check_testing_period(frm);
    }, __('Testing Period'));
    
    frm.add_custom_button(__('Calculate Sick Leave Deduction'), function() {
        calculate_sick_leave_deduction(frm);
    }, __('Sick Leave'));
    
    frm.add_custom_button(__('Leaves Summary'), function() {
        show_leaves_summary(frm);
    }, __('Summary'));
    
    // Advanced Analysis
    frm.add_custom_button(__('Enhanced Leave Analysis'), function() {
        show_enhanced_leave_analysis_dialog(frm);
    }, __('Advanced'));
    
    frm.add_custom_button(__('Check Eligibility'), function() {
        check_employee_eligibility(frm);
    }, __('Advanced'));
    
    // Contract Management
    frm.add_custom_button(__('Contract Management'), function() {
        show_contract_management_dialog(frm);
    }, __('Contract'));
}

function show_phr_main_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('PHR Management - ' + frm.doc.employee_name),
        fields: [
            {
                label: __('Leave Management'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Calculate Annual Leave Balance'),
                fieldtype: 'Button',
                click: function() {
                    calculate_annual_leave_balance(frm);
                    dialog.hide();
                }
            },
            {
                label: __('Show Leaves Summary'),
                fieldtype: 'Button',
                click: function() {
                    show_leaves_summary(frm);
                    dialog.hide();
                }
            },
            {
                label: __('Enhanced Leave Analysis'),
                fieldtype: 'Button',
                click: function() {
                    show_enhanced_leave_analysis_dialog(frm);
                    dialog.hide();
                }
            },
            {
                label: __('Testing Period'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Check Testing Period'),
                fieldtype: 'Button',
                click: function() {
                    check_testing_period(frm);
                    dialog.hide();
                }
            },
            {
                label: __('Sick Leave Management'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Calculate Sick Leave Deduction'),
                fieldtype: 'Button',
                click: function() {
                    calculate_sick_leave_deduction(frm);
                    dialog.hide();
                }
            },
            {
                label: __('Contract Management'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Contract Management'),
                fieldtype: 'Button',
                click: function() {
                    show_contract_management_dialog(frm);
                    dialog.hide();
                }
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function calculate_annual_leave_balance(frm) {
    frappe.call({
        method: 'phr.phr.phr.api.leave_management.get_employee_leave_summary',
        args: {
            employee_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                const annualLeave = data.annual_leave || {};
                
                // Update form fields
                frm.set_value('annual_leave_balance', annualLeave.allocated || 0);
                frm.set_value('annual_leave_used', annualLeave.used || 0);
                frm.set_value('annual_leave_remaining', annualLeave.remaining || 0);
                
                // Show detailed dialog
                show_annual_leave_dialog(data);
                
                frappe.msgprint(__('Annual leave balance calculated and updated successfully'));
            }
        }
    });
}

function show_annual_leave_dialog(data) {
    const annualLeave = data.annual_leave || {};
    const employeeInfo = data.employee_info || {};
    
    const dialog = new frappe.ui.Dialog({
        title: __('Annual Leave Balance - ' + employeeInfo.employee_name),
        fields: [
            {
                label: __('Employee Information'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Working Years'),
                fieldtype: 'Data',
                default: employeeInfo.working_years || 0,
                read_only: 1
            },
            {
                label: __('Working Months'),
                fieldtype: 'Data',
                default: employeeInfo.working_months || 0,
                read_only: 1
            },
            {
                label: __('Eligible for 30 Days'),
                fieldtype: 'Check',
                default: employeeInfo.is_eligible_30_days || false,
                read_only: 1
            },
            {
                label: __('Annual Leave Details'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Total Allocated'),
                fieldtype: 'Float',
                default: annualLeave.allocated || 0,
                read_only: 1
            },
            {
                label: __('Days Used'),
                fieldtype: 'Float',
                default: annualLeave.used || 0,
                read_only: 1
            },
            {
                label: __('Days Remaining'),
                fieldtype: 'Float',
                default: annualLeave.remaining || 0,
                read_only: 1
            },
            {
                label: __('Utilization Percentage'),
                fieldtype: 'Data',
                default: annualLeave.allocated > 0 ? 
                    ((annualLeave.used / annualLeave.allocated) * 100).toFixed(2) + '%' : '0%',
                read_only: 1
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function check_testing_period(frm) {
    if (!frm.doc.date_of_joining) {
        frappe.msgprint(__('Please set joining date first'));
        return;
    }
    
    const joiningDate = new Date(frm.doc.date_of_joining);
    const testingEndDate = new Date(joiningDate);
    testingEndDate.setMonth(testingEndDate.getMonth() + 3); // 3 months testing period
    
    frm.set_value('testing_period_end_date', testingEndDate.toISOString().split('T')[0]);
    
    const today = new Date();
    const diffTime = testingEndDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 0) {
        frm.set_value('remaining_testing_days', diffDays);
        show_testing_period_dialog(joiningDate, testingEndDate, diffDays, 'active');
    } else {
        frm.set_value('remaining_testing_days', 0);
        show_testing_period_dialog(joiningDate, testingEndDate, 0, 'completed');
    }
}

function show_testing_period_dialog(joiningDate, testingEndDate, remainingDays, status) {
    const dialog = new frappe.ui.Dialog({
        title: __('Testing Period Status'),
        fields: [
            {
                label: __('Testing Period Information'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Joining Date'),
                fieldtype: 'Date',
                default: joiningDate.toISOString().split('T')[0],
                read_only: 1
            },
            {
                label: __('Testing Period End Date'),
                fieldtype: 'Date',
                default: testingEndDate.toISOString().split('T')[0],
                read_only: 1
            },
            {
                label: __('Remaining Days'),
                fieldtype: 'Data',
                default: remainingDays,
                read_only: 1
            },
            {
                label: __('Status'),
                fieldtype: 'Data',
                default: status === 'active' ? 'Active' : 'Completed',
                read_only: 1
            },
            {
                label: __('Progress'),
                fieldtype: 'Data',
                default: status === 'active' ? 
                    ((90 - remainingDays) / 90 * 100).toFixed(1) + '%' : '100%',
                read_only: 1
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
    
    // Show appropriate message
    if (status === 'active') {
        frappe.msgprint(__('Testing period is active. ' + remainingDays + ' days remaining.'));
    } else {
        frappe.msgprint(__('Testing period has been completed.'));
    }
}

function calculate_sick_leave_deduction(frm) {
    // Show dialog to select period for sick leave calculation
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
                reqd: 1
            },
            {
                label: __('End Date'),
                fieldtype: 'Date',
                fieldname: 'end_date',
                reqd: 1
            },
            {
                label: __('Salary Period'),
                fieldtype: 'Select',
                options: ['Monthly', 'Bi-weekly', 'Weekly'],
                default: 'Monthly',
                fieldname: 'salary_period'
            }
        ],
        primary_action_label: __('Calculate'),
        primary_action: function() {
            const values = dialog.get_values();
            if (!values.start_date || !values.end_date) {
                frappe.msgprint(__('Please select both start and end dates'));
                return;
            }
            
            perform_sick_leave_calculation(frm, values);
            dialog.hide();
        },
        secondary_action_label: __('Cancel'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function perform_sick_leave_calculation(frm, values) {
    frappe.call({
        method: 'phr.phr.phr.utils.salary_components.calculate_sick_leave_deduction',
        args: {
            employee_id: frm.doc.name,
            start_date: values.start_date,
            end_date: values.end_date
        },
        callback: function(r) {
            if (r.message) {
                show_sick_leave_deduction_results(r.message, values);
            }
        }
    });
}

function show_sick_leave_deduction_results(data, period) {
    const dialog = new frappe.ui.Dialog({
        title: __('Sick Leave Deduction Calculation'),
        fields: [
            {
                label: __('Period Information'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Start Date'),
                fieldtype: 'Date',
                default: period.start_date,
                read_only: 1
            },
            {
                label: __('End Date'),
                fieldtype: 'Date',
                default: period.end_date,
                read_only: 1
            },
            {
                label: __('Sick Leave Details'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Total Sick Days Taken'),
                fieldtype: 'Data',
                default: data.sick_days_taken || 0,
                read_only: 1
            },
            {
                label: __('Days 1-30 (Full Pay)'),
                fieldtype: 'Data',
                default: Math.min(data.sick_days_taken || 0, 30),
                read_only: 1
            },
            {
                label: __('Days 31-90 (75% Pay)'),
                fieldtype: 'Data',
                default: data.deduction_25_percent || 0,
                read_only: 1
            },
            {
                label: __('Days 90+ (No Pay)'),
                fieldtype: 'Data',
                default: data.deduction_100_percent || 0,
                read_only: 1
            },
            {
                label: __('Total Deduction'),
                fieldtype: 'Currency',
                default: data.total_deduction || 0,
                read_only: 1
            },
            {
                label: __('Deduction Breakdown'),
                fieldtype: 'HTML',
                fieldname: 'deduction_breakdown'
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    // Generate deduction breakdown HTML
    const breakdown = generate_deduction_breakdown(data);
    dialog.fields_dict.deduction_breakdown.$wrapper.html(breakdown);
    
    dialog.show();
}

function generate_deduction_breakdown(data) {
    let html = '<div style="margin-top: 10px;">';
    html += '<h5>Deduction Rules:</h5>';
    html += '<ul>';
    html += '<li><strong>Days 1-30:</strong> Full pay (0% deduction)</li>';
    html += '<li><strong>Days 31-90:</strong> 75% pay (25% deduction)</li>';
    html += '<li><strong>Days 90+:</strong> No pay (100% deduction)</li>';
    html += '</ul>';
    
    if (data.sick_days_taken > 0) {
        html += '<h5>Calculation:</h5>';
        html += '<table class="table table-bordered" style="margin-top: 10px;">';
        html += '<tr><td>Total Sick Days</td><td>' + data.sick_days_taken + '</td></tr>';
        html += '<tr><td>Full Pay Days</td><td>' + Math.min(data.sick_days_taken, 30) + '</td></tr>';
        html += '<tr><td>75% Pay Days</td><td>' + (data.deduction_25_percent || 0) + '</td></tr>';
        html += '<tr><td>No Pay Days</td><td>' + (data.deduction_100_percent || 0) + '</td></tr>';
        html += '<tr><td><strong>Total Deduction</strong></td><td><strong>' + (data.total_deduction || 0) + '</strong></td></tr>';
        html += '</table>';
    }
    
    html += '</div>';
    return html;
}

function show_leaves_summary(frm) {
    frappe.call({
        method: 'phr.phr.phr.api.leave_management.get_employee_leave_summary',
        args: {
            employee_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                show_comprehensive_leaves_summary(data);
            }
        }
    });
}

function show_comprehensive_leaves_summary(data) {
    const employeeInfo = data.employee_info || {};
    const annualLeave = data.annual_leave || {};
    const sickLeave = data.sick_leave || {};
    
    const dialog = new frappe.ui.Dialog({
        title: __('Leaves Summary - ' + employeeInfo.employee_name),
        fields: [
            {
                label: __('Employee Information'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Employee Name'),
                fieldtype: 'Data',
                default: employeeInfo.employee_name || '',
                read_only: 1
            },
            {
                label: __('Working Years'),
                fieldtype: 'Data',
                default: employeeInfo.working_years || 0,
                read_only: 1
            },
            {
                label: __('Working Months'),
                fieldtype: 'Data',
                default: employeeInfo.working_months || 0,
                read_only: 1
            },
            {
                label: __('Eligible for 30 Days Annual Leave'),
                fieldtype: 'Check',
                default: employeeInfo.is_eligible_30_days || false,
                read_only: 1
            },
            {
                label: __('Annual Leave'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Total Allocated'),
                fieldtype: 'Float',
                default: annualLeave.allocated || 0,
                read_only: 1
            },
            {
                label: __('Days Used'),
                fieldtype: 'Float',
                default: annualLeave.used || 0,
                read_only: 1
            },
            {
                label: __('Days Remaining'),
                fieldtype: 'Float',
                default: annualLeave.remaining || 0,
                read_only: 1
            },
            {
                label: __('Sick Leave'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Daily Accumulation Rate'),
                fieldtype: 'Float',
                default: sickLeave.daily_rate || 0,
                read_only: 1
            },
            {
                label: __('Accumulated This Year'),
                fieldtype: 'Float',
                default: sickLeave.accumulated_this_year || 0,
                read_only: 1
            },
            {
                label: __('Total Remaining'),
                fieldtype: 'Float',
                default: sickLeave.total_remaining || 0,
                read_only: 1
            },
            {
                label: __('Leave Allocations'),
                fieldtype: 'HTML',
                fieldname: 'allocations_html'
            },
            {
                label: __('Recent Leave Applications'),
                fieldtype: 'HTML',
                fieldname: 'applications_html'
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    // Generate HTML content for allocations and applications
    const allocationsHtml = generate_allocations_html(data.allocations || []);
    const applicationsHtml = generate_applications_html(data.applications || []);
    
    dialog.fields_dict.allocations_html.$wrapper.html(allocationsHtml);
    dialog.fields_dict.applications_html.$wrapper.html(applicationsHtml);
    
    dialog.show();
}

function generate_allocations_html(allocations) {
    if (allocations.length === 0) {
        return '<p>No leave allocations found.</p>';
    }
    
    let html = '<div style="max-height: 200px; overflow-y: auto;">';
    html += '<table class="table table-bordered table-condensed">';
    html += '<thead><tr><th>Leave Type</th><th>Allocated</th><th>Used</th><th>Remaining</th><th>Period</th></tr></thead>';
    html += '<tbody>';
    
    allocations.forEach(function(alloc) {
        html += '<tr>';
        html += '<td>' + (alloc.leave_type || '') + '</td>';
        html += '<td>' + (alloc.total_leaves_allocated || 0) + '</td>';
        html += '<td>' + ((alloc.total_leaves_allocated || 0) - (alloc.unused_leaves || 0)) + '</td>';
        html += '<td>' + (alloc.unused_leaves || 0) + '</td>';
        html += '<td>' + (alloc.from_date || '') + ' to ' + (alloc.to_date || '') + '</td>';
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += '</div>';
    return html;
}

function generate_applications_html(applications) {
    if (applications.length === 0) {
        return '<p>No leave applications found.</p>';
    }
    
    let html = '<div style="max-height: 200px; overflow-y: auto;">';
    html += '<table class="table table-bordered table-condensed">';
    html += '<thead><tr><th>Leave Type</th><th>From Date</th><th>To Date</th><th>Days</th><th>Status</th></tr></thead>';
    html += '<tbody>';
    
    applications.slice(0, 10).forEach(function(app) { // Show only last 10 applications
        html += '<tr>';
        html += '<td>' + (app.leave_type || '') + '</td>';
        html += '<td>' + (app.from_date || '') + '</td>';
        html += '<td>' + (app.to_date || '') + '</td>';
        html += '<td>' + (app.total_leave_days || 0) + '</td>';
        html += '<td><span class="label label-' + get_status_class(app.status) + '">' + (app.status || '') + '</span></td>';
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += '</div>';
    return html;
}

function get_status_class(status) {
    switch(status) {
        case 'Approved': return 'success';
        case 'Rejected': return 'danger';
        case 'Pending': return 'warning';
        default: return 'default';
    }
}

function show_contract_management_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Contract Management'),
        fields: [
            {
                label: __('Contract Actions'),
                fieldtype: 'Section Break'
            },
            {
                label: __('Calculate Contract Days'),
                fieldtype: 'Button',
                click: function() {
                    calculate_contract_days_remaining(frm);
                    dialog.hide();
                }
            },
            {
                label: __('Send Contract Notification'),
                fieldtype: 'Button',
                click: function() {
                    send_contract_notification(frm);
                    dialog.hide();
                }
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function calculate_working_period(frm) {
    if (!frm.doc.date_of_joining) return;
    
    frappe.call({
        method: 'phr.phr.phr.api.leave_management.check_employee_eligibility_api',
        args: {
            employee_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                frm.dashboard.add_comment(__('Working Years: ' + data.working_years), 'info', true);
                frm.dashboard.add_comment(__('Working Months: ' + data.working_months), 'info', true);
                
                // Show eligibility status
                const eligibility = data.is_eligible_30_days ? '30 days' : '21 days';
                frm.dashboard.add_comment(__('Annual Leave Eligibility: ' + eligibility), 'success', true);
                
                // Show sick leave daily rate
                frm.dashboard.add_comment(__('Sick Leave Daily Rate: ' + data.sick_leave_daily_rate.toFixed(6)), 'info', true);
            }
        }
    });
}

function create_automatic_leave_allocations(frm) {
    frappe.call({
        method: 'phr.phr.phr.api.leave_management.create_employee_leave_allocations',
        args: {
            employee_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.msgprint(__('Leave allocations created successfully: ' + r.message.message));
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Error creating leave allocations: ' + (r.message.message || 'Unknown error')));
            }
        }
    });
}

function check_employee_eligibility(frm) {
    frappe.call({
        method: 'phr.phr.phr.api.leave_management.check_employee_eligibility_api',
        args: {
            employee_id: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                show_eligibility_dialog(data);
            }
        }
    });
}

function show_eligibility_dialog(data) {
    const dialog = new frappe.ui.Dialog({
        title: __('Employee Eligibility Status'),
        fields: [
            {
                label: __('Working Years'),
                fieldtype: 'Data',
                default: data.working_years,
                read_only: 1
            },
            {
                label: __('Working Months'),
                fieldtype: 'Data',
                default: data.working_months,
                read_only: 1
            },
            {
                label: __('Eligible for 30 Days Annual Leave'),
                fieldtype: 'Check',
                default: data.is_eligible_30_days,
                read_only: 1
            },
            {
                label: __('Annual Leave Days'),
                fieldtype: 'Data',
                default: data.annual_leave_days,
                read_only: 1
            },
            {
                label: __('Sick Leave Daily Rate'),
                fieldtype: 'Data',
                default: data.sick_leave_daily_rate.toFixed(6),
                read_only: 1
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function show_enhanced_leave_analysis_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Enhanced Leave Analysis'),
        fields: [
            {
                label: __('Leave Type'),
                fieldtype: 'Link',
                options: 'Leave Type',
                fieldname: 'leave_type'
            },
            {
                label: __('Start Date'),
                fieldtype: 'Date',
                fieldname: 'start_date'
            },
            {
                label: __('End Date'),
                fieldtype: 'Date',
                fieldname: 'end_date'
            },
            {
                label: __('Analysis Type'),
                fieldtype: 'Select',
                options: ['By Type', 'By Period', 'Complete Analysis'],
                default: 'Complete Analysis',
                fieldname: 'analysis_type'
            }
        ],
        primary_action_label: __('Analyze'),
        primary_action: function() {
            const values = dialog.get_values();
            if (values.analysis_type === 'By Period' && (!values.start_date || !values.end_date)) {
                frappe.msgprint(__('Please select both start and end dates for period analysis'));
                return;
            }
            
            perform_enhanced_analysis(frm, values);
            dialog.hide();
        },
        secondary_action_label: __('Cancel'),
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
}

function perform_enhanced_analysis(frm, values) {
    let method = 'phr.phr.phr.api.leave_management.get_enhanced_leave_analysis_api';
    let args = { employee_id: frm.doc.name };
    
    if (values.analysis_type === 'By Type' && values.leave_type) {
        method = 'phr.phr.phr.api.leave_management.get_leave_analysis_by_type';
        args.leave_type = values.leave_type;
    } else if (values.analysis_type === 'By Period' && values.start_date && values.end_date) {
        method = 'phr.phr.phr.api.leave_management.get_leave_analysis_by_period';
        args.start_date = values.start_date;
        args.end_date = values.end_date;
        if (values.leave_type) {
            args.leave_type = values.leave_type;
        }
    }
    
    frappe.call({
        method: method,
        args: args,
        callback: function(r) {
            if (r.message) {
                show_analysis_results(r.message, values.analysis_type);
            }
        }
    });
}

function show_analysis_results(data, analysis_type) {
    let title = __('Leave Analysis Results');
    if (analysis_type === 'By Type') {
        title = __('Leave Analysis by Type');
    } else if (analysis_type === 'By Period') {
        title = __('Leave Analysis by Period');
    }
    
    const dialog = new frappe.ui.Dialog({
        title: title,
        fields: [
            {
                label: __('Analysis Data'),
                fieldtype: 'HTML',
                fieldname: 'analysis_html'
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });
    
    // Generate HTML content based on analysis type
    let html = generate_analysis_html(data, analysis_type);
    dialog.fields_dict.analysis_html.$wrapper.html(html);
    
    dialog.show();
}

function generate_analysis_html(data, analysis_type) {
    let html = '<div style="max-height: 400px; overflow-y: auto;">';
    
    if (data.employee_info) {
        html += '<h4>Employee Information</h4>';
        html += '<table class="table table-bordered">';
        html += '<tr><td><strong>Name:</strong></td><td>' + data.employee_info.employee_name + '</td></tr>';
        html += '<tr><td><strong>Working Years:</strong></td><td>' + data.employee_info.working_years + '</td></tr>';
        html += '<tr><td><strong>Working Months:</strong></td><td>' + data.employee_info.working_months + '</td></tr>';
        html += '<tr><td><strong>Eligible for 30 Days:</strong></td><td>' + (data.employee_info.is_eligible_30_days ? 'Yes' : 'No') + '</td></tr>';
        html += '</table>';
    }
    
    if (data.leave_balances) {
        html += '<h4>Leave Balances by Type</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><th>Leave Type</th><th>Allocated</th><th>Used</th><th>Remaining</th></tr></thead>';
        html += '<tbody>';
        
        for (let [leaveType, balance] of Object.entries(data.leave_balances)) {
            html += '<tr>';
            html += '<td>' + leaveType + '</td>';
            html += '<td>' + balance.allocated + '</td>';
            html += '<td>' + balance.used + '</td>';
            html += '<td>' + balance.remaining + '</td>';
            html += '</tr>';
        }
        
        html += '</tbody></table>';
    }
    
    if (data.period_analysis && data.period_analysis.leave_type_breakdown) {
        html += '<h4>Period Analysis</h4>';
        html += '<table class="table table-bordered">';
        html += '<thead><tr><th>Leave Type</th><th>Allocated</th><th>Used</th><th>Remaining</th><th>Applications</th></tr></thead>';
        html += '<tbody>';
        
        for (let [leaveType, breakdown] of Object.entries(data.period_analysis.leave_type_breakdown)) {
            html += '<tr>';
            html += '<td>' + leaveType + '</td>';
            html += '<td>' + breakdown.allocated + '</td>';
            html += '<td>' + breakdown.used + '</td>';
            html += '<td>' + breakdown.remaining + '</td>';
            html += '<td>' + breakdown.applications_count + '</td>';
            html += '</tr>';
        }
        
        html += '</tbody></table>';
    }
    
    html += '</div>';
    return html;
}

function calculate_contract_days_remaining(frm) {
    if (!frm.doc.contract_end_date) return;
    
    const today = new Date();
    const contractEnd = new Date(frm.doc.contract_end_date);
    const diffTime = contractEnd - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 0) {
        frm.dashboard.add_comment(__('Contract ends in ' + diffDays + ' days'), 'warning', true);
        
        if (diffDays <= 90) {
            frappe.msgprint(__('Contract ending soon! Consider sending notification to HR team.'));
        }
    } else {
        frm.dashboard.add_comment(__('Contract has expired'), 'danger', true);
    }
}

function send_contract_notification(frm) {
    if (!frm.doc.contract_end_date) {
        frappe.msgprint(__('Please set contract end date first'));
        return;
    }
    
    frappe.call({
        method: 'phr.phr.phr.utils.contract_management.check_contract_end_notifications',
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.msgprint(__('Contract notification sent successfully'));
            } else {
                frappe.msgprint(__('Error sending notification: ' + (r.message.message || 'Unknown error')));
            }
        }
    });
}

function update_employee_restrictions(frm) {
    let restrictions = [];
    
    if (frm.doc.is_female) {
        restrictions.push('Female');
    }
    if (frm.doc.is_muslim) {
        restrictions.push('Muslim');
    }
    
    if (restrictions.length > 0) {
        frm.dashboard.add_comment(__('Employee Restrictions: ' + restrictions.join(', ')), 'info', true);
    }
}

function update_leave_dashboard(frm) {
    // Clear existing comments
    frm.dashboard.clear_comments();
    
    // Show employee type
    if (frm.doc.is_female) {
        frm.dashboard.add_comment(__('Female Employee'), 'blue', true);
    }
    if (frm.doc.is_muslim) {
        frm.dashboard.add_comment(__('Muslim Employee'), 'green', true);
    }
    
    // Show leave balances if available
    if (frm.doc.annual_leave_balance > 0) {
        frm.dashboard.add_comment(__('Annual Leave Balance: ' + frm.doc.annual_leave_balance + ' days'), 'info', true);
    }
    if (frm.doc.sick_leave_balance > 0) {
        frm.dashboard.add_comment(__('Sick Leave Balance: ' + frm.doc.sick_leave_balance + ' days'), 'info', true);
    }
    
    // Show testing period info
    if (frm.doc.remaining_testing_days > 0) {
        frm.dashboard.add_comment(__('Testing Period: ' + frm.doc.remaining_testing_days + ' days remaining'), 'warning', true);
    }
}

function show_employee_details(frm) {
    if (frm.doc.date_of_joining) {
        calculate_working_period(frm);
    }
    
    if (frm.doc.contract_end_date) {
        calculate_contract_days_remaining(frm);
    }
    
    if (frm.doc.date_of_joining && !frm.doc.testing_period_end_date) {
        check_testing_period(frm);
    }
}
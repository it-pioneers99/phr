frappe.pages['attendance_penalty_setup'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Attendance Penalty Setup'),
        single_column: true
    });

    // Add refresh button
    page.add_inner_button(__('Refresh'), function() {
        load_penalty_setup_status(page);
    });

    // Add setup button
    page.add_inner_button(__('Setup Penalty Types'), function() {
        setup_penalty_types(page);
    }, __('Actions'));

    // Add view penalties button
    page.add_inner_button(__('View Penalty Records'), function() {
        frappe.set_route('List', 'Penalty Record');
    }, __('Actions'));

    // Add employee summary button
    page.add_inner_button(__('Employee Summary'), function() {
        show_employee_summary_dialog(page);
    }, __('Reports'));

    // Initial load
    load_penalty_setup_status(page);
}

function load_penalty_setup_status(page) {
    frappe.call({
        method: 'phr.phr.page.attendance_penalty_setup.attendance_penalty_setup.get_penalty_setup_status',
        callback: function(r) {
            if (r.message) {
                render_penalty_setup_status(page, r.message);
            }
        }
    });
}

function render_penalty_setup_status(page, data) {
    let html = `
        <div class="penalty-setup-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <h3>${__('Penalty Types Configuration')}</h3>
                    ${render_penalty_types_status(data)}
                </div>
            </div>
            
            <div class="row" style="margin-top: 30px;">
                <div class="col-md-12">
                    <h3>${__('Penalty Statistics (Last 30 Days)')}</h3>
                    ${render_penalty_stats(data.penalty_stats)}
                </div>
            </div>
            
            <div class="row" style="margin-top: 30px;">
                <div class="col-md-12">
                    <h3>${__('Recent Penalty Records')}</h3>
                    ${render_recent_penalties(data.recent_penalties)}
                </div>
            </div>
        </div>
        
        <style>
            .penalty-setup-dashboard {
                padding: 20px;
            }
            
            .penalty-type-card {
                border: 1px solid #d1d8dd;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 10px;
                background: #f8f9fa;
            }
            
            .penalty-type-card.configured {
                background: #d4edda;
                border-color: #c3e6cb;
            }
            
            .penalty-type-card.not-configured {
                background: #f8d7da;
                border-color: #f5c6cb;
            }
            
            .stat-card {
                border: 1px solid #d1d8dd;
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                margin-bottom: 10px;
            }
            
            .stat-value {
                font-size: 32px;
                font-weight: bold;
                color: #36414c;
            }
            
            .stat-label {
                font-size: 14px;
                color: #6c757d;
                margin-top: 5px;
            }
            
            .penalty-record-row {
                border-bottom: 1px solid #e9ecef;
                padding: 10px 0;
            }
            
            .penalty-record-row:last-child {
                border-bottom: none;
            }
        </style>
    `;
    
    page.$body.html(html);
}

function render_penalty_types_status(data) {
    let html = '';
    
    if (data.penalty_types_configured) {
        html += `
            <div class="alert alert-success">
                <i class="fa fa-check-circle"></i> 
                ${__('All attendance penalty types are configured properly!')}
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-warning">
                <i class="fa fa-exclamation-triangle"></i> 
                ${__('Some attendance penalty types are missing. Click "Setup Penalty Types" to configure them.')}
            </div>
        `;
    }
    
    const required_types = [
        "Late Arrival 15-30 Minutes",
        "Late Arrival 30-45 Minutes",
        "Late Arrival 45-75 Minutes",
        "Late Arrival Over 75 Minutes",
        "Early Departure Before 15 Minutes"
    ];
    
    required_types.forEach(function(type) {
        const exists = data.penalty_types.find(pt => pt.penalty_type === type);
        html += `
            <div class="penalty-type-card ${exists ? 'configured' : 'not-configured'}">
                <strong>${type}</strong>
                ${exists ? 
                    `<span class="badge badge-success pull-right">${__('Configured')}</span>` : 
                    `<span class="badge badge-danger pull-right">${__('Not Configured')}</span>`
                }
            </div>
        `;
    });
    
    return html;
}

function render_penalty_stats(stats) {
    if (!stats || stats.length === 0) {
        return `<p class="text-muted">${__('No penalty records in the last 30 days.')}</p>`;
    }
    
    let html = '<div class="row">';
    
    stats.forEach(function(stat) {
        html += `
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-value">${stat.count}</div>
                    <div class="stat-label">${stat.penalty_status || 'Draft'}</div>
                    <div class="stat-label">
                        ${frappe.format(stat.total_amount || 0, {fieldtype: 'Currency'})}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function render_recent_penalties(penalties) {
    if (!penalties || penalties.length === 0) {
        return `<p class="text-muted">${__('No recent penalty records.')}</p>`;
    }
    
    let html = '<div>';
    
    penalties.forEach(function(penalty) {
        html += `
            <div class="penalty-record-row">
                <div class="row">
                    <div class="col-md-3">
                        <strong>${penalty.employee}</strong>
                    </div>
                    <div class="col-md-3">
                        ${penalty.violation_type}
                    </div>
                    <div class="col-md-2">
                        ${frappe.datetime.str_to_user(penalty.violation_date)}
                    </div>
                    <div class="col-md-2">
                        ${frappe.format(penalty.penalty_amount || 0, {fieldtype: 'Currency'})}
                    </div>
                    <div class="col-md-2">
                        <span class="badge badge-${get_status_badge_color(penalty.penalty_status)}">
                            ${penalty.penalty_status}
                        </span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function get_status_badge_color(status) {
    const colors = {
        'Draft': 'secondary',
        'Submitted': 'info',
        'Approved': 'success',
        'Rejected': 'danger'
    };
    return colors[status] || 'secondary';
}

function setup_penalty_types(page) {
    frappe.confirm(
        __('This will create or update all 5 attendance penalty types based on Saudi Labor Law. Continue?'),
        function() {
            frappe.call({
                method: 'phr.phr.utils.attendance_penalty_detector.setup_attendance_penalty_types',
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Penalty types setup completed successfully!'),
                            indicator: 'green'
                        });
                        load_penalty_setup_status(page);
                    }
                }
            });
        }
    );
}

function show_employee_summary_dialog(page) {
    let dialog = new frappe.ui.Dialog({
        title: __('Employee Penalty Summary'),
        fields: [
            {
                fieldname: 'employee',
                fieldtype: 'Link',
                label: __('Employee'),
                options: 'Employee'
            },
            {
                fieldname: 'col_break_1',
                fieldtype: 'Column Break'
            },
            {
                fieldname: 'from_date',
                fieldtype: 'Date',
                label: __('From Date'),
                default: frappe.datetime.add_months(frappe.datetime.get_today(), -3)
            },
            {
                fieldname: 'to_date',
                fieldtype: 'Date',
                label: __('To Date'),
                default: frappe.datetime.get_today()
            },
            {
                fieldname: 'section_break_1',
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'summary_html',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: __('Get Summary'),
        primary_action: function() {
            const values = dialog.get_values();
            
            frappe.call({
                method: 'phr.phr.page.attendance_penalty_setup.attendance_penalty_setup.get_employee_penalty_summary',
                args: {
                    employee: values.employee,
                    from_date: values.from_date,
                    to_date: values.to_date
                },
                callback: function(r) {
                    if (r.message) {
                        render_employee_summary(dialog, r.message);
                    }
                }
            });
        }
    });
    
    dialog.show();
}

function render_employee_summary(dialog, data) {
    if (!data || data.length === 0) {
        dialog.fields_dict.summary_html.$wrapper.html(`
            <p class="text-muted">${__('No penalty records found for the selected criteria.')}</p>
        `);
        return;
    }
    
    let html = '<table class="table table-bordered">';
    html += `
        <thead>
            <tr>
                <th>${__('Employee')}</th>
                <th>${__('Violation Type')}</th>
                <th>${__('Occurrences')}</th>
                <th>${__('Total Amount')}</th>
                <th>${__('Last Violation')}</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    data.forEach(function(row) {
        html += `
            <tr>
                <td>${row.employee}<br><small class="text-muted">${row.employee_name || ''}</small></td>
                <td>${row.violation_type}</td>
                <td><span class="badge badge-primary">${row.occurrence_count}</span></td>
                <td>${frappe.format(row.total_penalty_amount || 0, {fieldtype: 'Currency'})}</td>
                <td>${frappe.datetime.str_to_user(row.last_violation_date)}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    
    dialog.fields_dict.summary_html.$wrapper.html(html);
}


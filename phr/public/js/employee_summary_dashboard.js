/**
 * PHR Employee Summary Dashboard
 * Provides interactive dashboard for employee leave and test period management
 */

frappe.provide("phr.employee_summary");

phr.employee_summary.EmployeeSummaryDashboard = class {
    constructor(container) {
        this.container = container;
        this.employee_id = null;
        this.data = null;
    }

    async load(employee_id) {
        this.employee_id = employee_id;
        try {
            const response = await frappe.call({
                method: "phr.api.employee_summary.get_employee_summary",
                args: { employee_id: employee_id }
            });
            
            if (response.message.success) {
                this.data = response.message.data;
                this.render();
            } else {
                this.show_error(response.message.error);
            }
        } catch (error) {
            this.show_error(error.message);
        }
    }

    render() {
        if (!this.data) return;

        this.container.html(`
            <div class="employee-summary-dashboard">
                <div class="dashboard-header">
                    <h3>Employee Summary - ${this.data.employee_name}</h3>
                    <div class="action-buttons">
                        <button class="btn btn-primary btn-sm" onclick="phr.employee_summary.refreshData('${this.employee_id}')">
                            <i class="fa fa-refresh"></i> Refresh
                        </button>
                        <button class="btn btn-success btn-sm" onclick="phr.employee_summary.calculateLeaveBalance('${this.employee_id}')">
                            <i class="fa fa-calculator"></i> Calculate Leave Balance
                        </button>
                    </div>
                </div>

                <div class="dashboard-content">
                    <div class="row">
                        <!-- Years of Service -->
                        <div class="col-md-3">
                            <div class="summary-card">
                                <div class="card-header">
                                    <h4>Years of Service</h4>
                                </div>
                                <div class="card-body">
                                    <div class="metric-value">${this.data.years_of_service}</div>
                                    <div class="metric-label">Years</div>
                                </div>
                            </div>
                        </div>

                        <!-- Annual Leave -->
                        <div class="col-md-3">
                            <div class="summary-card">
                                <div class="card-header">
                                    <h4>Annual Leave</h4>
                                </div>
                                <div class="card-body">
                                    <div class="leave-progress">
                                        <div class="progress">
                                            <div class="progress-bar" style="width: ${this.data.annual_leave.percentage_used}%"></div>
                                        </div>
                                        <div class="leave-details">
                                            <div class="leave-used">Used: ${this.data.annual_leave.used} days</div>
                                            <div class="leave-remaining">Remaining: ${this.data.annual_leave.remaining} days</div>
                                            <div class="leave-allocated">Allocated: ${this.data.annual_leave.allocated} days</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Sick Leave -->
                        <div class="col-md-3">
                            <div class="summary-card">
                                <div class="card-header">
                                    <h4>Sick Leave</h4>
                                </div>
                                <div class="card-body">
                                    <div class="leave-progress">
                                        <div class="progress">
                                            <div class="progress-bar bg-warning" style="width: ${(this.data.sick_leave.used / this.data.sick_leave.allocated) * 100}%"></div>
                                        </div>
                                        <div class="leave-details">
                                            <div class="leave-used">Used: ${this.data.sick_leave.used} days</div>
                                            <div class="leave-remaining">Remaining: ${this.data.sick_leave.remaining} days</div>
                                            <div class="leave-allocated">Allocated: ${this.data.sick_leave.allocated} days</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Test Period -->
                        <div class="col-md-3">
                            <div class="summary-card ${this.getTestPeriodClass()}">
                                <div class="card-header">
                                    <h4>Test Period</h4>
                                </div>
                                <div class="card-body">
                                    <div class="test-period-info">
                                        <div class="remaining-days">${this.data.test_period.remaining_days} days</div>
                                        <div class="test-status">${this.data.test_period.status}</div>
                                        <div class="end-date">Ends: ${this.data.test_period.end_date || 'N/A'}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Sick Leave Deductions -->
                    ${this.renderSickLeaveDeductions()}

                    <!-- Test Period Alerts -->
                    ${this.renderTestPeriodAlerts()}
                </div>
            </div>
        `);

        this.addStyles();
    }

    renderSickLeaveDeductions() {
        const deductions = this.data.sick_leave.deductions;
        if (deductions.total_deduction_amount === 0) {
            return '';
        }

        return `
            <div class="row mt-3">
                <div class="col-12">
                    <div class="summary-card">
                        <div class="card-header">
                            <h4>Sick Leave Salary Deductions</h4>
                        </div>
                        <div class="card-body">
                            <div class="deduction-breakdown">
                                <div class="deduction-item">
                                    <span class="deduction-label">No Deduction (First 30 days):</span>
                                    <span class="deduction-value">${deductions.no_deduction_days} days</span>
                                </div>
                                <div class="deduction-item">
                                    <span class="deduction-label">25% Deduction (Days 31-90):</span>
                                    <span class="deduction-value">${deductions.deduction_25_percent_days} days - ${deductions.deduction_25_amount.toFixed(2)} SAR</span>
                                </div>
                                <div class="deduction-item">
                                    <span class="deduction-label">100% Deduction (Days 91+):</span>
                                    <span class="deduction-value">${deductions.deduction_100_percent_days} days - ${deductions.deduction_100_amount.toFixed(2)} SAR</span>
                                </div>
                                <div class="deduction-item total">
                                    <span class="deduction-label"><strong>Total Deduction:</strong></span>
                                    <span class="deduction-value"><strong>${deductions.total_deduction_amount.toFixed(2)} SAR</strong></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderTestPeriodAlerts() {
        if (this.data.test_period.remaining_days > 30) {
            return '';
        }

        const alertClass = this.data.test_period.remaining_days <= 7 ? 'alert-danger' : 'alert-warning';
        const message = this.data.test_period.remaining_days <= 7 
            ? 'Test period ends in less than a week!'
            : 'Test period ending soon - 30 days or less remaining';

        return `
            <div class="row mt-3">
                <div class="col-12">
                    <div class="alert ${alertClass}">
                        <i class="fa fa-exclamation-triangle"></i>
                        <strong>Test Period Alert:</strong> ${message}
                    </div>
                </div>
            </div>
        `;
    }

    getTestPeriodClass() {
        const days = this.data.test_period.remaining_days;
        if (days <= 7) return 'test-period-critical';
        if (days <= 30) return 'test-period-warning';
        return 'test-period-normal';
    }

    show_error(message) {
        this.container.html(`
            <div class="alert alert-danger">
                <i class="fa fa-exclamation-circle"></i>
                <strong>Error:</strong> ${message}
            </div>
        `);
    }

    addStyles() {
        if (document.getElementById('employee-summary-styles')) return;

        const styles = `
            <style id="employee-summary-styles">
                .employee-summary-dashboard {
                    padding: 20px;
                }
                
                .dashboard-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #ddd;
                }
                
                .summary-card {
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .card-header {
                    background: #f8f9fa;
                    padding: 15px;
                    border-bottom: 1px solid #ddd;
                    border-radius: 8px 8px 0 0;
                }
                
                .card-header h4 {
                    margin: 0;
                    color: #333;
                    font-size: 16px;
                }
                
                .card-body {
                    padding: 15px;
                }
                
                .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #007bff;
                }
                
                .metric-label {
                    color: #666;
                    font-size: 14px;
                }
                
                .leave-progress {
                    margin-bottom: 10px;
                }
                
                .progress {
                    height: 8px;
                    background-color: #e9ecef;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                
                .progress-bar {
                    background-color: #28a745;
                    border-radius: 4px;
                }
                
                .leave-details {
                    font-size: 12px;
                }
                
                .leave-used, .leave-remaining, .leave-allocated {
                    margin-bottom: 2px;
                }
                
                .test-period-critical {
                    border-left: 4px solid #dc3545;
                }
                
                .test-period-warning {
                    border-left: 4px solid #ffc107;
                }
                
                .test-period-normal {
                    border-left: 4px solid #28a745;
                }
                
                .remaining-days {
                    font-size: 20px;
                    font-weight: bold;
                    color: #333;
                }
                
                .test-status {
                    color: #666;
                    font-size: 14px;
                }
                
                .end-date {
                    color: #666;
                    font-size: 12px;
                }
                
                .deduction-breakdown {
                    margin-top: 10px;
                }
                
                .deduction-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 5px 0;
                    border-bottom: 1px solid #eee;
                }
                
                .deduction-item.total {
                    border-top: 2px solid #333;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                
                .deduction-label {
                    font-weight: 500;
                }
                
                .deduction-value {
                    color: #007bff;
                    font-weight: 500;
                }
                
                .action-buttons {
                    display: flex;
                    gap: 10px;
                }
                
                .action-buttons .btn {
                    font-size: 12px;
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
};

// Global functions for button actions
phr.employee_summary.refreshData = function(employee_id) {
    const dashboard = new phr.employee_summary.EmployeeSummaryDashboard($('#employee-summary-container'));
    dashboard.load(employee_id);
};

phr.employee_summary.calculateLeaveBalance = function(employee_id) {
    frappe.call({
        method: "phr.api.employee_summary.calculate_employee_leave_balance",
        args: { employee_id: employee_id },
        callback: function(response) {
            if (response.message.success) {
                frappe.show_alert({
                    message: 'Leave balance calculated successfully!',
                    indicator: 'green'
                });
                phr.employee_summary.refreshData(employee_id);
            } else {
                frappe.msgprint('Error: ' + response.message.error);
            }
        }
    });
};

// Initialize dashboard when page loads
$(document).ready(function() {
    if (frappe.route && frappe.route[0] === 'Employee') {
        // Add summary tab to Employee form
        frappe.ui.form.on('Employee', {
            refresh: function(frm) {
                if (frm.doc.name) {
                    frm.add_custom_button('Employee Summary', function() {
                        frappe.route_options = {
                            employee_id: frm.doc.name
                        };
                        frappe.set_route('Employee Summary');
                    });
                }
            }
        });
    }
});

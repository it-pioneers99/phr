# Attendance Penalty System - PHR App

## 📋 Overview

The Attendance Penalty System automatically detects and processes attendance violations based on Employee Checkin times compared to shift schedules. This system implements **progressive penalties** as per Saudi Labor Law, where penalties increase with repeated violations within a 180-day window.

---

## 🎯 Key Features

### 1. **Automatic Penalty Detection**
- Automatically triggered when Employee Checkin records are created
- Compares checkin times with shift start/end times
- Creates Penalty Records without manual intervention

### 2. **Progressive Penalty Levels**
- Tracks violation history for 180 days
- Increases penalty severity with each occurrence
- Resets to first level after 180 days of no violations

### 3. **Penalty Categories**

#### **Late Arrival Penalties**

| Time Range | 1st Occurrence | 2nd Occurrence | 3rd Occurrence | 4th+ Occurrence |
|------------|----------------|----------------|----------------|-----------------|
| 15-30 min  | 0% (Warning)   | 5% deduction   | 10% deduction  | 20% deduction   |
| 30-45 min  | 10% deduction  | 20% deduction  | 30% deduction  | 50% deduction   |
| 45-75 min  | 30% deduction  | 50% deduction  | 50% deduction  | 100% deduction  |
| Over 75 min| 0% (Warning)   | 100% deduction | 150% deduction | 200% deduction  |

#### **Early Departure Penalties**

| Time Range | 1st Occurrence | 2nd Occurrence | 3rd Occurrence | 4th+ Occurrence |
|------------|----------------|----------------|----------------|-----------------|
| Before 15 min | 0% (Warning) | 5% deduction  | 15% deduction  | 50% deduction   |

**Note:** Percentages are calculated based on the employee's **daily wage**.

### 4. **Salary Integration**
- Penalties automatically included in monthly salary slips
- Added as "Attendance Penalty" deduction component
- Calculated monthly based on approved penalty records

---

## 🔧 System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Employee Checkin                          │
│                   (Biometric Device)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Attendance Penalty Detector                     │
│        (phr/utils/attendance_penalty_detector.py)            │
│                                                               │
│  • Compares checkin time vs shift time                       │
│  • Determines violation type and severity                    │
│  • Counts previous occurrences (180 days)                    │
│  • Calculates penalty amount                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Penalty Record                             │
│            (Penalty Record DocType)                          │
│                                                               │
│  Fields:                                                      │
│  • Employee                                                   │
│  • Violation Date                                             │
│  • Violation Type (Penalty Type)                             │
│  • Checkin Reference                                          │
│  • Occurrence Number (1st, 2nd, 3rd, 4th)                   │
│  • Lateness/Early Minutes                                     │
│  • Penalty Amount                                             │
│  • Status (Draft/Submitted/Approved/Rejected)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Salary Slip Integration                     │
│          (phr/utils/salary_components.py)                    │
│                                                               │
│  • Fetches all approved penalties for the month              │
│  • Adds "Attendance Penalty" deduction component             │
│  • Automatically calculates total deduction                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation & Setup

### Step 1: Migrate the Database

After pulling the latest PHR app code:

```bash
cd /home/gadallah/frappe-bench
bench --site [your-site] migrate
```

This will:
- Update the Penalty Record DocType with new fields
- Create the Attendance Penalty Setup page

### Step 2: Setup Penalty Types

**Option A: Using the Setup Page (Recommended)**

1. Go to **PHR > Attendance Penalty Setup**
2. Click **"Setup Penalty Types"** button
3. Confirm the setup dialog
4. All 5 penalty types will be created automatically

**Option B: Using Console**

```bash
bench --site [your-site] console
```

```python
import frappe
from phr.phr.utils.attendance_penalty_detector import setup_attendance_penalty_types

setup_attendance_penalty_types()
frappe.db.commit()
```

### Step 3: Verify Setup

1. Go to **PHR > Attendance Penalty Setup**
2. Check that all 5 penalty types show as "Configured"
3. Review the penalty type configurations at **Penalty Type** list

### Step 4: Create Attendance Penalty Salary Component

The "Attendance Penalty" salary component should already exist. To verify:

1. Go to **HR > Salary Component**
2. Search for "Attendance Penalty"
3. If it doesn't exist, create it with:
   - **Type:** Deduction
   - **Formula:** (Auto-calculated via doc_events)

---

## 🚀 How It Works

### Automatic Flow

1. **Employee Checks In/Out**
   - Biometric device sends data to ERPNext
   - Employee Checkin record is created

2. **Penalty Detection (Automatic)**
   - System compares checkin time with shift start/end time
   - If late/early, determines violation category
   - Counts previous violations in last 180 days
   - Determines occurrence number (1st, 2nd, 3rd, 4th)
   - Calculates penalty amount based on occurrence level
   - Creates Penalty Record in "Draft" status

3. **Penalty Review (Manual)**
   - HR Manager reviews Penalty Records
   - Can edit or reject if there were valid reasons
   - Submits/Approves penalty record

4. **Salary Deduction (Automatic)**
   - When creating monthly Salary Slip
   - System fetches all approved penalties for the month
   - Adds "Attendance Penalty" deduction automatically
   - Total is deducted from net salary

---

## 📊 Usage Guide

### For HR Managers

#### Reviewing Penalty Records

1. Go to **PHR > Penalty Record** list
2. Filter by:
   - Employee
   - Date range
   - Status (Draft/Approved/Rejected)
   - Violation Type

3. Open a Penalty Record to review:
   - Employee details
   - Violation type and date
   - Checkin reference (link to actual checkin)
   - Lateness/Early minutes
   - Occurrence number
   - Calculated penalty amount

4. Actions:
   - **Approve:** Submit the record to include in salary
   - **Reject:** Change status to "Rejected" to exclude from salary
   - **Edit:** Modify penalty amount if needed (e.g., manager approved the lateness)

#### Monitoring Dashboard

Go to **PHR > Attendance Penalty Setup** to view:
- Penalty types configuration status
- Statistics for last 30 days (by status)
- Recent penalty records
- Employee penalty summaries

#### Employee Penalty Summary

1. Go to **PHR > Attendance Penalty Setup**
2. Click **"Employee Summary"** in Reports menu
3. Filter by:
   - Employee (optional - leave blank for all)
   - Date range
4. View:
   - Total occurrences by violation type
   - Total penalty amounts
   - Last violation date

### For Employees (Self-Service)

Employees can view their own penalty records:

1. Log in to ERPNext
2. Go to **Penalty Record** (if permissions allow)
3. Filter by their Employee ID
4. View violation history and amounts

---

## 🔍 Examples

### Example 1: First-Time Late Arrival (20 minutes)

**Scenario:**
- Employee: Ahmed
- Shift Start: 08:00 AM
- Check-In Time: 08:20 AM (20 minutes late)

**Result:**
- Violation Type: "Late Arrival 15-30 Minutes"
- Occurrence Number: 1 (First time)
- Penalty Type: Warning
- Penalty Amount: 0 SAR (Warning only)

### Example 2: Second-Time Late Arrival (25 minutes)

**Scenario:**
- Employee: Ahmed (same as above)
- Previous violation: 45 days ago
- Shift Start: 08:00 AM
- Check-In Time: 08:25 AM (25 minutes late)

**Result:**
- Violation Type: "Late Arrival 15-30 Minutes"
- Occurrence Number: 2 (Second time within 180 days)
- Penalty Type: Percentage Deduction
- Penalty Amount: 5% of daily wage = (5000 SAR / 30 days) * 5% = 8.33 SAR

### Example 3: Fourth-Time Late Arrival (40 minutes)

**Scenario:**
- Employee: Ahmed
- Previous violations: 3 times in last 120 days
- Shift Start: 08:00 AM
- Check-In Time: 08:40 AM (40 minutes late)

**Result:**
- Violation Type: "Late Arrival 30-45 Minutes"
- Occurrence Number: 4 (Fourth+ time)
- Penalty Type: Percentage Deduction
- Penalty Amount: 50% of daily wage = (5000 SAR / 30 days) * 50% = 83.33 SAR

### Example 4: Early Departure (25 minutes)

**Scenario:**
- Employee: Fatima
- Shift End: 05:00 PM
- Check-Out Time: 04:35 PM (25 minutes early)

**Result:**
- Violation Type: "Early Departure Before 15 Minutes"
- Occurrence Number: 1 (First time)
- Penalty Type: Warning
- Penalty Amount: 0 SAR (Warning only)

---

## ⚙️ Configuration

### Customizing Penalty Rules

If you need to modify penalty percentages or add new rules:

1. Go to **Penalty Type** list
2. Open the specific penalty type (e.g., "Late Arrival 15-30 Minutes")
3. Modify the **Penalty Levels** table:
   - Occurrence Number (1, 2, 3, 4)
   - Penalty Type Level (Warning, Percentage Deduction, Day Deduction, etc.)
   - Penalty Value Level (percentage or fixed amount)
   - Is Percentage Level (checkbox)

4. Save and submit the changes

### Adjusting 180-Day Window

The 180-day rolling window for occurrence tracking is hardcoded in:
`phr/phr/utils/attendance_penalty_detector.py`

To change it, modify the `count_previous_violations()` function:

```python
def count_previous_violations(employee, violation_type, days_back=180):
    # Change days_back parameter to desired value
    # e.g., days_back=365 for a full year
```

### Disabling Automatic Penalty Detection

If you want to disable automatic detection temporarily:

1. Edit `phr/phr/doc_events/employee_checkin_events.py`
2. Comment out the penalty detection enqueue:

```python
# frappe.enqueue(
#     detect_attendance_penalties,
#     queue='short',
#     timeout=300,
#     checkin_name=doc.name,
#     is_async=True
# )
```

3. Restart bench: `bench restart`

---

## 🐛 Troubleshooting

### Penalties Not Being Created

**Check 1: Penalty Types Setup**
- Go to **Attendance Penalty Setup**
- Verify all 5 penalty types are configured

**Check 2: Shift Assignment**
- Ensure employee has a valid shift assigned
- Check that shift has `start_time` and `end_time` configured

**Check 3: Error Log**
- Go to **Error Log** in ERPNext
- Filter by "Attendance Penalty Detector"
- Review any error messages

**Check 4: Background Jobs**
- Run: `bench doctor`
- Check if RQ workers are running
- Restart workers: `bench restart`

### Penalties Not Appearing in Salary Slip

**Check 1: Penalty Status**
- Penalties must be "Submitted" or "Approved" status
- Draft and Rejected penalties are excluded

**Check 2: Date Range**
- Verify penalty violation_date is within the salary slip's month

**Check 3: Salary Component**
- Ensure "Attendance Penalty" salary component exists
- Type must be "Deduction"

**Check 4: Doc Events Hook**
- Verify `phr/phr/doc_events/salary_slip.py` is hooked correctly
- Check `phr/phr/hooks.py` has Salary Slip doc_events

### Wrong Penalty Amount Calculated

**Check 1: Employee Salary**
- Verify employee has a valid Salary Structure Assignment
- Check that base salary is set correctly

**Check 2: Penalty Level Configuration**
- Open the Penalty Type
- Review penalty levels table
- Ensure percentages are correct

**Check 3: Occurrence Count**
- Check if previous violations exist within 180 days
- Verify occurrence number is calculated correctly

---

## 🔐 Permissions

### Recommended Role Permissions

#### HR Manager
- Full access to Penalty Record (create, read, write, submit, approve)
- Full access to Penalty Type (create, read, write, submit)
- Access to Attendance Penalty Setup page

#### HR User
- Read and create Penalty Record
- Read only for Penalty Type

#### Employee (Self-Service)
- Read only for their own Penalty Records
- No access to Penalty Type

---

## 📈 Reports

### Available Reports

1. **Attendance Penalty Setup Dashboard**
   - Path: PHR > Attendance Penalty Setup
   - Shows: Configuration status, statistics, recent penalties

2. **Employee Penalty Summary**
   - Path: PHR > Attendance Penalty Setup > Employee Summary
   - Shows: Penalties grouped by employee and violation type

3. **Penalty Record List**
   - Path: PHR > Penalty Record
   - Supports: Filtering, sorting, export to Excel

### Creating Custom Reports

You can create custom reports using Report Builder:

1. Go to **Report Builder**
2. Select **Penalty Record** as the DocType
3. Add fields:
   - Employee
   - Employee Name
   - Violation Type
   - Violation Date
   - Occurrence Number
   - Penalty Amount
   - Penalty Status

4. Add filters and save

---

## 🧪 Testing

### Manual Testing Procedure

1. **Create a Test Employee**
   - Name: Test Employee
   - Assign to a shift with known start/end times

2. **Create Test Checkin (Late)**
   - Go to Employee Checkin
   - Create new record
   - Set time 20 minutes after shift start
   - Save

3. **Verify Penalty Record Created**
   - Check Penalty Record list
   - Should see a new Draft record for the test employee
   - Occurrence Number should be 1
   - Penalty Amount should be 0 (Warning)

4. **Create Second Test Checkin (Late)**
   - Create another checkin 25 minutes late
   - Verify new Penalty Record
   - Occurrence Number should be 2
   - Penalty Amount should be 5% of daily wage

5. **Test Salary Integration**
   - Approve the penalty records
   - Create a Salary Slip for the test employee
   - Verify "Attendance Penalty" deduction appears
   - Amount should match total of approved penalties

---

## 📝 API Reference

### Python Functions

#### `process_checkin_for_penalties(checkin_doc)`
Processes an Employee Checkin for attendance penalties.

```python
from phr.phr.utils.attendance_penalty_detector import process_checkin_for_penalties
import frappe

checkin = frappe.get_doc("Employee Checkin", "EMP-CHK-001")
process_checkin_for_penalties(checkin)
```

#### `setup_attendance_penalty_types()`
Creates all 5 attendance penalty types.

```python
from phr.phr.utils.attendance_penalty_detector import setup_attendance_penalty_types

result = setup_attendance_penalty_types()
# Returns: {"created": [...], "updated": [...]}
```

#### `calculate_attendance_penalty(employee, month, year)`
Calculates total penalty amount for an employee for a specific month.

```python
from phr.phr.utils.salary_components import calculate_attendance_penalty

penalty_amount = calculate_attendance_penalty("EMP-001", 10, 2025)
# Returns: Float (total penalty amount)
```

### Frappe Whitelisted Methods

#### `get_penalty_setup_status()`
Gets penalty setup status for the dashboard.

```javascript
frappe.call({
    method: 'phr.phr.page.attendance_penalty_setup.attendance_penalty_setup.get_penalty_setup_status',
    callback: function(r) {
        console.log(r.message);
    }
});
```

#### `get_employee_penalty_summary(employee, from_date, to_date)`
Gets penalty summary for an employee or all employees.

```javascript
frappe.call({
    method: 'phr.phr.page.attendance_penalty_setup.attendance_penalty_setup.get_employee_penalty_summary',
    args: {
        employee: 'EMP-001',
        from_date: '2025-01-01',
        to_date: '2025-10-09'
    },
    callback: function(r) {
        console.log(r.message);
    }
});
```

---

## 🔄 Integration with Other Modules

### Biometric Device Integration
- Works seamlessly with real-time biometric API
- Automatically processes penalties after checkin sync
- No manual intervention required

### Shift Management
- Requires properly configured Shift Types
- Uses shift start_time and end_time for comparisons
- Supports flexible shift schedules

### Salary Processing
- Integrates with HRMS Salary Slip
- Automatic deduction calculation
- Supports custom salary components

### Leave Management
- Future enhancement: Exclude checkins with approved leave
- Future enhancement: Exclude checkins with approved shift permissions

---

## 📞 Support

For issues, questions, or feature requests:

1. Check the troubleshooting section
2. Review error logs in ERPNext
3. Contact your system administrator
4. Review the PHR app documentation

---

## 📜 License

Copyright (c) 2025, Pioneers Holding
Licensed under the same license as the PHR app.

---

## 📚 Related Documentation

- [Automatic Attendance Sync](./AUTOMATIC_ATTENDANCE_SYNC.md)
- [Real-time Biometric API Integration](./REALTIME_BIOMETRIC_API_INTEGRATION.md)
- [PHR Requirements Verification](./REQUIREMENTS_VERIFICATION_REPORT.md)

---

**Last Updated:** October 9, 2025
**Version:** 1.0.0
**Author:** PHR Development Team


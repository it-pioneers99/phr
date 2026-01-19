# PHR Comprehensive System Analysis - Complete Requirements
**Date**: January 2025  
**App**: PHR (Pioneer HR Management)  
**Status**: Analysis & Implementation Plan

---

## 📋 Table of Contents

1. [Employee Details Analysis](#1-employee-details-analysis)
2. [Leave Management System](#2-leave-management-system)
3. [Attendance & Penalties](#3-attendance--penalties)
4. [Overtime Management](#4-overtime-management)
5. [Shift Permissions](#5-shift-permissions)
6. [Loan Management](#6-loan-management)
7. [Salary Components](#7-salary-components)
8. [End of Service](#8-end-of-service)
9. [Attendance Automations](#9-attendance-automations)

---

## 1. Employee Details Analysis

### 1.1 Employee Details Dropdown
**Location**: Employee form page  
**Components**:
- Employee information
- Leave types linked to employee
- Leave allocation details
- Leave application history

**Implementation**:
- Create dropdown button in Employee form
- Show comprehensive summaries and calculations
- Real-time data refresh
- Auto-allocate leaves button

### 1.2 Leave Analysis Dependencies
**Dependencies**:
- Leave Type (is_annual_leave, is_sick_leave flags)
- Leave Allocation (current period allocations)
- Leave Period (current year/period)

**Calculations**:
- Years of service from joining date
- Annual leave allocation (21 days <5 years, 30 days >=5 years)
- Sick leave balance and usage
- Remaining testing period days

---

## 2. Leave Management System

### 2.1 Annual Leave Calculation Rules

#### Years of Service Calculation
- **Source**: Employee `date_of_joining`
- **Formula**: `(Current Date - Joining Date) / 365.25`
- **Threshold**: 5 years = 60 months

#### Annual Leave Allocation
- **< 5 years**: 21 days per year
- **>= 5 years**: 30 days per year
- **Additional Annual Leave Flag**: If `is_additional_annual_leave = 1`, always allocate 30 days

#### Daily Synchronization
- **< 5 years**: 21 days/year = 1.75 days/month
- **>= 5 years**: 30 days/year = 2.5 days/month
- **Sync frequency**: Daily background job

### 2.2 Sick Leave Calculation

#### Salary Deduction Rules
- **0-30 days**: 100% paid (0% deduction)
- **31-90 days**: 75% paid (25% deduction)
- **90+ days**: 0% paid (100% deduction)

#### Implementation
- Check `is_sick_leave` flag in Leave Type
- Calculate total sick leave days used
- Apply deduction in Salary Component
- Show in leave summary

### 2.3 Leave Type Custom Fields

#### Required Fields in Leave Type
- `is_annual_leave` (Checkbox, 0 or 1)
- `is_sick_leave` (Checkbox, 0 or 1)
- `is_muslim` (Checkbox, 0 or 1)
- `is_female` (Checkbox, 0 or 1)

### 2.4 Dynamic Leave Allocation

#### Allocation Rules Based on Leave Type Flags

**Rule 1**: `is_muslim = 1` only
- Allocate to employees where `is_muslim = 1`
- Exclude non-Muslim employees

**Rule 2**: `is_female = 1` only
- Allocate to employees where `is_female = 1`
- Exclude male employees

**Rule 3**: `is_muslim = 1` AND `is_female = 1`
- Allocate to employees where BOTH `is_muslim = 1` AND `is_female = 1`
- Most restrictive rule

**Rule 4**: `is_female = 1` AND `is_muslim = 0`
- Allocate to employees where `is_female = 1` AND `is_muslim = 0`
- Non-Muslim female employees only

**Rule 5**: `is_female = 1` (any Muslim status)
- Allocate to all female employees
- Muslim status doesn't matter

#### Automatic Allocation Trigger
- On Employee save/update
- On new employee registration
- When joining date changes
- When demographic flags change
- Manual "Reallocate Leaves" button

### 2.5 Testing Period Tracking

#### Field Requirements
- `testing_period_start_date` (Date)
- `testing_period_end_date` (Date)
- `remaining_testing_days` (Read-only, Integer)

#### Calculation Logic
```python
if testing_period_end_date > today:
    remaining_days = (testing_period_end_date - today).days
else:
    remaining_days = 0
```

### 2.6 Contract Management

#### Employee Contract Fields
- `contract_start_date` (Date)
- `contract_end_date` (Date)

#### Notification System
- **60 days before expiry**: Send notification
- **150 days before expiry**: Send reminder notification
- **Scheduled Job**: Daily check for expiring contracts

#### Implementation
- Create scheduled task
- Send email notifications
- Create notification records
- Track notification status

### 2.7 Online Present Leave Type

#### Requirements
- New leave type: "Online Present"
- **Limit**: One time per month
- **Validation**: Check if already used in current month
- **Allocation**: Automatic monthly allocation

---

## 3. Attendance & Penalties

### 3.1 Penalty Type System

#### Penalty Types (5 Types)
1. **Late Arrival 15-30 Minutes**
   - First: 0%, Second: 5%, Third: 10%, Fourth: 20%

2. **Late Arrival 30-45 Minutes**
   - First: 10%, Second: 20%, Third: 30%, Fourth: 50%

3. **Late Arrival 45-75 Minutes**
   - First: 30%, Second: 50%, Third: 50%, Fourth: 100%

4. **Late Arrival above 75 Minutes**
   - First: 0%, Second: 100%, Third: 150%, Fourth: 200%

5. **Early Left above 15 Minutes**
   - First: 0%, Second: 5%, Third: 15%, Fourth: 50%

#### Penalty Level System
- **Child Table**: Penalty Levels in Penalty Record
- **Fields**: Occurrence number, Penalty type, Penalty value
- **Reset Period**: 180 days (if no violation, reset to first level)

### 3.2 Penalty Record Creation

#### Current Issue
- Only penalty levels created, not penalty records
- Need to create BOTH penalty record AND penalty level

#### Fix Required
- When syncing employee checkin:
  1. Detect violation (late/early)
  2. Create Penalty Record
  3. Determine penalty level (check last violation within 180 days)
  4. Add Penalty Level to Penalty Record child table
  5. Link to employee

### 3.3 Attendance Penalty Integration

#### Salary Component
- **Name**: "Attendance Penalty"
- **Type**: Deduction
- **Calculation**: Sum of all penalty deductions for the month
- **Integration**: Auto-calculate in Salary Slip

#### Penalty Types Impact
- **Deduction**: Added to salary component
- **Warning**: Recorded only, no salary impact
- **Withholding Promotion**: Flag in Employee record
- **Termination**: Update Employee status to "Left"

---

## 4. Overtime Management

### 4.1 Overtime Request Doctype

#### Fields
- Employee (Link)
- Date (Date)
- Number of hours (Float)
- Reason (Text)
- Status (Select: Draft, Submitted, Approved, Rejected)

#### Business Rules
- **Minimum**: 1 hour (less than 1 hour not considered)
- **Maximum per day**: 2 hours
- **Maximum per month**: 5 hours
- **Premium**: 50% of hourly rate
- **Salary cap**: 10% of total salary
- **High earners**: > SAR 5,000 requires Executive approval

### 4.2 Overtime Allowance Calculation

#### Salary Component
- **Name**: "Overtime Allowance"
- **Type**: Earning
- **Formula**: `(Overtime Hours × Hourly Rate) × 1.5`

#### Validation
- Check daily limit (2 hours)
- Check monthly limit (5 hours)
- Check salary percentage (10% max)
- Check approval status

---

## 5. Shift Permissions

### 5.1 Shift Permission Request

#### Fields
- Employee (Link)
- Permission Type (Select: Late, Early, Out of Office)
- Date (Date)
- Number of hours (Float)
- Reason (Text)
- Status (Select: Draft, Submitted, Approved, Rejected)
- Notes (Text)

#### Business Rules
- **Minimum**: 1 hour
- **Maximum**: 4 hours per month
- **Umrah Permission**: Half day every 3 months, max 4 times/year
- **Combining**: Can combine hours (4 hours at once)

#### Leave Integration
- If excess permission: Deduct from annual leave balance
- If no leave balance: Deduct from salary (quarter/half day)
- If not approved: Apply penalty regulations

---

## 6. Loan Management

### 6.1 Loan Installment Postponement

#### Fields
- Employee (Link)
- Loan ID (Link to Loan)
- Installment to postpone (Link)
- Current installment month (Date)
- New installment month (Date, Required)
- Reason (Text)
- Status (Select: Draft, Submitted, Approved, Rejected)

#### Workflow
1. Submit request
2. Check specified installment
3. Update installment date to new month
4. Add link in Loan DocType to postponement request

### 6.2 End of Service Loan Deduction

#### Logic
- Check if employee has loan
- Fetch outstanding amount (total - paid installments)
- Deduct from EOS benefits
- If EOS < loan balance: Show alert
- Create salary component: "Loan Balance Deduction"

---

## 7. Salary Components

### 7.1 Social Insurance

#### Saudi Employee
- **Employee deduction**: 9.75% of (Basic + Housing)
- **Employer contribution**: 11.75% of (Basic + Housing)

#### Foreign Employee
- **Employee deduction**: 0%
- **Employer contribution**: 2% of (Basic + Housing)

#### Salary Subject to Insurance
- Basic Salary
- Housing Allowance
- **NOT included**: Transportation, other allowances

### 7.2 Salary Progression

#### Employee Table
- **Fields**: From Date, To Date, Salary, Document (Attach)
- **Purpose**: Track salary changes over time
- **Validation**: Document attachment mandatory

#### Implementation
- Child table in Employee doctype
- Auto-populate on salary change
- Link to salary modification document

---

## 8. End of Service

### 8.1 End of Service Settlement

#### Fields
- Employee (Link)
- Date of Appointment (Date, Auto from Employee)
- Date of End of Service (Date)
- Reason (Select: Resignation, Contract Expiry)
- Last Basic Salary (Float, Auto from Salary Component)
- Number of Years of Service (Float, Auto-calculated)
- Eligible for EOS Gratuity (Checkbox)
- Notes/Attachments (Text/File)

### 8.2 Gratuity Calculation

#### Article 84: Employer Termination
- **First 5 years**: Half salary per year
- **After 5 years**: Full salary per year
- **Partial year**: Proportional calculation
- **Base**: Last basic salary

#### Article 85: Employee Resignation
- **< 2 years**: Nothing
- **2 to < 5 years**: 1/3 of Article 84 calculation
- **5 to < 10 years**: 2/3 of Article 84 calculation
- **10+ years**: Full Article 84 calculation

### 8.3 Vacation Allowance

#### Calculation
- **First 5 years**: Half month per year
- **6+ years**: Full month per year
- **Unused days**: Compensated in EOS

### 8.4 Fingerprint Penalty
- **First time**: Quarter day deduction
- **Second time**: Half day deduction
- **Third+ times**: Full day deduction

---

## 9. Attendance Automations

### 9.1 Employee Checkin → Attendance

#### Current Implementation
- ✅ Auto-create attendance after checkin
- ✅ Check for leave/travel/shift request
- ⚠️ Need to fix: Mark as "On Leave" if in active leave period

#### Required Fix
```python
When Employee Checkin created:
    1. Check if employee has approved leave for that date
    2. If yes: Create Attendance with status "On Leave"
    3. If no: Check for travel trip
    4. If travel: Mark accordingly
    5. If shift request: Mark accordingly
    6. If none: Check for checkin/checkout
    7. If no checkin/checkout: Create draft Penalty Record
```

### 9.2 Penalty Record Creation Fix

#### Current Issue
- Only penalty levels created during sync
- Need to create Penalty Record with Penalty Level

#### Fix Required
```python
When violation detected:
    1. Create Penalty Record
    2. Determine penalty level (check last violation within 180 days)
    3. Add Penalty Level to Penalty Record child table
    4. Link to employee and violation type
```

### 9.3 Attendance Status Logic

#### Priority Order
1. **Active Leave**: Mark as "On Leave"
2. **Travel Trip**: Mark as "On Leave" or custom status
3. **Shift Request**: Mark as "Present" with permission
4. **Checkin/Checkout Present**: Mark as "Present"
5. **No Checkin/Checkout**: Create draft Penalty Record

---

## Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. ✅ Fix annual leave calculation (21/30 days, not 39)
2. ✅ Fix attendance automation (mark as leave if in leave period)
3. ✅ Fix penalty record creation (create record + level)
4. ✅ Implement is_additional_annual_leave logic

### Phase 2: Core Features (Week 1)
1. Employee Details dropdown with analysis
2. Online Present leave type
3. Contract notification system
4. Testing period tracking

### Phase 3: Advanced Features (Week 2)
1. Dynamic leave allocation based on demographics
2. Sick leave salary deduction
3. Penalty system enhancements
4. Overtime validation

### Phase 4: Integration (Week 3)
1. Salary component integrations
2. EOS calculations
3. Loan postponement
4. Shift permissions

---

## Technical Implementation Notes

### Database Relationships
- Employee → Leave Allocation (1:Many)
- Employee → Leave Application (1:Many)
- Employee → Penalty Record (1:Many)
- Employee → Overtime Request (1:Many)
- Employee → Shift Permission (1:Many)
- Employee → Loan Postponement (1:Many)
- Employee → Salary Progression (1:Many)
- Employee → EOS Settlement (1:1)

### Custom Scripts Required
1. Years of service calculation
2. Dynamic leave allocation
3. Sick leave salary calculation
4. Penalty level determination
5. Overtime allowance calculation
6. Social insurance calculation
7. EOS gratuity calculation
8. Contract notification system

### Scheduled Jobs
1. Daily leave balance sync
2. Daily contract expiry check
3. Monthly online present allocation
4. Daily attendance processing

### Validation Rules
- Leave allocation demographic matching
- Overtime limits
- Permission duration limits
- Penalty level progression
- EOS eligibility

---

## Testing Checklist

### Leave Management
- [ ] Annual leave allocation (21/30 days)
- [ ] Additional annual leave flag
- [ ] Demographic-based allocation
- [ ] Sick leave deduction calculation
- [ ] Testing period tracking
- [ ] Contract notifications

### Attendance
- [ ] Auto-attendance creation
- [ ] Leave period detection
- [ ] Penalty record creation
- [ ] Penalty level progression

### Other Modules
- [ ] Overtime validation
- [ ] Shift permissions
- [ ] Loan postponement
- [ ] EOS calculations

---

## Notes

- All calculations follow Saudi Labor Law
- Progressive penalty system with 180-day reset
- Social insurance compliance (Saudi vs Foreign)
- EOS calculation per Articles 84/85
- Comprehensive leave analysis and reporting

---

**Last Updated**: January 2025  
**Version**: 2.0  
**Status**: Active Development


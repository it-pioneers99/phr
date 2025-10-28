# PHR System Analysis - Module Integration and Implementation Plan

## Overview
This document outlines the comprehensive HR system implementation for the PHR app, covering attendance management, penalties, overtime, shift permissions, loans, and salary components with Saudi Labor Law compliance.

## Module Integration Map

### 1. ATTENDANCE & PENALTIES MODULE
**Core Components:**
- Penalty Type (Settings/Doctype) - Define penalty types per Saudi Law
- Employee Checkin Integration - Link with shift times
- Penalty Record - Track violations with progressive levels
- Salary Component Integration - "Attendance Penalty" deduction

**Data Flow:**
```
Employee Checkin → Shift Comparison → Violation Detection → Penalty Record → Salary Component
```

**Key Features:**
- Progressive penalty system (180-day reset cycle)
- Penalty levels child table
- Automatic salary deduction calculation
- Termination integration

### 2. OVERTIME MODULE
**Core Components:**
- Overtime Request Doctype
- Approval workflow
- Salary Component: "Overtime Allowance"
- Business rules validation

**Data Flow:**
```
Overtime Request → Approval → Salary Component Calculation → Salary Slip
```

**Key Features:**
- 50% premium on hourly rate
- 2 hours max per day, 5 hours max per month
- 10% salary cap
- Executive approval for high earners

### 3. SHIFT PERMISSIONS MODULE
**Core Components:**
- Shift Permission Request Doctype
- Umrah permission tracking
- Leave balance integration
- Penalty fallback

**Data Flow:**
```
Permission Request → Approval → Leave Balance Check → Salary Deduction (if needed)
```

**Key Features:**
- 1-4 hours per month limit
- Umrah: half day every 3 months
- Annual leave integration
- Penalty system fallback

### 4. LOAN MANAGEMENT MODULE
**Core Components:**
- Loan Installment Postponement Doctype
- End of Service integration
- Salary Component: "Loan Balance Deduction"
- Outstanding balance calculation

**Data Flow:**
```
Postponement Request → Approval → Schedule Update → EOS Deduction → Salary Slip
```

**Key Features:**
- Installment postponement workflow
- Automatic EOS deduction
- Financial obligation alerts
- Final salary slip integration

### 5. SALARY COMPONENTS MODULE
**Core Components:**
- Social Insurance calculations
- Salary progression tracking
- Component definitions
- Saudi vs Foreign employee handling

**Data Flow:**
```
Employee Data → Social Insurance Calculation → Salary Components → Salary Slip
```

**Key Features:**
- Saudi: 9.75% employee, 11.75% employer
- Foreign: 2% employer only
- Salary subject to insurance: Basic + Housing
- Salary progression history

### 6. END OF SERVICE MODULE
**Core Components:**
- End of Service Settlement Doctype
- Gratuity calculation (Article 84/85)
- Vacation allowance calculation
- Final salary slip generation

**Data Flow:**
```
EOS Request → Gratuity Calculation → Vacation Allowance → Final Salary Slip
```

**Key Features:**
- Article 84: Employer termination (half/full salary per year)
- Article 85: Employee resignation (1/3, 2/3, full based on years)
- Vacation compensation
- Fingerprint penalty system

## Implementation Sequence

### Phase 1: Foundation
1. Create base doctypes structure
2. Implement penalty types and settings
3. Set up salary components framework

### Phase 2: Attendance & Penalties
1. Penalty Type doctype/settings
2. Penalty Record with progressive levels
3. Employee Checkin integration
4. Salary component integration

### Phase 3: Overtime & Permissions
1. Overtime Request system
2. Shift Permission Request system
3. Approval workflows
4. Business rule validations

### Phase 4: Loan Management
1. Loan Installment Postponement
2. EOS integration
3. Outstanding balance calculations

### Phase 5: Salary & EOS
1. Social insurance calculations
2. Salary progression tracking
3. End of Service Settlement
4. Final salary slip integration

## Technical Considerations

### Database Relationships
- Employee → Penalty Records (1:Many)
- Employee → Overtime Requests (1:Many)
- Employee → Shift Permissions (1:Many)
- Employee → Loan Postponements (1:Many)
- Employee → Salary Progression (1:Many)
- Employee → EOS Settlement (1:1)

### Custom Scripts Required
1. Penalty calculation based on progressive levels
2. Overtime allowance calculation
3. Social insurance calculation
4. EOS gratuity calculation
5. Vacation allowance calculation
6. Loan balance deduction

### Integration Points
- HRMS Employee doctype
- ERPNext Salary Slip
- ERPNext Salary Structure
- ERPNext Leave Application
- ERPNext Loan doctype

### Validation Rules
- Penalty level progression (180-day reset)
- Overtime limits and approvals
- Permission duration limits
- Umrah frequency limits
- Social insurance thresholds
- EOS eligibility rules

## Compliance Notes
- All calculations follow Saudi Labor Law
- Progressive penalty system implementation
- Social insurance compliance (Saudi vs Foreign)
- EOS calculation per Articles 84/85
- Umrah permission tracking
- Fingerprint penalty system

## Testing Strategy
1. Unit tests for calculation scripts
2. Integration tests for salary slip generation
3. Workflow tests for approval processes
4. Compliance tests for Saudi Law requirements
5. End-to-end tests for complete employee lifecycle

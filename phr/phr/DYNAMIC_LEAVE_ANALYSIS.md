# Dynamic Leave Management System Analysis

## System Overview
This document outlines a comprehensive dynamic leave management system that automatically calculates and allocates leaves based on employee tenure, demographics, and leave types with real-time synchronization.

## Core Components

### 1. EMPLOYEE MANAGEMENT
**Enhanced Employee Doctype:**
- Contract End Date field
- Years of Service calculation (automatic)
- Is Muslim field (0 or 1)
- Is Female field (0 or 1)
- Testing Period tracking
- Contract notification system

### 2. LEAVE TYPE MANAGEMENT
**Enhanced Leave Type Doctype:**
- is_annual_leave (0 or 1)
- is_sick_leave (0 or 1)
- is_muslim (0 or 1)
- is_female (0 or 1)
- Dynamic allocation rules

### 3. DYNAMIC LEAVE ALLOCATION
**Automatic Allocation Logic:**
- Years < 5: 21 days annual leave
- Years >= 5: 30 days annual leave
- Sick leave: 30 days full pay, 31-90 days 75% pay, 90+ days unpaid
- Demographic-based allocation (Muslim/Female specific leaves)

### 4. LEAVE BALANCE TRACKING
**Real-time Balance Management:**
- Remaining days calculation
- Testing period tracking
- Daily synchronization
- Leave usage monitoring

## Data Flow Architecture

```
Employee Registration → Years Calculation → Leave Type Assignment → Dynamic Allocation → Balance Tracking → Salary Integration
```

## Implementation Phases

### Phase 1: Employee Enhancement
1. Add contract end date field
2. Implement years of service calculation
3. Add demographic fields (is_muslim, is_female)
4. Create testing period tracking

### Phase 2: Leave Type Enhancement
1. Add leave type flags (is_annual_leave, is_sick_leave)
2. Add demographic flags (is_muslim, is_female)
3. Implement allocation rules

### Phase 3: Dynamic Allocation System
1. Create automatic allocation logic
2. Implement years-based allocation
3. Add demographic-based filtering
4. Create daily synchronization

### Phase 4: Sick Leave Calculation
1. Implement sick leave salary calculation
2. Create salary components for deductions
3. Add sick leave balance tracking
4. Integrate with salary slip

### Phase 5: Notifications & Reports
1. Contract end date notifications
2. Leave summary reports
3. Balance tracking reports
4. Testing period alerts

## Technical Implementation

### Database Relationships
- Employee → Leave Allocation (1:Many)
- Employee → Leave Application (1:Many)
- Leave Type → Leave Allocation (1:Many)
- Employee → Contract Notifications (1:Many)

### Custom Scripts Required
1. Years of service calculation
2. Dynamic leave allocation
3. Sick leave salary calculation
4. Contract notification system
5. Leave balance synchronization

### Integration Points
- HRMS Employee doctype
- ERPNext Leave Type
- ERPNext Leave Allocation
- ERPNext Leave Application
- ERPNext Salary Slip
- PHR notification system

## Business Rules

### Annual Leave Allocation
- < 5 years service: 21 days per year
- >= 5 years service: 30 days per year
- Pro-rated allocation based on joining date

### Sick Leave Calculation
- Days 1-30: 100% salary (no deduction)
- Days 31-90: 75% salary (25% deduction)
- Days 90+: 0% salary (100% deduction)

### Demographic-based Allocation
- Muslim-specific leaves for Muslim employees
- Female-specific leaves for female employees
- Combined demographic filtering

### Contract Management
- 90-day advance notification
- Automatic contract tracking
- End of service integration

## Compliance & Validation

### Saudi Labor Law Compliance
- Annual leave entitlements
- Sick leave calculations
- Contract management
- End of service benefits

### Data Validation
- Years calculation accuracy
- Leave balance consistency
- Demographic field validation
- Contract date validation

## Testing Strategy

### Unit Tests
1. Years of service calculation
2. Leave allocation logic
3. Sick leave calculations
4. Demographic filtering

### Integration Tests
1. Employee registration flow
2. Leave application process
3. Salary slip integration
4. Notification system

### End-to-End Tests
1. Complete leave lifecycle
2. Contract management flow
3. Salary calculation accuracy
4. Report generation

## Performance Considerations

### Optimization
- Efficient years calculation
- Cached leave balances
- Optimized database queries
- Background synchronization

### Scalability
- Bulk allocation processing
- Efficient notification system
- Scalable reporting
- Performance monitoring

## Security & Permissions

### Access Control
- Role-based leave access
- Manager approval workflows
- HR admin controls
- Employee self-service

### Data Protection
- Sensitive demographic data
- Contract information security
- Leave history privacy
- Salary calculation security

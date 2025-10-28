# Automatic Attendance Sync from Employee Checkins

## Overview
The PHR app now automatically processes employee checkins from biometric devices and creates attendance records without any manual intervention.

## How It Works

### 1. **Automatic Processing**
- When the biometric sync tool creates an Employee Checkin record, the system automatically triggers attendance processing
- The processing happens asynchronously in the background to avoid blocking checkin creation
- The system identifies the employee's shift and creates the appropriate attendance record

### 2. **Processing Flow**
```
Biometric Device → Employee Checkin Created → Automatic Trigger → 
Shift Identified → Attendance Processed → Attendance Record Created
```

### 3. **Key Features**
- ✅ **Real-time Processing**: Attendance is processed immediately after checkin sync
- ✅ **Asynchronous**: Non-blocking background processing
- ✅ **Shift-aware**: Automatically identifies the correct shift for each employee
- ✅ **Error Handling**: Logs errors without blocking the checkin process
- ✅ **Bulk Processing**: Manual bulk processing available for pending checkins

## Configuration

### Prerequisites
1. **Shift Types** must have "Enable Auto Attendance" enabled
2. **Employees** must be assigned to appropriate shifts
3. **Shift Times** must be properly configured

### Enable Auto Attendance for Shifts
1. Go to: **HR > Shift Management > Shift Type**
2. Open the relevant Shift Type
3. Enable **"Enable Auto Attendance"**
4. Set the **"Process Attendance After"** time
5. Configure attendance marking rules (working hours, grace periods, etc.)
6. Save the Shift Type

## Attendance Sync Manager Page

A dedicated management page is available at: **HR > Attendance Sync Manager**

### Features:
- **Statistics Dashboard**: View real-time statistics
  - Total Checkins
  - Processed Checkins
  - Pending Checkins
  - Total Attendance Records

- **Bulk Processing**: Process any pending checkins manually
  - Select date range
  - Process all pending checkins in that period
  - View processing results

### Access the Page:
1. Navigate to: **HR → Attendance Sync Manager**
2. View current statistics
3. Use "Process Pending Checkins" to manually trigger bulk processing if needed

## Manual Bulk Processing

If you need to process checkins that were created before this feature was enabled:

### Option 1: Using the UI
1. Go to **HR → Attendance Sync Manager**
2. Click **Actions → Process Pending Checkins**
3. Select date range
4. Click **Process**

### Option 2: Using Code/Console
```python
import frappe
from phr.phr.doc_events.employee_checkin_events import bulk_process_pending_checkins

# Process all pending checkins
result = bulk_process_pending_checkins()

# Process checkins for a specific date range
result = bulk_process_pending_checkins(
    from_date='2025-01-01',
    to_date='2025-01-31'
)

print(f"Processed: {result['processed']}, Errors: {result['errors']}")
```

## Troubleshooting

### Attendance Not Being Created?

**Check these items:**

1. **Shift Type Configuration**
   - Is "Enable Auto Attendance" checked?
   - Is "Process Attendance After" set correctly?
   - Are the working hours and grace periods configured?

2. **Employee Setup**
   - Does the employee have a shift assigned?
   - Is the shift assignment active for the checkin date?
   - Is the employee status "Active"?

3. **Checkin Data**
   - Does the checkin have "Skip Auto Attendance" unchecked?
   - Is the checkin time within a valid shift period?
   - Is the checkin linked to the correct employee?

4. **Check Error Logs**
   - Go to: **Tools → Error Log**
   - Search for: "Employee Checkin Auto Attendance"
   - Review any error messages

### View Processing Logs

Check the Frappe error logs for detailed processing information:
```bash
# From bench directory
tail -f sites/[your-site]/logs/frappe.log | grep "Employee Checkin"
```

## Technical Details

### Files Created/Modified

1. **Event Handler**: `phr/phr/doc_events/employee_checkin_events.py`
   - Handles automatic attendance processing after checkin creation
   - Provides bulk processing functionality

2. **Hooks Configuration**: `phr/hooks.py`
   - Added Employee Checkin event hook

3. **Attendance Sync Manager Page**: 
   - `phr/phr/page/attendance_sync_manager/`
   - UI for monitoring and managing attendance sync

### Database Events

The system hooks into the Employee Checkin `after_insert` event:
- Automatically triggered when a new Employee Checkin is created
- Processes asynchronously to avoid blocking
- Links the attendance record back to the checkin

### Performance Considerations

- **Asynchronous Processing**: Attendance processing happens in background queue
- **Batch Processing**: Manual bulk processing handles large volumes efficiently
- **Error Resilience**: Individual checkin failures don't block others

## Benefits

1. **⚡ Zero Manual Work**: No need to manually process attendance
2. **🎯 Real-time**: Attendance records available immediately
3. **📊 Accurate**: Based on actual biometric checkin data
4. **🔄 Reliable**: Automatic retry and error handling
5. **📈 Scalable**: Handles high volumes of checkins efficiently

## Support

For issues or questions:
1. Check the Error Log in Frappe
2. Review the troubleshooting section above
3. Contact your system administrator

---

**Implementation Date**: January 2025  
**Version**: 1.0  
**Module**: PHR - Pioneer HR Management


# Attendance Penalty System - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Migrate Database
```bash
cd /home/gadallah/frappe-bench
bench --site mnc.pioneers-holding.link migrate
```

### Step 2: Setup Penalty Types

**Using Console (Fastest):**
```bash
bench --site mnc.pioneers-holding.link console
```

```python
from phr.phr.utils.attendance_penalty_detector import setup_attendance_penalty_types
setup_attendance_penalty_types()
frappe.db.commit()
exit()
```

**Or Using UI:**
1. Login to ERPNext
2. Go to **PHR > Attendance Penalty Setup**
3. Click **"Setup Penalty Types"**
4. Confirm

### Step 3: Verify Setup
1. Go to **PHR > Attendance Penalty Setup**
2. All 5 penalty types should show as "Configured" ✅

---

## ✅ That's It!

The system is now active and will automatically:
- ✅ Detect late arrivals and early departures
- ✅ Create penalty records with progressive levels
- ✅ Calculate penalties based on daily wage
- ✅ Add deductions to monthly salary slips

---

## 📝 How to Use

### For HR Managers

**Review Penalties Daily:**
1. Go to **PHR > Penalty Record**
2. Review Draft records
3. Submit to approve or Reject if valid excuse

**Monitor Dashboard:**
- Go to **PHR > Attendance Penalty Setup**
- View statistics and recent penalties

### For Employees

**Check Your Penalties:**
1. Go to **Penalty Record**
2. Filter by your Employee ID
3. View violation history

---

## 🔍 Test the System

### Quick Test Procedure

1. **Create Test Checkin:**
   ```python
   # In bench console
   import frappe
   from frappe.utils import now_datetime, add_to_date
   
   # Create a late checkin (20 minutes late)
   checkin = frappe.new_doc("Employee Checkin")
   checkin.employee = "EMP-001"  # Change to your test employee
   checkin.shift = "Day Shift"   # Change to actual shift
   checkin.time = add_to_date(now_datetime(), minutes=20)
   checkin.log_type = "IN"
   checkin.insert()
   frappe.db.commit()
   ```

2. **Wait 10 seconds** (for background job to process)

3. **Check Penalty Record:**
   - Go to **Penalty Record** list
   - You should see a new Draft record
   - Employee: EMP-001
   - Violation Type: "Late Arrival 15-30 Minutes"
   - Occurrence: 1
   - Amount: 0 (Warning for first time)

---

## 📊 Penalty Rules Reference

| Violation | 1st | 2nd | 3rd | 4th+ |
|-----------|-----|-----|-----|------|
| **Late 15-30 min** | Warning (0%) | 5% | 10% | 20% |
| **Late 30-45 min** | 10% | 20% | 30% | 50% |
| **Late 45-75 min** | 30% | 50% | 50% | 100% |
| **Late 75+ min** | Warning (0%) | 100% | 150% | 200% |
| **Early 15+ min** | Warning (0%) | 5% | 15% | 50% |

*Percentages are based on daily wage. Occurrence counts reset after 180 days.*

---

## 🐛 Troubleshooting

### Penalties Not Creating?

**Check Background Jobs:**
```bash
bench doctor
supervisorctl status all
```

**Restart if needed:**
```bash
bench restart
```

**Check Error Log:**
- Go to **Error Log** in ERPNext
- Filter: "Attendance Penalty"

### Need Help?

📖 Read full documentation: `ATTENDANCE_PENALTY_SYSTEM.md`

---

## 🎯 Next Steps

1. ✅ Test with real employees
2. ✅ Train HR team on penalty review process
3. ✅ Configure role permissions as needed
4. ✅ Create custom reports if needed

---

**Ready to go!** 🚀


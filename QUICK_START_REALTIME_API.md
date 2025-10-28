# Quick Start Guide: Real-time Biometric API

**⏱️ Setup Time**: 15 minutes  
**📊 Difficulty**: Intermediate

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Generate API Keys (2 minutes)

```bash
cd /home/gadallah/frappe-bench
bench console
```

```python
# In Frappe console
from frappe.utils.password import get_decrypted_password

# Create API user if doesn't exist
if not frappe.db.exists("User", "biometric_api@yourcompany.com"):
    user = frappe.get_doc({
        "doctype": "User",
        "email": "biometric_api@yourcompany.com",
        "first_name": "Biometric",
        "last_name": "API",
        "user_type": "System User",
        "roles": [{"role": "HR Manager"}, {"role": "API User"}]
    })
    user.insert()

# Generate keys
api_key, api_secret = frappe.generate_keys("biometric_api@yourcompany.com")

print("=" * 60)
print("SAVE THESE CREDENTIALS:")
print("=" * 60)
print(f"API Key:    {api_key}")
print(f"API Secret: {api_secret}")
print("=" * 60)
```

**Save these credentials securely!**

---

### Step 2: Test API Connection (1 minute)

```bash
# Replace with your credentials
API_KEY="your-api-key"
API_SECRET="your-api-secret"
SITE_URL="https://your-site.com"

curl -X GET "${SITE_URL}/api/method/phr.phr.api.biometric_realtime_sync.test_connection" \
  -H "Authorization: token ${API_KEY}:${API_SECRET}"
```

**Expected Response**:
```json
{
    "success": true,
    "message": "Connection successful",
    "server_time": "2025-01-27 14:30:00"
}
```

✅ If you see this, your API is working!

---

### Step 3: Test Single Attendance Push (2 minutes)

```bash
# Create a test attendance log
curl -X POST "${SITE_URL}/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log" \
  -H "Authorization: token ${API_KEY}:${API_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "TEST001",
    "timestamp": "2025-01-27 14:30:00",
    "device_id": "TEST-DEVICE",
    "log_type": "IN"
  }'
```

**Expected Response**:
```json
{
    "success": true,
    "checkin_id": "CHECKIN-2025-00001",
    "message": "Attendance logged successfully",
    "employee": "EMP-001",
    "attendance_created": true
}
```

---

### Step 4: Configure Your Biometric Device (5 minutes)

#### Option A: ZKTeco with Push Capability

1. Open device web interface: `http://{device-ip}`
2. Go to: **System → Cloud Settings**
3. Configure:
   - **Push URL**: `https://your-site.com/api/method/phr.phr.api.biometric_realtime_sync.receive_attendance_log`
   - **Method**: POST
   - **Content-Type**: application/json
   - **Header**: `Authorization: token {api_key}:{api_secret}`
4. Set push data format (JSON):
   ```json
   {
       "employee_id": "{userid}",
       "timestamp": "{timestamp}",
       "device_id": "{device_sn}",
       "log_type": "{inout}"
   }
   ```
5. Test push with a real punch

#### Option B: Use Python Script

```bash
# Download the push script
cd /home/gadallah/frappe-bench/apps/phr/examples

# Edit configuration
nano biometric_push_script.py
# Update: ERPNEXT_URL, API_KEY, API_SECRET, DEVICE_IP

# Install requirements
pip3 install pyzk requests

# Run the script
python3 biometric_push_script.py
```

The script will continuously monitor the device and push new attendance in real-time.

---

### Step 5: Verify and Monitor (5 minutes)

1. **Check Checkin Created**:
   - Navigate to: **HR → Employee Checkin**
   - Verify new checkins appearing

2. **Check Attendance Created**:
   - Navigate to: **HR → Attendance**
   - Verify attendance records auto-created

3. **Monitor Sync Logs**:
   - Navigate to: **HR → Biometric Sync Log**
   - Check for any errors

4. **View Statistics**:
   - Navigate to: **HR → Attendance Sync Manager**
   - View real-time sync statistics

---

## 📊 Verification Checklist

- [ ] API keys generated
- [ ] Test connection successful
- [ ] Test attendance push successful
- [ ] Device configured to push data
- [ ] Real attendance log tested
- [ ] Checkin created in ERPNext
- [ ] Attendance auto-created
- [ ] Sync logs showing success
- [ ] No errors in Biometric Sync Log

---

## 🔥 Common Issues

### Issue 1: 401 Unauthorized
**Solution**: Check API key/secret are correct and properly formatted

### Issue 2: Missing required fields
**Solution**: Verify JSON format and all required fields (employee_id, timestamp, device_id)

### Issue 3: Employee not found
**Solution**: Ensure employee's `attendance_device_id` matches biometric device ID

### Issue 4: Attendance not created
**Solution**: 
- Check shift type has "Enable Auto Attendance" enabled
- Verify employee has active shift assignment
- Check background workers are running: `bench doctor`

---

## 📞 Need Help?

1. **Check Logs**:
   ```bash
   tail -f sites/[your-site]/logs/frappe.log
   ```

2. **Check Sync Logs**:
   - HR → Biometric Sync Log

3. **Test with Script**:
   ```bash
   cd /home/gadallah/frappe-bench/apps/phr/examples
   ./test_api.sh
   ```

4. **Review Documentation**:
   - Full Guide: `REALTIME_BIOMETRIC_API_INTEGRATION.md`

---

## 🎉 You're Done!

Your biometric devices are now pushing attendance data in real-time!

**What Happens Now**:
1. Employee punches in/out on device
2. Device immediately sends data to ERPNext (< 1 second)
3. Employee Checkin created automatically
4. Attendance record created automatically
5. All in real-time, no manual intervention!

---

**Next Steps**:
- Configure remaining devices
- Set up monitoring alerts
- Train HR staff on new system
- Disable old polling tool (optional)

---

*For detailed documentation, see: `REALTIME_BIOMETRIC_API_INTEGRATION.md`*


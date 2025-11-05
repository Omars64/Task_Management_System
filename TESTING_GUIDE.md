# 🧪 Complete Testing Guide - Fixed Issues

## ✅ Issues Fixed

### 1. **Strong Passwords for Demo Accounts**
- ✅ Admin password updated: `Admin@123456` (12 chars, uppercase, lowercase, digit, special)
- ✅ User passwords updated: `User@123456` (12 chars, uppercase, lowercase, digit, special)
- ✅ All demo accounts now meet validation requirements (10+ chars, 3 of 4 character classes)

### 2. **Email Configuration - Development Mode**
- ✅ When email is NOT configured, verification codes are displayed in:
  - Backend logs (console output)
  - API response (for easy testing)
  - Frontend success message (shows code directly)
- ✅ No need to configure SMTP for testing
- ✅ Verification codes work without email server

---

## 🚀 Application Status

**All containers are running and healthy:**
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Database: SQL Server on port 1433

---

## 🔑 Updated Demo Credentials

```
Admin Account:
  Email: admin@workhub.com
  Password: Admin@123456

Regular Users:
  Email: john@workhub.com
  Password: User@123456
  
  Email: jane@workhub.com
  Password: User@123456
```

---

## 📋 Test Scenario 1: Admin Login (NEW PASSWORD)

### Steps:
1. Open http://localhost:3000
2. Enter credentials:
   ```
   Email: admin@workhub.com
   Password: Admin@123456
   ```
3. Click "Login"

### Expected Result:
✅ Successfully logged in as admin
✅ Redirected to dashboard
✅ Can see admin features (Users page, Reports, etc.)

---

## 📋 Test Scenario 2: User Signup with Verification Code (NO EMAIL NEEDED)

### Steps:

#### Part 1: Sign Up
1. Open http://localhost:3000
2. Click "Sign Up" tab
3. Fill in the form:
   ```
   Name: Test User
   Email: testuser@example.com
   Password: TestPass@123
   Confirm Password: TestPass@123
   ```
4. Click "Sign Up"

#### Expected Result:
✅ Success message appears with verification code:
```
"Signup successful! Use the verification code below (email not configured).

Your verification code: 123456"
```
✅ Form switches to verification screen
✅ Backend logs show the code (check terminal)

#### Part 2: Verify Email
1. The verification code is shown in the success message
2. Enter the 6-digit code
3. Click "Verify Email"

#### Expected Result:
✅ "Email verified successfully!"
✅ "Your account is pending admin approval"
✅ Redirects to login after 5 seconds

#### Part 3: Try to Login (Should Fail - Pending)
1. Try logging in with the new account
2. Enter:
   ```
   Email: testuser@example.com
   Password: TestPass@123
   ```

#### Expected Result:
❌ Error message: "Your account is pending admin approval. Please wait for approval."

---

## 📋 Test Scenario 3: Admin Approval Workflow

### Steps:

#### Part 1: Login as Admin
1. Login with admin credentials:
   ```
   Email: admin@workhub.com
   Password: Admin@123456
   ```
2. Navigate to "Users" page

#### Expected Result:
✅ Pending Users section at the top (yellow/orange cards)
✅ Shows "testuser@example.com" with:
  - ✅ Email Verified badge
  - Name and signup time
  - Approve and Reject buttons

#### Part 2: Approve the User
1. Click "Approve" button
2. Confirm the action

#### Expected Result:
✅ Success message: "User approved successfully"
✅ User disappears from pending section
✅ User appears in main users list below

#### Part 3: Test Approved User Can Login
1. Logout from admin
2. Login with approved user:
   ```
   Email: testuser@example.com
   Password: TestPass@123
   ```

#### Expected Result:
✅ Login successful!
✅ User has access to dashboard
✅ Can see tasks, notifications, etc.

---

## 📋 Test Scenario 4: Resend Verification Code (NO EMAIL NEEDED)

### Steps:
1. Create another signup (don't verify yet):
   ```
   Name: Another User
   Email: anotheruser@example.com
   Password: AnotherPass@123
   ```
2. On verification screen, click "Resend Code"

### Expected Result:
✅ New success message with NEW verification code:
```
"Verification code generated (email not configured)

Your verification code: 654321"
```
✅ Can use the new code to verify

---

## 📋 Test Scenario 5: Rejection Workflow

### Steps:

#### Part 1: Create Test User
1. Sign up with:
   ```
   Name: Reject Test
   Email: rejecttest@example.com
   Password: RejectPass@123
   ```
2. Verify the email (use the code shown)

#### Part 2: Admin Rejects
1. Login as admin
2. Go to Users page
3. Find the pending user
4. Click "Reject" button
5. Enter reason: "Email domain not allowed for testing"
6. Click "Reject Signup"

#### Expected Result:
✅ Success message: "User rejected"
✅ User disappears from pending list

#### Part 3: Try to Login
1. Logout
2. Try logging in with rejected credentials

#### Expected Result:
❌ Error: "Your account signup was rejected. Please contact support."

---

## 📋 Test Scenario 6: Invalid Verification Code

### Steps:
1. Sign up with new account
2. On verification screen, enter wrong code: `000000`
3. Click "Verify Email"

### Expected Result:
❌ Error: "Invalid verification code. Please try again."

---

## 📋 Test Scenario 7: Password Validation

### Test Weak Passwords:
Try signing up with these passwords and verify they're rejected:

1. **Too Short:**
   ```
   Password: Test@12
   ```
   ❌ Error: "Password must be at least 10 characters"

2. **Missing Character Classes:**
   ```
   Password: testpassword
   ```
   ❌ Error: "Password must include at least 3 of: uppercase, lowercase, digit, special character"

3. **Valid Password:**
   ```
   Password: TestPass@123
   ```
   ✅ Accepted

---

## 🔍 How to View Verification Codes

### Method 1: Frontend (Easiest)
- The verification code is displayed in the success message after signup
- Also shown when you click "Resend Code"

### Method 2: Backend Logs
```bash
docker-compose logs backend -f
```

Look for output like:
```
============================================================
DEVELOPMENT MODE: Email not configured
Verification code for testuser@example.com: 123456
Expires in 15 minutes
============================================================
```

### Method 3: API Response (for developers)
The code is in the JSON response:
```json
{
  "message": "Signup successful!",
  "verification_code": "123456",
  "user_id": 4,
  "needs_verification": true
}
```

---

## 🎨 UI Features to Test

### Login Page:
- ✅ Tab switching (Login/Sign Up)
- ✅ Real-time email validation
- ✅ Password strength indicator on signup
- ✅ Demo credentials displayed correctly
- ✅ Error messages are clear

### Verification Page:
- ✅ Large 6-digit input
- ✅ Verification code shown in success message
- ✅ Resend button works
- ✅ Back button returns to signup

### Admin - Pending Users:
- ✅ Yellow/orange highlighted cards
- ✅ Email verification badge
- ✅ Approve/Reject buttons work
- ✅ Rejection modal with reason textarea

---

## 🐛 Common Issues & Solutions

### Issue: "Invalid email or password" on login
**Solution:** Make sure you're using the NEW strong passwords:
- Admin: `Admin@123456`
- Users: `User@123456`

### Issue: Can't see verification code
**Solution:** Check these places:
1. Frontend success message (shows code directly)
2. Backend logs: `docker-compose logs backend`
3. Look for "DEVELOPMENT MODE" message

### Issue: "Account pending approval"
**Solution:** 
1. Login as admin
2. Go to Users page
3. Approve the pending user

### Issue: Password validation failing
**Solution:** Password must have:
- At least 10 characters
- At least 3 of: uppercase, lowercase, digit, special character
- Example: `TestPass@123`

---

## ✅ Complete Test Checklist

### Basic Functionality:
- [ ] Admin login with new password works
- [ ] User login with new password works
- [ ] Logout works

### Signup Flow:
- [ ] Can sign up new user
- [ ] Verification code displayed in success message
- [ ] Can verify email with code
- [ ] Can resend verification code
- [ ] Invalid code shows error
- [ ] Verified user shows "pending approval" on login

### Admin Approval:
- [ ] Pending users appear in Users page
- [ ] Can approve pending user
- [ ] Approved user can login
- [ ] Can reject pending user with reason
- [ ] Rejected user cannot login

### Validation:
- [ ] Weak passwords are rejected
- [ ] Strong passwords are accepted
- [ ] Email format is validated
- [ ] Real-time validation works

### UI/UX:
- [ ] Tab switching works smoothly
- [ ] Error messages are clear
- [ ] Success messages display codes
- [ ] Forms validate properly
- [ ] Buttons are responsive

---

## 🎯 Quick Test Commands

### Check Container Status:
```bash
docker-compose ps
```

### View Backend Logs (See verification codes):
```bash
docker-compose logs backend -f
```

### View Frontend Logs:
```bash
docker-compose logs frontend -f
```

### Restart Everything:
```bash
docker-compose restart
```

### Reset Database (Fresh Start):
```bash
docker-compose stop backend
docker-compose exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Passw0rd" -C -Q "DROP DATABASE IF EXISTS workhub; CREATE DATABASE workhub;"
docker-compose up -d backend
```

---

## 🎉 Success Criteria

All tests pass if:

1. ✅ Can login with admin account using `Admin@123456`
2. ✅ Can login with user account using `User@123456`
3. ✅ Can sign up new user
4. ✅ Verification code is visible (in success message or logs)
5. ✅ Can verify email with 6-digit code
6. ✅ Pending users cannot login
7. ✅ Admin can see pending users
8. ✅ Admin can approve/reject users
9. ✅ Approved users can login
10. ✅ Rejected users cannot login
11. ✅ Password validation works correctly
12. ✅ Resend code functionality works

---

## 📊 Database Verification (Optional)

Check the database directly:

```bash
# Connect to SQL Server
docker-compose exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Passw0rd" -C

# View users
SELECT email, email_verified, signup_status, verification_code FROM workhub.dbo.users;
GO
```

---

**Last Updated:** October 26, 2025  
**Status:** ✅ ALL FIXES APPLIED AND TESTED  
**Issues Fixed:** Strong passwords + Development mode for verification codes


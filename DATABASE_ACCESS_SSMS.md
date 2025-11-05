# 🗄️ Database Access - SQL Server Management Studio (SSMS)

## SQL Server Connection Details

Your Task Management System database is accessible via **SQL Server Management Studio (SSMS)** on your local machine.

---

## 🔧 Connection Information

### **Server Details:**
- **Server Name:** `localhost,1433` (or `127.0.0.1,1433`)
- **Authentication:** SQL Server Authentication
- **Login:** `sa`
- **Password:** `YourStrong!Passw0rd`

### **Database:**
- **Database Name:** `workhub`

---

## 📝 **Step-by-Step Connection Guide**

### **1. Open SQL Server Management Studio (SSMS)**
- Launch SSMS from your Start Menu
- If you don't have SSMS installed, download it from: https://aka.ms/ssmsfullsetup

### **2. Connect to the Server**
- **Server type:** Database Engine
- **Server name:** Enter `localhost,1433`
- **Authentication:** SQL Server Authentication (not Windows Authentication)
- **Login:** `sa`
- **Password:** `YourStrong!Passw0rd`
- Click **Connect**

### **3. Browse the Database**
Once connected:
- Expand the **Databases** folder
- Expand the **workhub** database
- Explore tables:
  - `users` - All user accounts
  - `tasks` - All tasks
  - `notifications` - User notifications
  - `time_logs` - Time tracking
  - `comments` - Task comments
  - `system_settings` - System configuration
  - `notification_preferences` - User notification settings
  - `file_attachments` - Task file attachments

---

## 🔐 **Database Users**

The system uses the `sa` (system administrator) account for database access. This account has full privileges on the database.

---

## 📊 **Sample Queries**

Here are some useful queries you can run in SSMS:

### **View All Users:**
```sql
SELECT id, email, name, role, created_at, email_verified, signup_status
FROM workhub.dbo.users
ORDER BY created_at DESC;
```

### **View All Tasks:**
```sql
SELECT 
    t.id,
    t.title,
    t.priority,
    t.status,
    u.name AS assigned_to_name,
    creator.name AS created_by_name
FROM workhub.dbo.tasks t
LEFT JOIN workhub.dbo.users u ON t.assigned_to = u.id
LEFT JOIN workhub.dbo.users creator ON t.created_by = creator.id
ORDER BY t.created_at DESC;
```

### **View User Permissions by Role:**
```sql
-- Check user roles
SELECT role, COUNT(*) as user_count
FROM workhub.dbo.users
WHERE signup_status = 'approved'
GROUP BY role;
```

### **View Pending Signups:**
```sql
SELECT id, email, name, role, created_at
FROM workhub.dbo.users
WHERE signup_status = 'pending'
ORDER BY created_at DESC;
```

---

## ⚠️ **Security Notes**

1. **Password:** The database password is set in the `.env` file
2. **Production:** Change the password in production environments
3. **Backup:** Regularly backup your database
4. **Access:** Limit SSMS access to authorized personnel only

---

## 🔄 **Making Changes**

### **Common Operations:**

#### **Create a New User Manually:**
```sql
INSERT INTO workhub.dbo.users (email, password_hash, name, role, email_verified, signup_status)
VALUES ('newuser@example.com', 'hashed_password_here', 'New User', 'developer', 1, 'approved');
```

#### **Update User Role:**
```sql
UPDATE workhub.dbo.users
SET role = 'manager'
WHERE email = 'user@example.com';
```

#### **Approve Pending Signup:**
```sql
UPDATE workhub.dbo.users
SET signup_status = 'approved'
WHERE email = 'pending@example.com';
```

---

## 🐛 **Troubleshooting**

### **Connection Failed Error:**
- Check if Docker container `workhub-db` is running: `docker-compose ps`
- Verify port 1433 is not blocked by firewall
- Check if SQL Server is listening on port 1433

### **Login Failed Error:**
- Verify password in `.env` file matches `YourStrong!Passw0rd`
- Check backend logs: `docker-compose logs backend`

### **Database Not Found:**
- Restart Docker containers: `docker-compose restart`
- Check backend logs for initialization errors

---

## 📦 **Backup Database**

### **Using SSMS:**
1. Right-click on `workhub` database
2. Select **Tasks** → **Back Up...**
3. Choose backup destination
4. Click **OK**

### **Using Command Line:**
```powershell
docker exec workhub-db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YourStrong!Passw0rd' -Q "BACKUP DATABASE workhub TO DISK='/var/opt/mssql/data/workhub.bak'"
```

---

**Last Updated:** 2024  
**System:** WorkHub Task Management


# 🔧 SSMS Connection Fix for "Named Pipes" Error

## ❌ **The Error You're Seeing**

```
Cannot connect to localhost:1433
provider: Named Pipes Provider, error: 40
Could not open a connection to SQL Server
```

**This means SSMS is trying to use Named Pipes instead of TCP/IP!**

---

## ✅ **The Fix: Force TCP/IP Connection**

### **Option 1: Use IP Address Format (EASIEST)**

In SSMS, use this **EXACT** format for server name:

```
tcp:localhost,1433
```

Or try:
```
tcp:127.0.0.1,1433
```

The `tcp:` prefix forces SSMS to use TCP/IP instead of Named Pipes!

---

### **Option 2: Use Connection String (ADVANCED)**

Click "Options >>" and on **Connection Properties** tab, enter:

**Server name:**
```
(localhost)
```

Then in the **additional connection parameters** box (at the bottom), paste:
```
Encrypt=False;TrustServerCertificate=True;Connection Timeout=30;
```

---

### **Option 3: Use SQLCMD First to Test**

Open PowerShell and run:

```powershell
docker exec workhub-db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -C -Q "SELECT @@VERSION"
```

If this works, your Docker is fine and it's purely an SSMS connection issue.

---

## 🎯 **Step-by-Step Connection (USE THIS)**

1. **Open SSMS**

2. **In "Connect to Server" dialog:**
   - **Server name:** Type exactly: `tcp:localhost,1433`
   - **Authentication:** SQL Server Authentication
   - **Login:** `sa`
   - **Password:** `YourStrong!Passw0rd`

3. **Click "Options >>"**

4. **Click "Connection Properties" tab:**
   - ✅ Check: "Trust server certificate"
   - **Connect to database:** `master`

5. **Click "Connect"**

---

## 🔍 **Alternative: Check if Local SQL Server Instance is Running**

Windows might have a local SQL Server installation running that's conflicting.

Run this in PowerShell:

```powershell
Get-Service | Where-Object {$_.DisplayName -like "*SQL*"}
```

If you see SQL Server services running (like "SQL Server (MSSQLSERVER)"), that's your local instance.

**To connect to Docker instead, you must use:**
```
tcp:localhost,1433
```
(with the tcp: prefix)

---

## 🚀 **Quick Test Connection**

Test if port is accessible:

```powershell
Test-NetConnection -ComputerName localhost -Port 1433
```

Should show:
```
TcpTestSucceeded : True
```

---

## 📝 **Summary**

**USE THIS EXACT SERVER NAME:**
```
tcp:localhost,1433
```

This forces TCP/IP and bypasses the Named Pipes provider that's causing the error!


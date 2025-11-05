# 📘 SSMS Connection Guide - Step by Step for SSMS 20

## 🎯 **Step-by-Step Connection Instructions**

### **Step 1: Open SQL Server Management Studio**
1. Open SSMS (SQL Server Management Studio) from your Start Menu
2. You'll see the "Connect to Server" dialog appear automatically

---

### **Step 2: Configure Basic Connection Details**

In the **Connect to Server** dialog:

1. **Server type:** Should be **"Database Engine"** (default)
   
2. **Server name:** Enter exactly this:
   ```
   127.0.0.1,1433
   ```
   
3. **Authentication:** Select **"SQL Server Authentication"** from the dropdown
   
4. **Login:** Enter:
   ```
   sa
   ```
   
5. **Password:** Enter:
   ```
   YourStrong!Passw0rd
   ```
   (Check the "Remember password" checkbox if you want)

---

### **Step 3: Enable Trust Server Certificate (CRITICAL)**

1. **Look for the "Options >>" button** at the bottom of the Connect to Server dialog
2. **Click "Options >>"** to expand advanced options
3. Now you'll see additional tabs at the top:
   - Connection Properties
   - Always Encrypt
   - Network
   - etc.

4. **Click on the "Connection Properties" tab**

5. Look for the **"Trust server certificate"** checkbox
   - ✅ **Check this box** (enable it)

6. In the same tab, set **"Connect to database:"** dropdown to:
   ```
   master
   ```

---

### **Step 4: Connect**

1. **Click "Connect"** button at the bottom of the dialog
2. You should now connect successfully! 🎉

---

## 🖼️ **Visual Guide - What It Should Look Like**

### **Before Clicking "Options >>":**
```
┌─────────────────────────────────────────────┐
│ Connect to Server                           │
├─────────────────────────────────────────────┤
│ Server type:    [Database Engine ▼]         │
│ Server name:    [127.0.0.1,1433        ]    │
│ Authentication: [SQL Server Authentication▼] │
│ Login:          [sa                     ]    │
│ Password:       [••••••••••••••••••••••]    │
│                  [☑ Remember password]       │
│                                              │
│                  [Cancel] [Options\(\ )>>] [Connect] │
└─────────────────────────────────────────────┘
```

### **After Clicking "Options >>":**
```
┌────────────────────────────────────────────────────────┐
│ Connect to Server                                      │
├────────────────────────────────────────────────────────┤
│ Server type:    [Database Engine ▼]                    │
│ Server name:    [127.0.0.1,1433                    ]   │
│ Authentication: [SQL Server Authentication▼]            │
│ Login:          [sa                                 ]   │
│ Password:       [••••••••••••••••••••••••••••••••]     │
│                  [☑ Remember password]                  │
├────────────────────────────────────────────────────────┤
│ [Connection Properties] [Always Encrypt] [Network] ...│
├────────────────────────────────────────────────────────┤
│ Connect to database:    [master ▼]                     │
│ Network protocol:       [<default>            ▼]       │
│ Network packet size:    [4096                 ]        │
│ Connection timeout:     [15                   ]        │
│ Command timeout:        [0                    ]        │
│ Encrypt connection:     [☐ checked]                    │
│ Trust server certificate: [☑ CHECK THIS!]              │
│                                          ^^^            │
│                                        CRITICAL!        │
│                                                         │
│                [Cancel] [Options(<<)] [Connect]        │
└────────────────────────────────────────────────────────┘
```

---

## ⚠️ **Troubleshooting**

### **If you still get Login failed error:**

1. **Double-check the password:**
   - Make sure it's exactly: `YourStrong!Passw0rd`
   - No extra spaces
   - Capital Y, S, P

2. **Try alternative server name:**
   - Instead of `127.0.0.1,1433` try: `localhost,1433`
   - Or just: `localhost`

3. **Check if Docker is running:**
   ```powershell
   docker ps
   ```
   You should see `workhub-db` container

4. **Verify the database container is healthy:**
   ```powershell
   docker-compose ps
   ```

---

## ✅ **After Successful Connection**

Once connected, you'll see:

1. **Object Explorer** on the left side
2. Expand: **Databases** → **workhub** → **Tables**
3. You should see tables like:
   - `users`
   - `tasks`
   - `notifications`
   - `time_logs`
   - `comments`
   - etc.

---

## 🎯 **Quick Connection String**

Alternatively, you can connect using this connection string directly:

```
Server=127.0.0.1,1433;Database=master;User Id=sa;Password=YourStrong!Passw0rd;TrustServerCertificate=True;
```

---

**Need more help?** Run `docker-compose logs database` to check container status.


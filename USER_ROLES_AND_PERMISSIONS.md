# 🔐 User Roles & Permissions Guide

## Overview

Your Task Management System has **6 user roles** with different levels of access and permissions. Each role is designed for specific use cases in an organization.

---

## 📊 Permission Matrix

| Permission | Super Admin | Admin | Manager | Team Lead | Developer | Viewer |
|-----------|-------------|-------|---------|-----------|-----------|--------|
| **Users** | | | | | | |
| Create Users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Read Users | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Update Users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Delete Users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Assign Roles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Tasks** | | | | | | |
| Create Tasks | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Read Tasks | ✅ | ✅ | ✅ | ✅ | ✅* | ✅* |
| Update Tasks | ✅ | ✅ | ✅ | ✅ | ✅** | ❌ |
| Delete Tasks | ✅ | ✅ | ✅*** | ✅*** | ❌ | ❌ |
| Assign Tasks | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Assign to Anyone | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Delete Any Task | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Reports** | | | | | | |
| View Reports | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View All Reports | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export Reports | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Settings** | | | | | | |
| View Settings | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage Settings | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **System** | | | | | | |
| Manage System | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Notifications** | | | | | | |
| Delete Notifications | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Comments** | | | | | | |
| Create Comments | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Delete Own Comments | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Delete Any Comment | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

**Notes:**
- ✅* - Can only read tasks assigned to them
- ✅** - Can only update tasks assigned to them
- ✅*** - Can only delete tasks they created

---

## 👥 Role Descriptions

### 1. **Super Admin** 👑
**Power Level: 🔴 Maximum**

**Full system control and configuration**
- ✅ Create, view, update, delete all users
- ✅ Assign any role to any user
- ✅ Full access to all tasks (create, read, update, delete)
- ✅ Assign tasks to any user
- ✅ View all reports across the organization
- ✅ Manage system settings (SMTP, email, notifications)
- ✅ System configuration and maintenance
- ✅ Delete any comments

**Typical Use Cases:**
- IT administrators
- System owners
- Platform administrators

**Restrictions:** None

---

### 2. **Admin** 👨‍💼
**Power Level: 🟠 Very High**

**Administrative access without system configuration**
- ✅ Create, view, update, delete users
- ✅ Assign any role to users
- ✅ Full access to all tasks (create, read, update, delete)
- ✅ Assign tasks to any user
- ✅ View all reports across organization
- ✅ Export reports
- ✅ Delete any comments
- ❌ Cannot manage system settings (SMTP, email config)

**Typical Use Cases:**
- Department heads
- HR administrators
- Project administrators

**Restrictions:**
- Cannot access system settings management

---

### 3. **Manager** 👔
**Power Level: 🟡 High**

**Team and project management**
- ✅ View all users in the system
- ✅ Create, read, update tasks
- ✅ Assign tasks to team members
- ✅ Delete tasks they created
- ✅ View all team reports
- ✅ Export reports
- ✅ Create and delete comments
- ✅ Manage their own notifications
- ❌ Cannot create/delete users
- ❌ Cannot assign roles
- ❌ Cannot assign to users outside their team
- ❌ Cannot delete other users' comments

**Typical Use Cases:**
- Project managers
- Department managers
- Team supervisors

**Restrictions:**
- Cannot manage users or roles
- Cannot see system settings
- Limited to team scope

---

### 4. **Team Lead** 👨‍💻
**Power Level: 🟢 Medium**

**Team coordination and task management**
- ✅ View all users
- ✅ Create, read, update tasks
- ✅ Assign tasks to team members
- ✅ Delete tasks they created
- ✅ View team reports
- ✅ Create and delete comments
- ✅ Manage their own notifications
- ❌ Cannot create/delete users
- ❌ Cannot assign roles
- ❌ Cannot export reports
- ❌ Cannot view all organization reports
- ❌ Cannot delete other users' comments

**Typical Use Cases:**
- Technical leads
- Senior developers
- Team coordinators

**Restrictions:**
- More limited than Manager
- No user management
- Limited reporting capabilities

---

### 5. **Developer** 💻
**Power Level: 🔵 Basic**

**Task execution and updates**
- ✅ Create tasks
- ✅ Read tasks assigned to them
- ✅ Update tasks assigned to them (especially status)
- ✅ View their own reports
- ✅ Create comments
- ✅ Manage their own notifications
- ❌ Cannot assign tasks
- ❌ Cannot delete tasks
- ❌ Cannot view all users
- ❌ Cannot delete comments
- ❌ Limited to own tasks and reports

**Typical Use Cases:**
- Software developers
- Task executors
- Individual contributors

**Restrictions:**
- Very limited scope
- Only sees tasks assigned to them
- Cannot manage other users or tasks

---

### 6. **Viewer** 👀
**Power Level: ⚪ Read-Only**

**Read-only access for monitoring**
- ✅ View tasks assigned to them
- ✅ View all users (read-only)
- ✅ View their own reports
- ✅ View system settings
- ❌ Cannot create, update, or delete tasks
- ❌ Cannot manage users
- ❌ Cannot create comments
- ❌ Cannot export reports
- ❌ Cannot manage notifications

**Typical Use Cases:**
- Stakeholders
- Executives needing visibility
- External observers
- Auditors

**Restrictions:**
- Completely read-only access
- No write operations allowed

---

## 🔍 Permission Details

### **Task Access Control**
- **Read Access**: Without `TASKS_READ` permission, users can only see tasks assigned to them
- **Update Access**: Regular users can only update tasks assigned to them (mainly status changes)
- **Create Access**: Developers and above can create tasks
- **Assign Access**: Managers and above can assign tasks
- **Delete Access**: Only creators can delete their tasks, unless they have `TASKS_DELETE_ANY`

### **User Access Control**
- **Read Access**: Viewers, Managers, and Admins can see user list
- **Create Access**: Only Admins and Super Admins can create users
- **Assign Roles**: Only Admins and Super Admins can change user roles

### **Reporting Access**
- **Personal Reports**: All roles except Viewer can view their own reports
- **All Reports**: Managers and above can view team/company-wide reports
- **Export**: Managers and above can export reports

### **Comment Access**
- **Create**: All roles except Viewer can create comments
- **Delete Own**: Managers, Team Leads, and above can delete their own comments
- **Delete Any**: Only Admins and Super Admins can delete any comment

---

## 🎯 Choosing the Right Role

### **For Individual Contributors**
→ **Developer** - Allows them to update their assigned tasks and track progress

### **For Team Coordination**
→ **Team Lead** - Can assign tasks and manage team workflow

### **For Project Management**
→ **Manager** - Full team management with reporting capabilities

### **For Administrators**
→ **Admin** - User and task management without system access

### **For System Owners**
→ **Super Admin** - Full system control and configuration

### **For Observers**
→ **Viewer** - Read-only access for monitoring

---

## 🚨 Security Notes

1. **Super Admin** should be used sparingly - assign to very few trusted individuals
2. **Role Changes** require Admin or Super Admin permissions
3. **Task Deletion** - Even Admins can only delete tasks they created (unless they have special permission)
4. **Reports** - Ensure sensitive data in reports is appropriately restricted
5. **Default Role** - New users default to `viewer` until explicitly promoted

---

## 📝 Best Practices

1. **Principle of Least Privilege**: Assign the minimum role needed for the user's job
2. **Regular Audits**: Periodically review user roles and permissions
3. **Role Templates**: Use predefined roles rather than custom permission combinations
4. **Access Reviews**: Regularly review who has admin or super admin access

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**System:** WorkHub Task Management


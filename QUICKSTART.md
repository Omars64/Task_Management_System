# Work Hub - Quick Start Guide

Get up and running with Work Hub in under 5 minutes!

## 🚀 Fastest Way: Docker (Recommended)

### Prerequisites
- Docker Desktop installed
- 5 GB free disk space

### Steps

1. **Open Terminal** and navigate to the project:
   ```bash
   cd /workspace
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

3. **Wait for services to start** (about 1-2 minutes)

4. **Open your browser**:
   - Go to: http://localhost:3000

5. **Login** with demo credentials:
   - **Admin**: `admin@workhub.com` / `admin123`
   - **User**: `john@workhub.com` / `user123`

That's it! 🎉

## 🛠️ Alternative: Manual Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8.0+

### Backend Setup (5 minutes)

```bash
# 1. Navigate to backend
cd workhub-backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
cp .env.example .env
# Edit .env with your MySQL credentials

# 5. Initialize database
python init_db.py

# 6. Run server
python app.py
```

Backend will run on: http://localhost:5000

### Frontend Setup (5 minutes)

**Open a NEW terminal**:

```bash
# 1. Navigate to frontend
cd workhub-frontend

# 2. Install dependencies
npm install

# 3. Run development server
npm run dev
```

Frontend will run on: http://localhost:3000

## 📱 Using the Application

### As Admin

1. **Login**: Use `admin@workhub.com` / `admin123`

2. **Create a User**:
   - Go to "Users" in sidebar
   - Click "Add User"
   - Fill in details

3. **Create a Task**:
   - Go to "Tasks"
   - Click "Create Task"
   - Assign to a user

4. **View Reports**:
   - Go to "Reports"
   - See system-wide statistics
   - Export to CSV

5. **Configure Settings**:
   - Go to "Settings"
   - Update system settings

### As User

1. **Login**: Use `john@workhub.com` / `user123`

2. **View Your Tasks**:
   - Go to "Tasks"
   - See only assigned tasks

3. **Update Task Status**:
   - Click on a task
   - Change status dropdown
   - View task details

4. **Check Notifications**:
   - Click "Notifications"
   - See task assignments
   - Mark as read

5. **View Your Reports**:
   - Go to "Reports"
   - See personal statistics

## 🎯 Key Features to Try

### Task Management
- ✅ Create tasks with priority levels
- ✅ Assign tasks to users
- ✅ Set due dates
- ✅ Update task status
- ✅ Filter and search tasks

### Notifications
- ✅ Automatic notifications on task assignment
- ✅ Mark as read/unread
- ✅ Clear all notifications

### Reports
- ✅ Task status overview
- ✅ Activity tracking
- ✅ Sprint summaries (Admin)
- ✅ CSV export

### Settings
- ✅ Personal theme settings
- ✅ Language preferences
- ✅ Notification preferences
- ✅ System configuration (Admin)

## 🔧 Common Commands

### Docker

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend
```

### Manual Setup

```bash
# Backend (Terminal 1)
cd workhub-backend
source venv/bin/activate
python app.py

# Frontend (Terminal 2)
cd workhub-frontend
npm run dev
```

## 🐛 Troubleshooting

### Port Already in Use

**Problem**: Port 3000 or 5000 already in use

**Solution**:
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:5000 | xargs kill -9  # Backend
```

### Database Connection Error

**Problem**: Can't connect to MySQL

**Solution**:
1. Ensure MySQL is running:
   ```bash
   docker-compose ps  # Docker
   # or
   sudo systemctl status mysql  # Linux
   ```

2. Check credentials in `.env` file

3. Test connection:
   ```bash
   mysql -h localhost -u root -p
   ```

### Frontend Won't Load

**Problem**: Frontend shows blank page

**Solution**:
1. Clear browser cache
2. Check browser console for errors
3. Ensure backend is running on port 5000
4. Check API proxy in `vite.config.js`

### Module Not Found

**Problem**: Python/Node modules not found

**Solution**:
```bash
# Backend
pip install -r requirements.txt

# Frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Next Steps

1. **Read Full Documentation**: Check `README.md`
2. **Explore API**: See `PROJECT_STRUCTURE.md`
3. **Deploy to Production**: Read `DEPLOYMENT.md`
4. **Customize**: Modify code to fit your needs

## 🎓 Learning Resources

### Understand the Code

- **Backend**: `workhub-backend/app.py` - Start here
- **Frontend**: `workhub-frontend/src/App.jsx` - Main component
- **Database**: `workhub-backend/models.py` - Data models
- **API**: `workhub-backend/tasks.py` - Example routes

### Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@workhub.com","password":"admin123"}'

# Get tasks (use token from login)
curl http://localhost:5000/api/tasks/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 💡 Tips

1. **Use Demo Accounts**: Don't create new accounts initially, use provided demo accounts
2. **Check Logs**: If something breaks, check Docker/console logs
3. **Browser DevTools**: Use Network tab to debug API calls
4. **Database GUI**: Use MySQL Workbench or phpMyAdmin to inspect data

## ✨ Demo Workflow

Try this complete workflow:

1. **Login as Admin** (`admin@workhub.com`)
2. **Create a new user** (Users page)
3. **Create a task** and assign it to the new user (Tasks page)
4. **Logout** and **login as the new user**
5. **See the notification** about task assignment
6. **Update task status** to "In Progress"
7. **Logout** and **login as Admin** again
8. **View reports** to see the task statistics
9. **Export report** to CSV

## 🎉 You're Ready!

You now have a fully functional task management system. Explore the features, read the code, and customize it to your needs!

### Need Help?

- 📖 Documentation: `README.md`
- 🏗️ Architecture: `PROJECT_STRUCTURE.md`
- 🚀 Deployment: `DEPLOYMENT.md`
- 📊 Database Schema: See `models.py`

---

Happy task managing! 🚀
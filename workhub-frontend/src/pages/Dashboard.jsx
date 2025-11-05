import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { tasksAPI, reportsAPI, projectsAPI, usersAPI } from '../services/api';
import { FiCheckSquare, FiClock, FiTrendingUp, FiUsers, FiFolder } from 'react-icons/fi';
import './Dashboard.css';

const Dashboard = () => {
  const { user, isAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentTasks, setRecentTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [projectsCount, setProjectsCount] = useState(0);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      const role = (user?.role || '').toLowerCase();
      // Always rely on backend scoping for tasks, then aggregate on client
      const allTasksRes = await tasksAPI.getAll();
      const allTasks = Array.isArray(allTasksRes.data) ? allTasksRes.data : [];
      setRecentTasks(allTasks.slice(0, 5));
      const counts = allTasks.reduce((acc, t) => {
        acc.total += 1;
        acc[t.status] = (acc[t.status] || 0) + 1;
        return acc;
      }, { total: 0, todo: 0, in_progress: 0, completed: 0 });
      if (role === 'super_admin' || role === 'admin') {
        // Global view
        setStats({ status_counts: { ...counts }, user_stats: { total: (await usersAPI.getAll().then(r=>r.data.length).catch(()=>0)) } });
        const { data: projects } = await projectsAPI.getAll().catch(()=>({ data: [] }));
        setProjectsCount(Array.isArray(projects) ? projects.length : 0);
      } else if (role === 'manager' || role === 'team_lead') {
        // Project-scoped handled by backend tasks scope; still show project count for their projects
        setStats({ status_counts: { ...counts } });
        const { data: myProjects } = await projectsAPI.getMine().catch(()=>({ data: [] }));
        setProjectsCount(Array.isArray(myProjects) ? myProjects.length : 0);
      } else {
        // Developer / Viewer: assigned tasks only (backend scopes); no user count
        setStats({ total: counts.total, completed: counts.completed, in_progress: counts.in_progress, todo: counts.todo });
        // projects they see: 0 or those included in their tasks; compute unique project ids
        const pids = new Set(allTasks.map(t => t.project_id).filter(Boolean));
        setProjectsCount(pids.size);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'warning';
      case 'todo':
        return 'primary';
      default:
        return 'secondary';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'secondary';
    }
  };

  if (loading) {
    return <div className="spinner" />;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome back, {user?.name}!</h1>
        <p className="text-light">Here's an overview of your tasks</p>
      </div>

      <div className="stats-grid">
        {isAdmin() ? (
          <>
            <div className="stat-card">
              <div className="stat-icon primary">
                <FiCheckSquare />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.status_counts?.total || 0}</div>
                <div className="stat-label">Total Tasks</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon success">
                <FiTrendingUp />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.status_counts?.completed || 0}</div>
                <div className="stat-label">Completed</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon warning">
                <FiClock />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.status_counts?.in_progress || 0}</div>
                <div className="stat-label">In Progress</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon info">
                <FiUsers />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.user_stats?.total || 0}</div>
                <div className="stat-label">Total Users</div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="stat-card">
              <div className="stat-icon primary">
                <FiCheckSquare />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.total || 0}</div>
                <div className="stat-label">Total Tasks</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon success">
                <FiTrendingUp />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.completed || 0}</div>
                <div className="stat-label">Completed</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon warning">
                <FiClock />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.in_progress || 0}</div>
                <div className="stat-label">In Progress</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon danger">
                <FiCheckSquare />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stats?.todo || 0}</div>
                <div className="stat-label">To Do</div>
              </div>
            </div>
          </>
        )}
        <div className="stat-card">
          <div className="stat-icon info">
            <FiFolder />
          </div>
          <div className="stat-content">
            <div className="stat-value">{projectsCount}</div>
            <div className="stat-label">Projects</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Recent Tasks</h2>
        {recentTasks.length === 0 ? (
          <p className="text-light text-center">No tasks available</p>
        ) : (
          <div className="tasks-list">
            {recentTasks.map(task => (
              <div key={task.id} className="task-item">
                <div className="task-info">
                  <h3 className="task-title">{task.title}</h3>
                  <p className="task-description">{task.description}</p>
                  <div className="task-meta">
                    <span className={`badge badge-${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                    <span className={`badge badge-${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                    {task.assignee_name && (
                      <span className="task-assignee">
                        Assigned to: {task.assignee_name}
                      </span>
                    )}
                  </div>
                </div>
                {task.due_date && (
                  <div className="task-due-date">
                    Due: {new Date(task.due_date).toLocaleDateString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
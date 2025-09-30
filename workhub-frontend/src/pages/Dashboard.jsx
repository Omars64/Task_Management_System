import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { tasksAPI, reportsAPI } from '../services/api';
import { FiCheckSquare, FiClock, FiTrendingUp, FiUsers } from 'react-icons/fi';
import './Dashboard.css';

const Dashboard = () => {
  const { user, isAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentTasks, setRecentTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      if (isAdmin()) {
        const [overviewRes, tasksRes] = await Promise.all([
          reportsAPI.getAdminOverview(),
          tasksAPI.getAll({ limit: 5 })
        ]);
        setStats(overviewRes.data);
        setRecentTasks(tasksRes.data.slice(0, 5));
      } else {
        const [statusRes, tasksRes] = await Promise.all([
          reportsAPI.getPersonalTaskStatus(),
          tasksAPI.getAll()
        ]);
        setStats(statusRes.data.status_counts);
        setRecentTasks(tasksRes.data.slice(0, 5));
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
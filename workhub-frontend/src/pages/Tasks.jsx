import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useApiError } from '../hooks/useApiError';
import { tasksAPI, usersAPI } from '../services/api';
import { FiPlus, FiEdit2, FiTrash2, FiMessageSquare, FiX, FiClock } from 'react-icons/fi';
import './Tasks.css';

const Tasks = () => {
  const { isAdmin } = useAuth();
  const { handleApiError, handleApiSuccess } = useApiError();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showTaskDetail, setShowTaskDetail] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTimeLogModal, setShowTimeLogModal] = useState(false);
  const [timeLogs, setTimeLogs] = useState([]);
  const [timeLogForm, setTimeLogForm] = useState({
    hours: '',
    description: ''
  });
  const [commentForm, setCommentForm] = useState({
    content: ''
  });
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: ''
  });
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    status: 'todo',
    assigned_to: '',
    due_date: ''
  });

  useEffect(() => {
    fetchTasks();
    if (isAdmin()) {
      fetchUsers();
    }
  }, [filters]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.search) params.search = filters.search;
      
      const response = await tasksAPI.getAll(params);
      setTasks(response.data);
    } catch (error) {
      handleApiError(error, 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await usersAPI.getAll();
      setUsers(response.data);
    } catch (error) {
      handleApiError(error, 'Failed to fetch users');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedTask) {
        await tasksAPI.update(selectedTask.id, formData);
        handleApiSuccess('Task updated successfully');
      } else {
        await tasksAPI.create(formData);
        handleApiSuccess('Task created successfully');
      }
      setShowModal(false);
      resetForm();
      fetchTasks();
    } catch (error) {
      handleApiError(error, 'Failed to save task');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await tasksAPI.delete(id);
        handleApiSuccess('Task deleted successfully');
        fetchTasks();
      } catch (error) {
        handleApiError(error, 'Failed to delete task');
      }
    }
  };

  const handleEdit = (task) => {
    setSelectedTask(task);
    setFormData({
      title: task.title,
      description: task.description || '',
      priority: task.priority,
      status: task.status,
      assigned_to: task.assigned_to || '',
      due_date: task.due_date ? task.due_date.split('T')[0] : ''
    });
    setShowModal(true);
  };

  const handleViewDetails = async (task) => {
    try {
      const response = await tasksAPI.getById(task.id);
      setSelectedTask(response.data);
      setShowTaskDetail(true);
      // Fetch time logs for this task
      const timeLogsResponse = await tasksAPI.getTimeLogs(task.id);
      setTimeLogs(timeLogsResponse.data);
    } catch (error) {
      handleApiError(error, 'Failed to fetch task details');
    }
  };

  const handleAddTimeLog = async (e) => {
    e.preventDefault();
    try {
      await tasksAPI.addTimeLog(selectedTask.id, timeLogForm);
      handleApiSuccess('Time log added successfully');
      setTimeLogForm({ hours: '', description: '' });
      setShowTimeLogModal(false);
      // Refresh time logs
      const timeLogsResponse = await tasksAPI.getTimeLogs(selectedTask.id);
      setTimeLogs(timeLogsResponse.data);
    } catch (error) {
      handleApiError(error, 'Failed to add time log');
    }
  };

  const handleDeleteTimeLog = async (logId) => {
    if (window.confirm('Are you sure you want to delete this time log?')) {
      try {
        await tasksAPI.deleteTimeLog(logId);
        handleApiSuccess('Time log deleted successfully');
        // Refresh time logs
        const timeLogsResponse = await tasksAPI.getTimeLogs(selectedTask.id);
        setTimeLogs(timeLogsResponse.data);
      } catch (error) {
        handleApiError(error, 'Failed to delete time log');
      }
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    try {
      await tasksAPI.addComment(selectedTask.id, commentForm.content);
      handleApiSuccess('Comment added successfully');
      setCommentForm({ content: '' });
      // Refresh task details to get updated comments
      const response = await tasksAPI.getById(selectedTask.id);
      setSelectedTask(response.data);
    } catch (error) {
      handleApiError(error, 'Failed to add comment');
    }
  };

  const handleStatusUpdate = async (taskId, newStatus) => {
    try {
      await tasksAPI.update(taskId, { status: newStatus });
      handleApiSuccess('Task status updated successfully');
      fetchTasks();
    } catch (error) {
      handleApiError(error, 'Failed to update status');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      priority: 'medium',
      status: 'todo',
      assigned_to: '',
      due_date: ''
    });
    setSelectedTask(null);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'todo': return 'primary';
      default: return 'secondary';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'danger';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'secondary';
    }
  };

  return (
    <div className="tasks-page">
      <div className="page-header">
        <h1>Tasks</h1>
        {isAdmin() && (
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <FiPlus /> Create Task
          </button>
        )}
      </div>

      <div className="card">
        <div className="filters">
          <input
            type="text"
            className="form-input"
            placeholder="Search tasks..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          <select
            className="form-select"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All Status</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
          <select
            className="form-select"
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
          >
            <option value="">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        {loading ? (
          <div className="spinner" />
        ) : tasks.length === 0 ? (
          <p className="text-center text-light">No tasks found</p>
        ) : (
          <div className="tasks-grid">
            {tasks.map(task => (
              <div key={task.id} className="task-card">
                <div className="task-card-header">
                  <h3 className="task-card-title" onClick={() => handleViewDetails(task)}>
                    {task.title}
                  </h3>
                  {isAdmin() && (
                    <div className="task-actions">
                      <button className="icon-btn" onClick={() => handleEdit(task)}>
                        <FiEdit2 />
                      </button>
                      <button className="icon-btn" onClick={() => handleDelete(task.id)}>
                        <FiTrash2 />
                      </button>
                    </div>
                  )}
                </div>
                <p className="task-card-description">{task.description}</p>
                <div className="task-card-meta">
                  <span className={`badge badge-${getStatusColor(task.status)}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                  <span className={`badge badge-${getPriorityColor(task.priority)}`}>
                    {task.priority}
                  </span>
                </div>
                {task.assignee_name && (
                  <p className="task-card-assignee">Assigned to: {task.assignee_name}</p>
                )}
                {task.due_date && (
                  <p className="task-card-due">Due: {new Date(task.due_date).toLocaleDateString()}</p>
                )}
                <div className="task-card-footer">
                  <select
                    className="status-select"
                    value={task.status}
                    onChange={(e) => handleStatusUpdate(task.id, e.target.value)}
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); resetForm(); }}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{selectedTask ? 'Edit Task' : 'Create Task'}</h2>
              <button className="modal-close" onClick={() => { setShowModal(false); resetForm(); }}>
                <FiX />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Priority</label>
                  <select
                    className="form-select"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Status</label>
                  <select
                    className="form-select"
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Assign To</label>
                  <select
                    className="form-select"
                    value={formData.assigned_to}
                    onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                  >
                    <option value="">Unassigned</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>{user.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Due Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-outline" onClick={() => { setShowModal(false); resetForm(); }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {selectedTask ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Task Detail Modal */}
      {showTaskDetail && selectedTask && (
        <div className="modal-overlay" onClick={() => setShowTaskDetail(false)}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{selectedTask.title}</h2>
              <button className="modal-close" onClick={() => setShowTaskDetail(false)}>
                <FiX />
              </button>
            </div>
            <div className="task-detail">
              <div className="task-detail-section">
                <h3>Description</h3>
                <p>{selectedTask.description || 'No description'}</p>
              </div>
              <div className="task-detail-meta">
                <div>
                  <strong>Status:</strong>
                  <span className={`badge badge-${getStatusColor(selectedTask.status)}`}>
                    {selectedTask.status.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <strong>Priority:</strong>
                  <span className={`badge badge-${getPriorityColor(selectedTask.priority)}`}>
                    {selectedTask.priority}
                  </span>
                </div>
                <div>
                  <strong>Assigned to:</strong> {selectedTask.assignee_name || 'Unassigned'}
                </div>
                <div>
                  <strong>Created by:</strong> {selectedTask.creator_name || 'Unknown'}
                </div>
                {selectedTask.due_date && (
                  <div>
                    <strong>Due Date:</strong> {new Date(selectedTask.due_date).toLocaleDateString()}
                  </div>
                )}
              </div>
              <div className="task-detail-section">
                <h3><FiMessageSquare /> Comments</h3>
                
                {/* Add Comment Form */}
                <form onSubmit={handleAddComment} style={{ marginBottom: '16px' }}>
                  <div className="form-group">
                    <textarea
                      className="form-textarea"
                      value={commentForm.content}
                      onChange={(e) => setCommentForm({ content: e.target.value })}
                      placeholder="Add a comment..."
                      rows="3"
                      required
                    />
                  </div>
                  <button type="submit" className="btn btn-primary btn-sm">
                    Add Comment
                  </button>
                </form>

                {/* Comments List */}
                {selectedTask.comments && selectedTask.comments.length > 0 ? (
                  <div className="comments-list">
                    {selectedTask.comments.map(comment => (
                      <div key={comment.id} className="comment">
                        <div className="comment-header">
                          <strong>{comment.user_name}</strong>
                          <span>{new Date(comment.created_at).toLocaleString()}</span>
                        </div>
                        <p>{comment.content}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-light">No comments yet</p>
                )}
              </div>
              
              <div className="task-detail-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3><FiClock /> Time Logs</h3>
                  <button 
                    className="btn btn-primary btn-sm" 
                    onClick={() => setShowTimeLogModal(true)}
                  >
                    <FiPlus /> Add Time Log
                  </button>
                </div>
                {timeLogs.length === 0 ? (
                  <p className="text-light">No time logs recorded</p>
                ) : (
                  <div className="time-logs-list">
                    {timeLogs.map(log => (
                      <div key={log.id} className="time-log-item">
                        <div className="time-log-header">
                          <div>
                            <strong>{log.hours} hours</strong>
                            <span className="text-light" style={{ marginLeft: '8px' }}>
                              {new Date(log.logged_at).toLocaleString()}
                            </span>
                          </div>
                          <button 
                            className="icon-btn" 
                            onClick={() => handleDeleteTimeLog(log.id)}
                            style={{ color: 'var(--danger-color)' }}
                          >
                            <FiTrash2 />
                          </button>
                        </div>
                        {log.description && (
                          <p className="time-log-description">{log.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Time Log Modal */}
      {showTimeLogModal && (
        <div className="modal-overlay" onClick={() => setShowTimeLogModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Add Time Log</h2>
              <button className="modal-close" onClick={() => setShowTimeLogModal(false)}>
                <FiX />
              </button>
            </div>
            <form onSubmit={handleAddTimeLog}>
              <div className="form-group">
                <label className="form-label">Hours *</label>
                <input
                  type="number"
                  step="0.25"
                  min="0.25"
                  className="form-input"
                  value={timeLogForm.hours}
                  onChange={(e) => setTimeLogForm({ ...timeLogForm, hours: e.target.value })}
                  required
                  placeholder="Enter hours worked"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={timeLogForm.description}
                  onChange={(e) => setTimeLogForm({ ...timeLogForm, description: e.target.value })}
                  placeholder="Describe what you worked on..."
                  rows="3"
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-outline" onClick={() => setShowTimeLogModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Add Time Log
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;
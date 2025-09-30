import axios from 'axios';

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  getCurrentUser: () => api.get('/auth/me'),
  changePassword: (oldPassword, newPassword) => 
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
};

// Users API
export const usersAPI = {
  getAll: () => api.get('/users/'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

// Tasks API
export const tasksAPI = {
  getAll: (params) => api.get('/tasks/', { params }),
  getById: (id) => api.get(`/tasks/${id}`),
  create: (data) => api.post('/tasks/', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
  addComment: (id, content) => api.post(`/tasks/${id}/comments`, { content }),
};

// Notifications API
export const notificationsAPI = {
  getAll: (params) => api.get('/notifications/', { params }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  markAllAsRead: () => api.put('/notifications/mark-all-read'),
  delete: (id) => api.delete(`/notifications/${id}`),
  clearAll: () => api.delete('/notifications/clear-all'),
};

// Reports API
export const reportsAPI = {
  getPersonalTaskStatus: () => api.get('/reports/personal/task-status'),
  getPersonalTimeLogs: (days) => api.get('/reports/personal/time-logs', { params: { days } }),
  getPersonalActivity: (days) => api.get('/reports/personal/activity', { params: { days } }),
  getAdminOverview: () => api.get('/reports/admin/overview'),
  getSprintSummary: (days) => api.get('/reports/admin/sprint-summary', { params: { days } }),
  exportToCSV: (reportType) => api.post('/reports/export/csv', 
    { report_type: reportType }, 
    { responseType: 'blob' }
  ),
};

// Settings API
export const settingsAPI = {
  getSystem: () => api.get('/settings/system'),
  updateSystem: (data) => api.put('/settings/system', data),
  getPersonal: () => api.get('/settings/personal'),
  updatePersonal: (data) => api.put('/settings/personal', data),
};

export default api;
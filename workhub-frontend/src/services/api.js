import axios from 'axios';

// Resolve API base URL (root), then append '/api' consistently so routes match the backend blueprint
// Order to resolve root:
// 1) window.__API_BASE__ (runtime override)
// 2) import.meta.env.VITE_API_URL (build-time)
// 3) Hard fallback to production backend root (no trailing '/api')
// If nothing found, default to '' and axios will use current origin; we then still append '/api'
const RUNTIME_BASE = (typeof window !== 'undefined' && window.__API_BASE__) || '';
const BUILD_BASE = (import.meta?.env?.VITE_API_URL) || '';
const HARD_FALLBACK_ROOT = 'https://workhub-backend-kf6vth5ica-uc.a.run.app';

const ROOT = (RUNTIME_BASE || BUILD_BASE || HARD_FALLBACK_ROOT || '');
const API_URL = `${ROOT.replace(/\/?$/, '')}/api`;

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
  signup: (data) => api.post('/auth/signup', data),
  verifyEmail: (email, code) => api.post('/auth/verify-email', { email, code }),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),
  getPendingUsers: () => api.get('/auth/pending-users'),
  getRejectedUsers: () => api.get('/auth/rejected-users'),
  approveUser: (userId) => api.post(`/auth/approve-user/${userId}`),
  rejectUser: (userId, reason) => api.post(`/auth/reject-user/${userId}`, { reason }),
  getCurrentUser: () => api.get('/auth/me'),
  changePassword: (oldPassword, newPassword) => 
    api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
  validateEmail: (email, checkMX = true) => 
    api.post('/auth/validate-email', { email, check_mx: checkMX }),
  checkEmailExists: (email) => api.get('/auth/check-email-exists', { params: { email } }),
  checkAccountStatus: (email) => api.get('/auth/account-status', { params: { email } }),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', { token, new_password: newPassword }),
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
  addComment: (id, payload) => api.post(`/tasks/${id}/comments`, payload),
  updateComment: (taskId, commentId, payload) => api.put(`/tasks/${taskId}/comments/${commentId}`, payload),
  deleteComment: (taskId, commentId) => api.delete(`/tasks/${taskId}/comments/${commentId}`),
  addTimeLog: (id, data) => api.post(`/tasks/${id}/time-logs`, data),
  getTimeLogs: (id) => api.get(`/tasks/${id}/time-logs`),
  deleteTimeLog: (logId) => api.delete(`/tasks/time-logs/${logId}`),
  getSubtasks: (id) => api.get(`/tasks/${id}/subtasks`),
  createSubtask: (id, data) => api.post(`/tasks/${id}/subtasks`, data),
  bulkUpdate: (data) => api.post('/tasks/bulk', data),
  bulkDelete: (data) => api.delete('/tasks/bulk', { data }),
  getCalendarTasks: (params) => api.get('/tasks/calendar', { params }),
  updateTaskDueDate: (taskId, dueDate) => api.put(`/tasks/${taskId}/update-due-date`, { due_date: dueDate }),
};

// Reminders API
export const remindersAPI = {
  getAll: (params) => api.get('/reminders/', { params }),
  create: (data) => api.post('/reminders/', data),
  update: (id, data) => api.put(`/reminders/${id}`, data),
  delete: (id) => api.delete(`/reminders/${id}`),
};

// Meetings API
export const meetingsAPI = {
  getAll: (params) => api.get('/meetings/', { params }),
  create: (data) => api.post('/meetings/', data),
  update: (id, data) => api.put(`/meetings/${id}`, data),
  delete: (id) => api.delete(`/meetings/${id}`),
  respondToInvitation: (meetingId, invitationId, data) => 
    api.post(`/meetings/${meetingId}/invitations/${invitationId}/respond`, data),
  getInvitations: (meetingId) => api.get(`/meetings/${meetingId}/invitations`),
};

// Chat API
export const chatAPI = {
  getUsers: () => api.get('/chat/users'),
  getConversations: () => api.get('/chat/conversations'),
  requestChat: (userId) => api.post('/chat/conversations/request', { user_id: userId }),
  acceptChat: (conversationId) => api.post(`/chat/conversations/${conversationId}/accept`),
  rejectChat: (conversationId) => api.post(`/chat/conversations/${conversationId}/reject`),
  getMessages: (conversationId) => api.get(`/chat/conversations/${conversationId}/messages`),
  sendMessage: (conversationId, content, replyToId) => api.post(`/chat/conversations/${conversationId}/messages`, { content, reply_to_id: replyToId }),
  markDelivered: (messageId) => api.put(`/chat/messages/${messageId}/delivered`),
  markRead: (messageId) => api.put(`/chat/messages/${messageId}/read`),
  markConversationRead: (conversationId) => api.post(`/chat/conversations/${conversationId}/read`),
  editMessage: (messageId, content) => api.put(`/chat/messages/${messageId}`, { content }),
  deleteForMe: (messageId) => api.delete(`/chat/messages/${messageId}/delete-for-me`),
  deleteForEveryone: (messageId) => api.delete(`/chat/messages/${messageId}/delete-for-everyone`),
  uploadAttachment: (conversationId, file, config = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/chat/conversations/${conversationId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      ...config,
    });
  },
  downloadAttachment: (messageId) =>
    api.get(`/chat/attachments/${messageId}`, { responseType: 'blob' }),
  setTyping: (conversationId, typing) => api.post(`/chat/conversations/${conversationId}/typing`, { typing }),
  getTyping: (conversationId) => api.get(`/chat/conversations/${conversationId}/typing`),
  heartbeat: () => api.post('/chat/presence/heartbeat'),
  getPresence: (userId) => api.get(`/chat/presence/${userId}`),
  addReaction: (messageId, emoji) => api.post(`/chat/messages/${messageId}/reactions`, { emoji }),
  removeReaction: (messageId, reactionId) => api.delete(`/chat/messages/${messageId}/reactions/${reactionId}`),
};

// Groups API
export const groupsAPI = {
  list: () => api.get('/chat/groups'),
  create: (name, memberIds = []) => api.post('/chat/groups', { name, member_ids: memberIds }),
  getMessages: (groupId) => api.get(`/chat/groups/${groupId}/messages`),
  sendMessage: (groupId, content, replyToId) => api.post(`/chat/groups/${groupId}/messages`, { content, reply_to_id: replyToId }),
  setTyping: (groupId, typing) => api.post(`/chat/groups/${groupId}/typing`, { typing }),
  getTyping: (groupId) => api.get(`/chat/groups/${groupId}/typing`),
  markRead: (groupId) => api.post(`/chat/groups/${groupId}/read`),
  getDetails: (groupId) => api.get(`/chat/groups/${groupId}`),
  rename: (groupId, name) => api.put(`/chat/groups/${groupId}`, { name }),
  addMembers: (groupId, memberIds = []) => api.post(`/chat/groups/${groupId}/members`, { member_ids: memberIds }),
  removeMember: (groupId, userId) => api.delete(`/chat/groups/${groupId}/members/${userId}`),
  setMemberRole: (groupId, userId, role) => api.put(`/chat/groups/${groupId}/members/${userId}/role`, { role }),
  listInvitations: () => api.get('/chat/groups/invitations'),
  respondInvitation: (invitationId, status, rejectionReason) =>
    api.post(`/chat/groups/invitations/${invitationId}/respond`, { status, rejection_reason: rejectionReason }),
};

// Projects & Sprints API
export const projectsAPI = {
  getAll: (params) => api.get('/projects/', { params }),
  getById: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  getMine: () => api.get('/projects/my'),
};

// Project Members API
export const projectMembersAPI = {
  list: (projectId) => api.get(`/projects/${projectId}/members`),
  add: (projectId, data) => api.post(`/projects/${projectId}/members`, data),
  remove: (projectId, userId) => api.delete(`/projects/${projectId}/members/${userId}`),
};

export const sprintsAPI = {
  getAll: (params) => api.get('/sprints/', { params }),
  getById: (id) => api.get(`/sprints/${id}`),
  create: (data) => api.post('/sprints/', data),
  update: (id, data) => api.put(`/sprints/${id}`, data),
  delete: (id) => api.delete(`/sprints/${id}`),
};

// Notifications API
export const notificationsAPI = {
  getAll: (params) => api.get('/notifications/', { params }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  markAllAsRead: () => api.put('/notifications/mark-all-read'),
  delete: (id) => api.delete(`/notifications/${id}`),
  clearAll: () => api.delete('/notifications/clear-all'),
  resolve: (id) => api.post(`/notifications/${id}/resolve`),
  getPreferences: () => api.get('/notifications/preferences'),
  updatePreferences: (data) => api.put('/notifications/preferences', data),
  getProjectActivity: (projectId, limit = 50) => api.get('/notifications/project-activity', { params: { project_id: projectId, limit } }),
};

// Reports API
export const reportsAPI = {
  getPersonalTaskStatus: () => api.get('/reports/personal/task-status'),
  getPersonalTimeLogs: (days) => api.get('/reports/personal/time-logs', { params: { days } }),
  getPersonalActivity: (days) => api.get('/reports/personal/activity', { params: { days } }),
  getAdminOverview: () => api.get('/reports/admin/overview'),
  getSprintSummary: (days) => api.get('/reports/admin/sprint-summary', { params: { days } }),
  getSprintBurndown: (params) => api.get('/reports/admin/sprint-burndown', { params }),
  getSprintVelocity: (params) => api.get('/reports/admin/sprint-velocity', { params }),
  getDailyStats: (params) => api.get('/reports/admin/daily-stats', { params }),
  getOverdue: (params) => api.get('/reports/admin/overdue', { params }),
  getTopProjectsThroughput: (params) => api.get('/reports/admin/top-projects-throughput', { params }),
  exportToCSV: (reportType) => api.post('/reports/export/csv', 
    { report_type: reportType }, 
    { responseType: 'blob' }
  ),
  exportByPeriodCSV: (params) => api.get('/reports/export/period', { params, responseType: 'blob' }),
};

// Settings API
export const settingsAPI = {
  getSystem: () => api.get('/settings/system'),
  updateSystem: (data) => api.put('/settings/system', data),
  getPersonal: () => api.get('/settings/personal'),
  updatePersonal: (data) => api.put('/settings/personal', data),
};

// File Uploads API
export const filesAPI = {
  uploadToTask: (taskId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/files/task/${taskId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getTaskAttachments: (taskId) => api.get(`/files/task/${taskId}/attachments`),
  downloadAttachment: (attachmentId) => 
    api.get(`/files/attachment/${attachmentId}/download`, { responseType: 'blob' }),
  deleteAttachment: (attachmentId) => api.delete(`/files/attachment/${attachmentId}`),
  getUploadStats: () => api.get('/files/stats'),
};

export default api;
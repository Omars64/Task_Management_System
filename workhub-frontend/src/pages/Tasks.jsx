import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { tasksAPI, usersAPI, filesAPI, projectsAPI, sprintsAPI, projectMembersAPI } from '../services/api';
import { FiPlus, FiEdit2, FiTrash2, FiMessageSquare, FiX, FiClock, FiPaperclip } from 'react-icons/fi';
import { useFormValidation, ValidationUtils } from '../utils/validation';
import { CharacterCounter } from '../components/CharacterCounter';
import { FileUpload, AttachmentsList } from '../components/FileUpload';
import { useModal } from '../hooks/useModal';
import Modal from '../components/Modal';
import RichTextEditor from '../components/RichTextEditor';
import RichTextDisplay from '../components/RichTextDisplay';
import { formatLocalDate, formatLocalDateTime, formatForInput } from '../utils/dateTime';
import './Tasks.css';

const Tasks = () => {
  const { isAdmin, user, canCreateTasks } = useAuth();
  const { addToast } = useToast();
  const [commentUsers, setCommentUsers] = useState([]);
  const { modalState, showAlert, showConfirm, showError, showSuccess, closeModal } = useModal();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showTaskDetail, setShowTaskDetail] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [loadingTaskDetail, setLoadingTaskDetail] = useState(false);
  const [showTimeLogModal, setShowTimeLogModal] = useState(false);
  const [timeLogs, setTimeLogs] = useState([]);
  const [timeLogForm, setTimeLogForm] = useState({
    hours: '',
    description: ''
  });
  const [commentForm, setCommentForm] = useState({ content: '' });
  const [replyForms, setReplyForms] = useState({}); // { [commentId]: string }
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editCommentContent, setEditCommentContent] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [loadingAttachments, setLoadingAttachments] = useState(false);
  const [dependencyForm, setDependencyForm] = useState({ blocks_task_id: '' });
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: '',
    project_id: '',
    sprint_id: ''
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(4);
  const [meta, setMeta] = useState(null);
  // Bulk selection state
  const [selectedTaskIds, setSelectedTaskIds] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [bulkForm, setBulkForm] = useState({ status: '', priority: '', assigned_to: '' });
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    status: 'todo',
    assigned_to: '',
    due_date: '',
    project_id: '',
    sprint_id: ''
  });
  const [projects, setProjects] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [selectedProjectMembers, setSelectedProjectMembers] = useState([]);

  // Form validation
  const { errors, validateField, validateForm, clearErrors } = useFormValidation('taskCreation');

  // Initialize filters/page from URL on first mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const init = { ...filters };
    if (params.get('status')) init.status = params.get('status');
    if (params.get('priority')) init.priority = params.get('priority');
    if (params.get('search')) init.search = params.get('search');
    if (params.get('project_id')) init.project_id = params.get('project_id');
    if (params.get('sprint_id')) init.sprint_id = params.get('sprint_id');
    const p = Number(params.get('page') || 1);
    const ps = Number(params.get('page_size') || 4);
    setFilters(init);
    setPage(Number.isFinite(p) && p > 0 ? p : 1);
    setPageSize([4,8,16].includes(ps) ? ps : 4);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle deep-linking: check for taskId in URL after tasks are loaded
  useEffect(() => {
    if (loading || !tasks.length) return; // Wait for tasks to load
    
    const params = new URLSearchParams(window.location.search);
    const taskId = params.get('taskId');
    const origin = params.get('origin');
    
    // Process deep-link if origin is 'notif', 'dashboard', or taskId is present without origin
    if (taskId && (origin === 'notif' || origin === 'dashboard' || !origin) && !showTaskDetail) {
      const taskIdNum = Number(taskId);
      if (Number.isFinite(taskIdNum) && taskIdNum > 0) {
        // Find task in current list or fetch it
        const existingTask = tasks.find(t => t.id === taskIdNum);
        if (existingTask) {
          handleViewDetails(existingTask);
        } else {
          // Task not in current list, fetch it
          tasksAPI.getById(taskIdNum)
            .then(response => {
              handleViewDetails(response.data);
            })
            .catch(error => {
              console.error('Failed to fetch task for deep-link:', error);
              addToast('Task not found', { type: 'error' });
            });
        }
        // Clean up URL parameters after processing
        if (origin === 'dashboard' || origin === 'notif') {
          const newParams = new URLSearchParams(window.location.search);
          newParams.delete('taskId');
          newParams.delete('origin');
          const newUrl = newParams.toString() ? `/tasks?${newParams.toString()}` : '/tasks';
          window.history.replaceState(null, '', newUrl);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tasks, loading]);

  // Sync URL with filters and pagination
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.priority) params.set('priority', filters.priority);
    if (filters.search) params.set('search', filters.search);
    if (filters.project_id) params.set('project_id', filters.project_id);
    if (filters.sprint_id) params.set('sprint_id', filters.sprint_id);
    if (page) params.set('page', String(page));
    if (pageSize) params.set('page_size', String(pageSize));
    const q = params.toString();
    const url = q ? `/tasks?${q}` : '/tasks';
    window.history.replaceState(null, '', url);
  }, [filters, page, pageSize]);

  useEffect(() => {
    fetchTasks();
  }, [filters, page, pageSize]);

  useEffect(() => {
    if (user) {
      fetchProjectsAndUsers();
    }
  }, [user]);

  // Limit comment/mention users to project members when task has a project
  useEffect(() => {
    const loadMembers = async () => {
      try {
        if (selectedTask && selectedTask.project_id) {
          const res = await projectMembersAPI.list(selectedTask.project_id);
          const members = (res.data || []).map(m => ({ id: m.user_id, name: m.name, email: m.email }));
          setCommentUsers(members);
        } else {
          // No project → all users
          setCommentUsers(users);
        }
      } catch {
        setCommentUsers(users);
      }
    };
    loadMembers();
  }, [selectedTask?.project_id, users, selectedTask]);

  // Normalize role helpers
  const normalizedRole = () => (user?.role || '').toLowerCase().replace(/\s+/g, '_');
  const isManagerOrLead = () => {
    const r = normalizedRole();
    return r === 'manager' || r === 'team_lead';
  };

  // Fetch project members when project is selected in the form
  useEffect(() => {
    if (formData.project_id) {
      console.log('[DEBUG] Project changed, fetching members for project:', formData.project_id);
      fetchProjectMembers(formData.project_id);
    } else {
      console.log('[DEBUG] No project selected, clearing members');
      setSelectedProjectMembers([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.project_id]);

  const fetchProjectsAndUsers = async () => {
    if (!user) return;
    try {
      // For managers/team leads: fetch only their assigned projects
      // For admins: fetch all projects
      const role = normalizedRole();
      if (role === 'manager' || role === 'team_lead') {
        let assignedProjects = [];
        try {
          const { data } = await projectsAPI.getMine();
          assignedProjects = data || [];
        } catch (_) {
          // Fallback to all projects if getMine fails
          try { const { data } = await projectsAPI.getAll(); assignedProjects = data || []; } catch (__) {}
        }
        setProjects(assignedProjects);
        // Fetch users from all assigned projects
        await fetchUsersFromProjects(assignedProjects);
      } else {
        // For admins: fetch all projects and all users
        try { const { data } = await projectsAPI.getAll(); setProjects(data || []); } catch (_) {}
        if (isAdmin()) {
          fetchUsers();
        }
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      // Don't crash the component on error
      setProjects([]);
    }
  };

  const fetchUsersFromProjects = async (projectsList = []) => {
    try {
      const role = user?.role?.toLowerCase();
      if (role === 'manager' || role === 'team_lead') {
        // Get all unique users from all projects the user is assigned to
        const userIds = new Set();
        for (const project of projectsList) {
          try {
            const { data: members } = await projectMembersAPI.list(project.id);
            members.forEach(m => userIds.add(m.user_id));
          } catch (_) {}
        }
        // Fetch user details for all unique user IDs
        if (userIds.size > 0) {
          const allUsers = await usersAPI.getAll();
          const filteredUsers = allUsers.data.filter(u => userIds.has(u.id));
          setUsers(filteredUsers);
        } else {
          setUsers([]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch users from projects:', error);
      setUsers([]);
    }
  };

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.search) params.search = filters.search;
      if (filters.project_id) params.project_id = filters.project_id;
      if (filters.sprint_id) params.sprint_id = filters.sprint_id;
      params.page = page;
      params.page_size = pageSize;
      
      const response = await tasksAPI.getAll(params);
      const data = response.data;
      if (data && Array.isArray(data.items)) {
        setTasks(data.items);
        setMeta(data.meta || null);
      } else if (Array.isArray(data)) {
        setTasks(data);
        setMeta(null);
      } else {
        setTasks([]);
        setMeta(null);
      }
      // Reset selection whenever tasks list refreshes
      setSelectedTaskIds([]);
      setSelectAll(false);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await usersAPI.getAll();
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchProjectMembers = async (projectId) => {
    if (!projectId) {
      setSelectedProjectMembers([]);
      return;
    }
    try {
      const { data: members } = await projectMembersAPI.list(projectId);
      console.log('[DEBUG] Project members response:', members);
      
      if (!members || members.length === 0) {
        console.log('[DEBUG] No members found for project');
        setSelectedProjectMembers([]);
        return;
      }
      
      // Members already contain user details (user_id, name, email)
      // Transform them to match the user object structure (id, name, email)
      const projectUsers = members.map(member => ({
        id: member.user_id,
        name: member.name,
        email: member.email,
        role: member.role || 'User'
      })).filter(u => u.id && u.name); // Filter out any invalid entries
      
      console.log('[DEBUG] Transformed project users:', projectUsers);
      setSelectedProjectMembers(projectUsers);
    } catch (error) {
      console.error('Failed to fetch project members:', error);
      setSelectedProjectMembers([]);
    }
  };

  // Get available users for assignment based on role and selected project
  const getAvailableUsers = () => {
    // When a project is selected, always limit to project members for all creator roles
    if (formData.project_id && selectedProjectMembers.length > 0) {
      console.log('[DEBUG] getAvailableUsers - limiting to project members:', selectedProjectMembers.length);
      return selectedProjectMembers;
    }
    // Fallback to all users
    return users;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form before submission
    if (!validateForm(formData)) {
      return;
    }

    // Store form data and selected task for API call (before reset)
    const taskData = { ...formData };
    const isEdit = !!selectedTask;
    const taskId = selectedTask?.id;
    const taskToEdit = selectedTask ? { ...selectedTask } : null;

    // Show toast immediately for better UX
    if (isEdit) {
      addToast('Updating task...', { type: 'info', timeout: 3000 });
    } else {
      addToast('Creating task...', { type: 'info', timeout: 3000 });
    }

    // Optimistic UI: Clear form and close modal immediately
    setShowModal(false);
    resetForm();

    // For create: Add optimistic task to list immediately
    let optimisticTaskId = null;
    if (!isEdit) {
      optimisticTaskId = `temp-${Date.now()}`;
      const optimisticTask = {
        id: optimisticTaskId,
        title: taskData.title,
        description: taskData.description || '',
        priority: taskData.priority,
        status: taskData.status || 'todo',
        assigned_to: taskData.assigned_to || null,
        due_date: taskData.due_date || null,
        project_id: taskData.project_id || null,
        sprint_id: taskData.sprint_id || null,
        created_by: user?.id || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_optimistic: true // Flag to identify optimistic tasks
      };
      setTasks(prev => [optimisticTask, ...prev]);
    }

    try {
      if (isEdit) {
        await tasksAPI.update(taskId, taskData);
        addToast('Task updated successfully', { type: 'success' });
        // Refresh tasks to get updated data
        fetchTasks();
      } else {
        const response = await tasksAPI.create(taskData);
        // API returns: { message: '...', task: {...} }
        const createdTask = response.data?.task;
        
        // Remove optimistic task
        if (optimisticTaskId) {
          setTasks(prev => prev.filter(t => t.id !== optimisticTaskId));
        }
        
        addToast('Task created successfully', { type: 'success' });
        
        // Refresh to get the real task with all relationships (assignee names, etc.)
        // This ensures we have complete data
        fetchTasks();
      }
    } catch (error) {
      // Remove optimistic task on error
      if (optimisticTaskId) {
        setTasks(prev => prev.filter(t => t.id !== optimisticTaskId));
      }
      
      const errorData = error.response?.data;
      addToast(errorData?.error || 'Failed to save task', { type: 'error' });
      
      // Reopen modal with form data if edit failed, or just show error for create
      if (isEdit && taskToEdit) {
        setFormData(taskData);
        setSelectedTask(taskToEdit);
        setShowModal(true);
      } else if (!isEdit) {
        // For create, reopen modal so user can retry
        setFormData(taskData);
        setShowModal(true);
      }
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm(
      'Are you sure you want to delete this task? This action cannot be undone.',
      'Delete Task'
    );
    
    if (confirmed) {
      try {
        await tasksAPI.delete(id);
        fetchTasks();
        showSuccess('Task deleted successfully');
      } catch (error) {
        showError(error.response?.data?.error || 'Failed to delete task', 'Error Deleting Task');
      }
    }
  };

  // ========== BULK OPERATIONS ==========
  const toggleSelectTask = (taskId) => {
    setSelectedTaskIds((prev) =>
      prev.includes(taskId) ? prev.filter((id) => id !== taskId) : [...prev, taskId]
    );
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedTaskIds([]);
      setSelectAll(false);
    } else {
      const allIds = tasks.map((t) => t.id);
      setSelectedTaskIds(allIds);
      setSelectAll(true);
    }
  };

  const handleBulkUpdate = async () => {
    if (selectedTaskIds.length === 0) return;
    if (!bulkForm.status && !bulkForm.priority && !bulkForm.assigned_to) {
      showAlert('Choose at least one field to update (status, priority, assignee).', 'Bulk Update');
      return;
    }
    try {
      await tasksAPI.bulkUpdate({
        task_ids: selectedTaskIds,
        ...(bulkForm.status ? { status: bulkForm.status } : {}),
        ...(bulkForm.priority ? { priority: bulkForm.priority } : {}),
        ...(bulkForm.assigned_to !== '' ? { assigned_to: bulkForm.assigned_to } : {}),
      });
      setBulkForm({ status: '', priority: '', assigned_to: '' });
      setSelectedTaskIds([]);
      setSelectAll(false);
      await fetchTasks();
      showSuccess('Bulk update applied successfully');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to apply bulk update', 'Bulk Update Error');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedTaskIds.length === 0) return;
    const confirmed = await showConfirm(
      `Delete ${selectedTaskIds.length} selected task(s)? This action cannot be undone.`,
      'Bulk Delete'
    );
    if (!confirmed) return;
    try {
      await tasksAPI.bulkDelete({ task_ids: selectedTaskIds });
      setSelectedTaskIds([]);
      setSelectAll(false);
      await fetchTasks();
      showSuccess('Selected tasks deleted');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete selected tasks', 'Bulk Delete Error');
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
      // Preserve date and time for validation (min lead time 1 hour)
      due_date: task.due_date ? formatForInput(task.due_date) : '',
      project_id: task.project_id || '',
      sprint_id: task.sprint_id || ''
    });
    setShowModal(true);
  };

  const handleViewDetails = async (task) => {
    try {
      setLoadingTaskDetail(true);
      setShowTaskDetail(true); // Show modal first to provide visual feedback
      setSelectedTask(task); // Set basic task data immediately so modal can render
      
      const response = await tasksAPI.getById(task.id);
      setSelectedTask(response.data);
      setDependencyForm({ blocks_task_id: response.data.blocks_task_id || '' });
      // Fetch time logs for this task
      try {
        const timeLogsResponse = await tasksAPI.getTimeLogs(task.id);
        setTimeLogs(timeLogsResponse.data);
      } catch (err) {
        console.error('Failed to fetch time logs:', err);
        setTimeLogs([]);
      }
      // Fetch attachments for this task
      fetchAttachments(task.id);
      setLoadingTaskDetail(false);
      
      // Handle deep-linking: scroll to comment if commentId is in URL
      setTimeout(() => {
        const params = new URLSearchParams(window.location.search);
        const commentId = params.get('commentId');
        if (commentId) {
          const commentIdNum = Number(commentId);
          if (Number.isFinite(commentIdNum) && commentIdNum > 0) {
            // Scroll to comment after a short delay to ensure DOM is ready
            setTimeout(() => {
              const commentElement = document.getElementById(`comment-${commentIdNum}`);
              if (commentElement) {
                commentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Highlight the comment briefly
                commentElement.style.backgroundColor = '#fef3c7';
                commentElement.style.transition = 'background-color 0.3s ease';
                setTimeout(() => {
                  commentElement.style.backgroundColor = '';
                }, 2000);
              }
            }, 300);
          }
        }
      }, 100);
    } catch (error) {
      console.error('Failed to fetch task details:', error);
      showError(error.response?.data?.error || 'Failed to load task details', 'Error');
      setShowTaskDetail(false);
      setSelectedTask(null);
      setLoadingTaskDetail(false);
    }
  };

  const handleSaveDependency = async () => {
    if (!selectedTask) return;
    try {
      const payload = {
        blocks_task_id: dependencyForm.blocks_task_id === '' ? null : Number(dependencyForm.blocks_task_id),
      };
      await tasksAPI.update(selectedTask.id, payload);
      const updated = await tasksAPI.getById(selectedTask.id);
      setSelectedTask(updated.data);
      addToast('Dependency updated', { type: 'success' });
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to update dependency', 'Error Updating Dependency');
    }
  };

  const handleAddTimeLog = async (e) => {
    e.preventDefault();
    const hoursValidation = ValidationUtils.validateHours(timeLogForm.hours);
    if (!hoursValidation.isValid) {
      showError(hoursValidation.message, 'Invalid Hours');
      return;
    }
    try {
      await tasksAPI.addTimeLog(selectedTask.id, {
        ...timeLogForm,
        hours: hoursValidation.value
      });
      setTimeLogForm({ hours: '', description: '' });
      setShowTimeLogModal(false);
      const timeLogsResponse = await tasksAPI.getTimeLogs(selectedTask.id);
      setTimeLogs(timeLogsResponse.data);
      showSuccess('Time log added successfully');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to add time log', 'Error Adding Time Log');
    }
  };

  const handleDeleteTimeLog = async (logId) => {
    const confirmed = await showConfirm(
      'Are you sure you want to delete this time log?',
      'Delete Time Log'
    );
    if (confirmed) {
      try {
        await tasksAPI.deleteTimeLog(logId);
        const timeLogsResponse = await tasksAPI.getTimeLogs(selectedTask.id);
        setTimeLogs(timeLogsResponse.data);
        showSuccess('Time log deleted successfully');
      } catch (error) {
        showError(error.response?.data?.error || 'Failed to delete time log', 'Error Deleting Time Log');
      }
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentForm.content.trim()) {
      showError('Comment cannot be empty', 'Invalid Comment');
      return;
    }
    try {
      await tasksAPI.addComment(selectedTask.id, { content: commentForm.content });
      setCommentForm({ content: '' });
      const response = await tasksAPI.getById(selectedTask.id);
      setSelectedTask(response.data);
      addToast('Comment added', { type: 'success' });
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to add comment', 'Error Adding Comment');
    }
  };

  const handleEditComment = async (commentId) => {
    if (!editCommentContent.trim()) {
      showError('Comment cannot be empty', 'Invalid Comment');
      return;
    }
    try {
      await tasksAPI.updateComment(selectedTask.id, commentId, { content: editCommentContent });
      setEditingCommentId(null);
      setEditCommentContent('');
      const response = await tasksAPI.getById(selectedTask.id);
      setSelectedTask(response.data);
      addToast('Comment updated', { type: 'success' });
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to update comment', 'Error Updating Comment');
    }
  };

  const handleDeleteComment = async (commentId) => {
    const confirmed = await showConfirm(
      'Are you sure you want to delete this comment?',
      'Delete Comment'
    );
    if (!confirmed) return;
    
    try {
      await tasksAPI.deleteComment(selectedTask.id, commentId);
      const response = await tasksAPI.getById(selectedTask.id);
      setSelectedTask(response.data);
      showSuccess('Comment deleted successfully');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete comment', 'Error Deleting Comment');
    }
  };

  const startEditComment = (comment) => {
    setEditingCommentId(comment.id);
    setEditCommentContent(comment.content);
  };

  const handleAddReply = async (parentCommentId) => {
    const content = replyForms[parentCommentId] || '';
    if (!content.trim()) {
      showError('Reply cannot be empty', 'Invalid Reply');
      return;
    }
    try {
      await tasksAPI.addComment(selectedTask.id, { content, parent_comment_id: parentCommentId });
      setReplyForms(prev => ({ ...prev, [parentCommentId]: '' }));
      const response = await tasksAPI.getById(selectedTask.id);
      setSelectedTask(response.data);
      addToast('Reply added', { type: 'success' });
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to add reply', 'Error Adding Reply');
    }
  };

  const fetchAttachments = async (taskId) => {
    setLoadingAttachments(true);
    try {
      const response = await filesAPI.getTaskAttachments(taskId);
      setAttachments(response.data);
    } catch (error) {
      console.error('Failed to fetch attachments:', error);
      setAttachments([]);
    } finally {
      setLoadingAttachments(false);
    }
  };

  const handleFileUploadSuccess = () => {
    if (selectedTask) {
      fetchAttachments(selectedTask.id);
    }
  };

  const handleDownloadAttachment = async (attachment) => {
    try {
      const response = await filesAPI.downloadAttachment(attachment.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', attachment.original_filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to download file', 'Error Downloading File');
    }
  };

  const handleDeleteAttachment = async (attachment) => {
    const confirmed = await showConfirm(
      `Are you sure you want to delete ${attachment.original_filename}?`,
      'Delete Attachment'
    );
    if (!confirmed) {
      return;
    }
    try {
      await filesAPI.deleteAttachment(attachment.id);
      fetchAttachments(selectedTask.id);
      showSuccess('Attachment deleted successfully');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to delete attachment', 'Error Deleting Attachment');
    }
  };

  const handleStatusUpdate = async (taskId, newStatus) => {
    // Optimistic update
    const prev = tasks;
    const next = tasks.map(t => t.id === taskId ? { ...t, status: newStatus } : t);
    setTasks(next);
    try {
      await tasksAPI.update(taskId, { status: newStatus });
      addToast('Status updated', { type: 'success' });
    } catch (error) {
      // rollback
      setTasks(prev);
      showError(error.response?.data?.error || 'Failed to update status', 'Error Updating Status');
    }
  };

  const handleAssigneeUpdate = async (taskId, newAssigneeId) => {
    const prev = tasks;
    const userName = users.find(u => String(u.id) === String(newAssigneeId))?.name || null;
    const next = tasks.map(t => t.id === taskId ? { ...t, assigned_to: newAssigneeId === '' ? null : Number(newAssigneeId), assignee_name: userName } : t);
    setTasks(next);
    try {
      await tasksAPI.update(taskId, { assigned_to: newAssigneeId === '' ? null : Number(newAssigneeId) });
      addToast('Assignee updated', { type: 'success' });
    } catch (error) {
      setTasks(prev);
      showError(error.response?.data?.error || 'Failed to update assignee', 'Error Updating Assignee');
    }
  };

  const handlePriorityUpdate = async (taskId, newPriority) => {
    const prev = tasks;
    const next = tasks.map(t => t.id === taskId ? { ...t, priority: newPriority } : t);
    setTasks(next);
    try {
      await tasksAPI.update(taskId, { priority: newPriority });
      addToast('Priority updated', { type: 'success' });
    } catch (error) {
      setTasks(prev);
      showError(error.response?.data?.error || 'Failed to update priority', 'Error Updating Priority');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      priority: 'medium',
      status: 'todo',
      assigned_to: '',
      due_date: '',
      project_id: '',
      sprint_id: ''
    });
    setSelectedTask(null);
    setSelectedProjectMembers([]);
  };

  const handleCreateNew = () => {
    resetForm();
    setShowModal(true);
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
        {canCreateTasks() && (
          <button className="btn btn-primary" onClick={handleCreateNew}>
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
          <select
            className="form-select"
            value={filters.project_id}
            onChange={async (e) => {
              const project_id = e.target.value;
              setFilters({ ...filters, project_id, sprint_id: '' });
              if (project_id) {
                try { const { data } = await sprintsAPI.getAll({ project_id }); setSprints(data); } catch (_) { setSprints([]); }
              } else {
                setSprints([]);
              }
            }}
          >
            <option value="">All Projects</option>
            {projects.map(p => (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <select
            className="form-select"
            value={filters.sprint_id}
            onChange={(e) => setFilters({ ...filters, sprint_id: e.target.value })}
            disabled={!filters.project_id || sprints.length === 0}
          >
            <option value="">All Sprints</option>
            {sprints.map(s => (<option key={s.id} value={s.id}>{s.name}</option>))}
          </select>
        </div>

        {/* Bulk actions toolbar */}
        {isAdmin() && (
          <div className="bulk-actions" style={{ margin: '12px 0', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input type="checkbox" checked={selectAll} onChange={handleSelectAll} />
              <span>Select All</span>
            </label>
            <span style={{ color: 'var(--text-light)' }}>Selected: {selectedTaskIds.length}</span>
            <select
              className="form-select"
              value={bulkForm.status}
              onChange={(e) => setBulkForm({ ...bulkForm, status: e.target.value })}
            >
              <option value="">Set Status…</option>
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
            <select
              className="form-select"
              value={bulkForm.priority}
              onChange={(e) => setBulkForm({ ...bulkForm, priority: e.target.value })}
            >
              <option value="">Set Priority…</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <select
              className="form-select"
              value={bulkForm.assigned_to}
              onChange={(e) => setBulkForm({ ...bulkForm, assigned_to: e.target.value })}
            >
              <option value="">Assign To…</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>{user.name}</option>
              ))}
            </select>
            <button className="btn btn-primary" disabled={selectedTaskIds.length === 0} onClick={handleBulkUpdate}>
              Apply Bulk Update
            </button>
            <button className="btn btn-outline" disabled={selectedTaskIds.length === 0} onClick={handleBulkDelete}>
              Delete Selected
            </button>
          </div>
        )}

        {loading ? (
          <div className="spinner" />
        ) : tasks.length === 0 ? (
          <p className="text-center text-light">No tasks found</p>
        ) : (
          <div className="tasks-grid">
            {tasks.map(task => (
              <div key={task.id} className="task-card">
                <div className="task-card-header">
                  {isAdmin() && (
                    <input
                      type="checkbox"
                      checked={selectedTaskIds.includes(task.id)}
                      onChange={() => toggleSelectTask(task.id)}
                      style={{ marginRight: 8 }}
                    />
                  )}
                  <h3 className="task-card-title" onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleViewDetails(task); }}>
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
                {task.project_name && (
                  <div style={{ margin: '6px 0 0', display:'inline-flex', alignItems:'center', gap:6 }}>
                    <span className="badge badge-secondary" title="Project">
                      Project: {task.project_name}
                    </span>
                    {task.sprint_name && (
                      <span className="badge badge-secondary" title="Sprint">
                        Sprint: {task.sprint_name}
                      </span>
                    )}
                  </div>
                )}
                <div className="task-card-meta">
                  {Array.isArray(task.blocked_by) && task.blocked_by.some(b => b.status !== 'completed') && (
                    <span className="badge badge-danger" title="This task is blocked by another task">Blocked</span>
                  )}
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
                  <p className="task-card-due">Due: {formatLocalDate(task.due_date)}</p>
                )}
                <div className="task-card-footer" style={{ display: 'grid', gap: 8 }}>
                  <select
                    className="status-select"
                    value={task.status}
                    onChange={(e) => handleStatusUpdate(task.id, e.target.value)}
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option
                      value="completed"
                      disabled={Array.isArray(task.blocked_by) && task.blocked_by.some(b => b.status !== 'completed')}
                    >
                      Completed{Array.isArray(task.blocked_by) && task.blocked_by.some(b => b.status !== 'completed') ? ' (Blocked)' : ''}
                    </option>
                  </select>
                  {isAdmin() && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <select
                        className="form-select"
                        value={task.assigned_to || ''}
                        onChange={(e) => handleAssigneeUpdate(task.id, e.target.value)}
                      >
                        <option value="">Unassigned</option>
                        {users.map(u => (
                          <option key={u.id} value={u.id}>{u.name}</option>
                        ))}
                      </select>
                      <select
                        className="form-select"
                        value={task.priority}
                        onChange={(e) => handlePriorityUpdate(task.id, e.target.value)}
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {meta && (
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop: 12, gap: 12, flexWrap:'wrap' }}>
            <div style={{ display:'flex', alignItems:'center', gap: 8 }}>
              <button className="btn btn-outline" disabled={!meta.has_prev} onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button>
              <span style={{ color:'var(--text-light)' }}>Page {meta.page} of {meta.total_pages || 1}</span>
              <button className="btn btn-outline" disabled={!meta.has_next} onClick={() => setPage((p) => p + 1)}>Next</button>
            </div>
            <div>
              <select className="form-select" value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
                <option value={4}>4 / page</option>
                <option value={8}>8 / page</option>
                <option value={16}>16 / page</option>
              </select>
            </div>
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
                <label className="form-label">Title * (3-100 characters)</label>
                <input
                  type="text"
                  className={`form-input ${errors.title ? 'error' : ''}`}
                  value={formData.title}
                  maxLength={100}
                  onChange={(e) => {
                    const value = e.target.value;
                    setFormData({ ...formData, title: value });
                    validateField('title', value, formData);
                  }}
                  placeholder="Enter task title"
                  required
                />
                {errors.title && <div className="error-message">{errors.title}</div>}
                <CharacterCounter current={formData.title.length} max={100} warningThreshold={0.9} />
              </div>
              <div className="form-group">
                <label className="form-label">Description (10-1000 characters)</label>
                <textarea
                  className={`form-textarea ${errors.description ? 'error' : ''}`}
                  value={formData.description}
                  maxLength={1000}
                  onChange={(e) => {
                    const value = e.target.value;
                    setFormData({ ...formData, description: value });
                    validateField('description', value, formData);
                  }}
                  placeholder="Describe the task in detail..."
                  rows="4"
                />
                {errors.description && <div className="error-message">{errors.description}</div>}
                <CharacterCounter current={formData.description.length} max={1000} warningThreshold={0.95} />
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
                    {getAvailableUsers().map(userOption => (
                      <option key={userOption.id} value={userOption.id}>{userOption.name}</option>
                    ))}
                  </select>
                  {formData.project_id && (
                    <small className="form-hint">Only showing members of the selected project</small>
                  )}
                </div>
                <div className="form-group">
                  <label className="form-label">Due Date & Time (min +1 hour)</label>
                  <input
                    type="datetime-local"
                    className={`form-input ${errors.due_date ? 'error' : ''}`}
                    value={formData.due_date}
                    onChange={(e) => {
                      const value = e.target.value;
                      setFormData({ ...formData, due_date: value });
                      validateField('due_date', value, formData);
                    }}
                  />
                  {errors.due_date && <div className="error-message">{errors.due_date}</div>}
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Project</label>
                  <select
                    className="form-select"
                    value={formData.project_id}
                    onChange={async (e) => {
                      const project_id = e.target.value;
                      setFormData({ ...formData, project_id, sprint_id: '' });
                      if (project_id) {
                        try { const { data } = await sprintsAPI.getAll({ project_id }); setSprints(data); } catch (_) { setSprints([]); }
                        // Always fetch project members to populate assignee list limitation
                        try {
                          const { data: members } = await projectMembersAPI.list(parseInt(project_id));
                          const projectUsers = members.map(m => ({ id: m.user_id, name: m.name, email: m.email })).filter(u => u.id && u.name);
                          setSelectedProjectMembers(projectUsers);
                        } catch (_) { setSelectedProjectMembers([]); }
                      } else { setSprints([]); }
                    }}
                  >
                    <option value="">No Project</option>
                    {projects.map(p => (<option key={p.id} value={p.id}>{p.name}</option>))}
                    {user && (user.role === 'manager' || user.role === 'team_lead') && projects.length === 0 && (
                      <option value="" disabled>No projects assigned</option>
                    )}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Sprint</label>
                  <select
                    className="form-select"
                    value={formData.sprint_id}
                    onChange={(e) => setFormData({ ...formData, sprint_id: e.target.value })}
                    disabled={!formData.project_id || sprints.length === 0}
                  >
                    <option value="">No Sprint</option>
                    {sprints.map(s => (<option key={s.id} value={s.id}>{s.name}</option>))}
                  </select>
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
        <div className="modal-overlay" onClick={() => { setShowTaskDetail(false); setSelectedTask(null); setLoadingTaskDetail(false); }}>
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{loadingTaskDetail ? 'Loading...' : (selectedTask.title || 'Task Details')}</h2>
              <button className="modal-close" onClick={() => { setShowTaskDetail(false); setSelectedTask(null); setLoadingTaskDetail(false); }}>
                <FiX />
              </button>
            </div>
            {loadingTaskDetail ? (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <p>Loading task details...</p>
              </div>
            ) : (
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
                  <strong>Project:</strong> {selectedTask.project_name || 'No Project'}
                </div>
                <div>
                  <strong>Assigned to:</strong> {selectedTask.assignee_name || 'Unassigned'}
                </div>
                <div>
                  <strong>Created by:</strong> {selectedTask.creator_name || 'Unknown'}
                </div>
                {selectedTask.due_date && (
                  <div>
                    <strong>Due Date:</strong> {formatLocalDateTime(selectedTask.due_date)}
                  </div>
                )}
              </div>
              <div className="task-detail-section">
                <h3>Dependencies</h3>
                <div style={{ display:'grid', gap: 8 }}>
                  <div>
                    <strong>Blocks:</strong> {selectedTask.blocked_task_title || 'None'}
                  </div>
                  <div>
                    <strong>Blocked by:</strong> {selectedTask.blocked_by && Array.isArray(selectedTask.blocked_by) && selectedTask.blocked_by.length > 0 ? selectedTask.blocked_by.map(b => b.title).join(', ') : 'None'}
                  </div>
                </div>
                {isAdmin() && (
                  <div style={{ marginTop: 12, display:'flex', gap: 8, alignItems:'center', flexWrap:'wrap' }}>
                    <select
                      className="form-select"
                      value={dependencyForm.blocks_task_id}
                      onChange={(e) => setDependencyForm({ blocks_task_id: e.target.value })}
                    >
                      <option value="">Does not block any task</option>
                      {tasks
                        .filter(t => t.id !== selectedTask.id && t.status !== 'completed')
                        .map(t => (
                          <option key={t.id} value={t.id}>{t.title}</option>
                        ))}
                    </select>
                    <button className="btn btn-primary btn-sm" onClick={handleSaveDependency}>Save</button>
                  </div>
                )}
              </div>
              
              <div className="task-detail-section">
                <h3><FiMessageSquare /> Comments</h3>
                <form onSubmit={handleAddComment} style={{ marginBottom: '16px' }}>
                  <div className="form-group">
                    <RichTextEditor
                      value={commentForm.content}
                      onChange={(content) => setCommentForm({ content })}
                      placeholder="Add a comment... Use @Name to mention someone"
                      maxLength={500}
                      users={commentUsers}
                    />
                  </div>
                  <button type="submit" className="btn btn-primary btn-sm">
                    Add Comment
                  </button>
                </form>
                {selectedTask.comments && Array.isArray(selectedTask.comments) && selectedTask.comments.length > 0 ? (
                  <div className="comments-list" style={{ display:'grid', gap:12 }}>
                    {selectedTask.comments
                      .filter(c => !c.parent_comment_id)
                      .sort((a,b) => {
                        const dateA = new Date(a.created_at);
                        const dateB = new Date(b.created_at);
                        return dateB - dateA;
                      })
                      .map(comment => (
                        <div 
                          key={comment.id} 
                          id={`comment-${comment.id}`}
                          className="comment" 
                          style={{ border:'1px solid var(--border-color)', borderRadius:8, padding:12 }}
                        >
                          <div className="comment-header" style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
                            <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                              <strong>{comment.user_name}</strong>
                              <span style={{ color:'var(--text-light)', fontSize:'0.875rem' }}>
                                {formatLocalDateTime(comment.created_at)}
                              </span>
                            </div>
                            {user && (comment.user_id === user.id || isAdmin()) && (
                              <div style={{ display:'flex', gap:4 }}>
                                {comment.user_id === user.id && editingCommentId !== comment.id && (
                                  <button
                                    className="icon-btn"
                                    onClick={() => startEditComment(comment)}
                                    title="Edit comment"
                                  >
                                    <FiEdit2 size={14} />
                                  </button>
                                )}
                                <button
                                  className="icon-btn"
                                  onClick={() => handleDeleteComment(comment.id)}
                                  title="Delete comment"
                                >
                                  <FiTrash2 size={14} />
                                </button>
                              </div>
                            )}
                          </div>
                          
                          {editingCommentId === comment.id ? (
                            <div style={{ marginBottom: 8 }}>
                              <RichTextEditor
                                value={editCommentContent}
                                onChange={setEditCommentContent}
                                placeholder="Edit your comment..."
                                maxLength={500}
                                users={commentUsers}
                              />
                              <div style={{ display:'flex', gap:8, marginTop:8 }}>
                                <button className="btn btn-primary btn-sm" onClick={() => handleEditComment(comment.id)}>
                                  Save
                                </button>
                                <button className="btn btn-outline btn-sm" onClick={() => {
                                  setEditingCommentId(null);
                                  setEditCommentContent('');
                                }}>
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <RichTextDisplay content={comment.content} />
                          )}

                          {/* Replies */}
                          {selectedTask.comments && Array.isArray(selectedTask.comments) && selectedTask.comments.filter(r => r.parent_comment_id === comment.id).length > 0 && (
                            <div className="replies" style={{ marginTop:12, marginLeft:12, display:'grid', gap:8 }}>
                              {selectedTask.comments
                                .filter(r => r.parent_comment_id === comment.id)
                                .map(reply => (
                                  <div key={reply.id} style={{ borderLeft:'2px solid var(--border-color)', paddingLeft:12, paddingTop:8 }}>
                                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:4 }}>
                                      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                                        <strong style={{ fontSize:'0.9rem' }}>{reply.user_name}</strong>
                                        <span style={{ color:'var(--text-light)', fontSize:'0.8rem' }}>
                                          {formatLocalDateTime(reply.created_at)}
                                        </span>
                                      </div>
                                      {user && (reply.user_id === user.id || isAdmin()) && (
                                        <div style={{ display:'flex', gap:4 }}>
                                          {reply.user_id === user.id && editingCommentId !== reply.id && (
                                            <button
                                              className="icon-btn"
                                              onClick={() => startEditComment(reply)}
                                              title="Edit reply"
                                            >
                                              <FiEdit2 size={12} />
                                            </button>
                                          )}
                                          <button
                                            className="icon-btn"
                                            onClick={() => handleDeleteComment(reply.id)}
                                            title="Delete reply"
                                          >
                                            <FiTrash2 size={12} />
                                          </button>
                                        </div>
                                      )}
                                    </div>
                                    {editingCommentId === reply.id ? (
                                      <div style={{ marginBottom: 8 }}>
                                        <RichTextEditor
                                          value={editCommentContent}
                                          onChange={setEditCommentContent}
                                          placeholder="Edit your reply..."
                                          maxLength={500}
                                          users={users}
                                        />
                                        <div style={{ display:'flex', gap:8, marginTop:8 }}>
                                          <button className="btn btn-primary btn-sm" onClick={() => handleEditComment(reply.id)}>
                                            Save
                                          </button>
                                          <button className="btn btn-outline btn-sm" onClick={() => {
                                            setEditingCommentId(null);
                                            setEditCommentContent('');
                                          }}>
                                            Cancel
                                          </button>
                                        </div>
                                      </div>
                                    ) : (
                                      <RichTextDisplay content={reply.content} />
                                    )}
                                  </div>
                                ))}
                            </div>
                          )}

                          {/* Reply form */}
                          <div style={{ display:'grid', gap:8, marginTop:12 }}>
                            <RichTextEditor
                              value={replyForms[comment.id] || ''}
                              onChange={(content) => setReplyForms(prev => ({ ...prev, [comment.id]: content }))}
                              placeholder="Write a reply... Use @Name to mention"
                              maxLength={500}
                              users={commentUsers}
                            />
                            <div style={{ display:'flex', gap:8 }}>
                              <button className="btn btn-primary btn-sm" onClick={() => handleAddReply(comment.id)}>Reply</button>
                              <button className="btn btn-outline btn-sm" onClick={() => setReplyForms(prev => ({ ...prev, [comment.id]: '' }))}>Cancel</button>
                            </div>
                          </div>
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
              
              <div className="task-detail-section">
                <h3><FiPaperclip /> Attachments</h3>
                <div style={{ marginBottom: '24px' }}>
                  <FileUpload 
                    taskId={selectedTask.id} 
                    onUploadSuccess={handleFileUploadSuccess}
                  />
                </div>
                {loadingAttachments ? (
                  <p className="text-light">Loading attachments...</p>
                ) : (
                  <AttachmentsList
                    attachments={attachments}
                    onDelete={handleDeleteAttachment}
                    onDownload={handleDownloadAttachment}
                  />
                )}
              </div>
            </div>
            )}
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

      {/* Modal Component */}
      <Modal
        isOpen={modalState.isOpen}
        onClose={closeModal}
        onConfirm={modalState.onConfirm}
        title={modalState.title}
        message={modalState.message}
        type={modalState.type}
        confirmText={modalState.confirmText}
        cancelText={modalState.cancelText}
        showCancel={modalState.showCancel}
      >
        {modalState.children}
      </Modal>
    </div>
  );
};

export default Tasks;
import React, { useState, useEffect } from 'react';
import { remindersAPI, meetingsAPI, tasksAPI, usersAPI, projectsAPI, projectMembersAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { FiBell, FiUsers, FiCalendar, FiClock, FiEdit, FiTrash2, FiFilter } from 'react-icons/fi';
import Modal from '../components/Modal';
import { useModal } from '../hooks/useModal';
import { useFormValidation } from '../utils/validation';
import { CharacterCounter } from '../components/CharacterCounter';
import moment from 'moment';
import './RemindersAndMeetings.css';

const RemindersAndMeetings = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const { modalState, showError, showSuccess, showConfirm, closeModal } = useModal();
  
  // Validation hooks
  const { errors: reminderErrors, warnings: reminderWarnings, validateField: validateReminderField, validateForm: validateReminderForm, clearErrors: clearReminderErrors } = useFormValidation('reminder');
  const { errors: meetingErrors, warnings: meetingWarnings, validateField: validateMeetingField, validateForm: validateMeetingForm, clearErrors: clearMeetingErrors } = useFormValidation('meeting');
  
  const [reminders, setReminders] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [projectMembers, setProjectMembers] = useState([]);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Normalize role helpers
  const normalizedRole = () => (user?.role || '').toLowerCase().replace(/\s+/g, '_');
  const isManagerOrLead = () => {
    const r = normalizedRole();
    return r === 'manager' || r === 'team_lead';
  };
  const isAdminRole = () => {
    const r = normalizedRole();
    return r === 'admin' || r === 'super_admin';
  };
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('reminders'); // 'reminders' or 'meetings'
  const [filter, setFilter] = useState('all'); // 'all', 'upcoming', 'past'
  const [showFilters, setShowFilters] = useState(false);
  const [showReminderModal, setShowReminderModal] = useState(false);
  const [showMeetingModal, setShowMeetingModal] = useState(false);
  const [editingReminder, setEditingReminder] = useState(null);
  const [editingMeeting, setEditingMeeting] = useState(null);
  const [reminderForm, setReminderForm] = useState({
    title: '',
    description: '',
    reminder_date: '',
    reminder_type: 'custom',
    task_id: '',
    days_before: '',
    time_based: ''
  });
  const [meetingForm, setMeetingForm] = useState({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    location: '',
    project_id: '',
    invite_user_ids: []
  });

  useEffect(() => {
    fetchData();
    fetchTasks();
    fetchUsers();
    fetchProjects();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [remindersRes, meetingsRes] = await Promise.all([
        remindersAPI.getAll(),
        meetingsAPI.getAll()
      ]);
      
      // Filter to show only user's own reminders and meetings they created or were invited to
      const userReminders = (remindersRes.data || []).filter(r => r.user_id === user.id);
      const userMeetings = (meetingsRes.data || []).filter(m => 
        m.created_by === user.id || 
        (m.invitations && m.invitations.some(inv => inv.user_id === user.id))
      );
      
      setReminders(userReminders);
      setMeetings(userMeetings);
    } catch (error) {
      console.error('Failed to fetch reminders and meetings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await tasksAPI.getAll({});
      const data = response.data;
      setTasks(Array.isArray(data) ? data : (data?.items || []));
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      setTasks([]);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await usersAPI.getAll();
      setUsers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setUsers([]);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.getAll();
      const projectsData = response.data || [];
      setProjects(projectsData);
      
      // For Team Leads and Managers, fetch project members to limit user invitations
      if (user && isManagerOrLead()) {
        // Get projects the current user is a member of
        const myProjectsResponse = await projectsAPI.getMine();
        const myProjects = myProjectsResponse.data || [];
        
        // Fetch members for each project
        const allMembers = new Set();
        for (const project of myProjects) {
          try {
            const membersResponse = await projectMembersAPI.list(project.id);
            const members = membersResponse.data || [];
            members.forEach(member => {
              if (member.user_id && member.user_id !== user.id) {
                allMembers.add(member.user_id);
              }
            });
          } catch (err) {
            console.error(`Failed to fetch members for project ${project.id}:`, err);
          }
        }
        setProjectMembers(Array.from(allMembers));
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      setProjects([]);
    }
  };

  const handleEditReminder = (reminder) => {
    setEditingReminder(reminder);
    setReminderForm({
      title: reminder.title || '',
      description: reminder.description || '',
      reminder_date: reminder.reminder_date ? moment(reminder.reminder_date).format('YYYY-MM-DDTHH:mm') : '',
      reminder_type: reminder.reminder_type || 'custom',
      task_id: reminder.task_id || '',
      days_before: reminder.days_before || '',
      time_based: reminder.time_based ? moment(reminder.time_based).format('YYYY-MM-DDTHH:mm') : ''
    });
    setShowReminderModal(true);
  };

  const handleEditMeeting = (meeting) => {
    setEditingMeeting(meeting);
    setMeetingForm({
      title: meeting.title || '',
      description: meeting.description || '',
      start_time: meeting.start_time ? moment(meeting.start_time).format('YYYY-MM-DDTHH:mm') : '',
      end_time: meeting.end_time ? moment(meeting.end_time).format('YYYY-MM-DDTHH:mm') : '',
      location: meeting.location || '',
      project_id: meeting.project_id || '',
      invite_user_ids: meeting.invitations ? meeting.invitations.map(inv => inv.user_id) : []
    });
    setShowMeetingModal(true);
  };

  const handleSaveReminder = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateReminderForm(reminderForm)) {
      // Show specific error messages from validation
      if (reminderErrors.title) {
        addToast(`Title validation failed: ${reminderErrors.title}`, { type: 'error' });
      } else if (reminderErrors.description) {
        addToast(`Description validation failed: ${reminderErrors.description}`, { type: 'error' });
      } else if (reminderErrors.reminder_date) {
        addToast(`Reminder date validation failed: ${reminderErrors.reminder_date}`, { type: 'error' });
      } else if (reminderErrors.time_based) {
        addToast(`Time validation failed: ${reminderErrors.time_based}`, { type: 'error' });
      } else if (reminderErrors.days_before) {
        addToast(`Days before validation failed: ${reminderErrors.days_before}`, { type: 'error' });
      } else {
        addToast('Please fix the validation errors before submitting', { type: 'error' });
      }
      return;
    }
    
    try {
      const payload = {
        title: reminderForm.title,
        description: reminderForm.description,
        reminder_type: reminderForm.reminder_type,
        task_id: reminderForm.task_id || null,
        days_before: reminderForm.days_before ? parseInt(reminderForm.days_before) : null,
        time_based: reminderForm.time_based ? moment(reminderForm.time_based).toISOString() : null
      };
      
      if (reminderForm.reminder_type === 'custom' && reminderForm.reminder_date) {
        payload.reminder_date = moment(reminderForm.reminder_date).toISOString();
      }
      
      if (editingReminder) {
        await remindersAPI.update(editingReminder.id, payload);
        addToast('Reminder updated successfully', { type: 'success' });
      } else {
        await remindersAPI.create(payload);
        addToast('Reminder created successfully', { type: 'success' });
      }
      
      setShowReminderModal(false);
      setEditingReminder(null);
      setReminderForm({
        title: '',
        description: '',
        reminder_date: '',
        reminder_type: 'custom',
        task_id: '',
        days_before: '',
        time_based: ''
      });
      clearReminderErrors();
      fetchData();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to save reminder', 'Error');
    }
  };

  const handleSaveMeeting = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateMeetingForm(meetingForm)) {
      // Show specific error messages from validation
      if (meetingErrors.title) {
        addToast(`Title validation failed: ${meetingErrors.title}`, { type: 'error' });
      } else if (meetingErrors.description) {
        addToast(`Description validation failed: ${meetingErrors.description}`, { type: 'error' });
      } else if (meetingErrors.start_time) {
        addToast(`Start time validation failed: ${meetingErrors.start_time}`, { type: 'error' });
      } else if (meetingErrors.end_time) {
        addToast(`End time validation failed: ${meetingErrors.end_time}`, { type: 'error' });
      } else {
        addToast('Please fix the validation errors before submitting', { type: 'error' });
      }
      return;
    }
    
    try {
      const payload = {
        title: meetingForm.title,
        description: meetingForm.description,
        start_time: moment(meetingForm.start_time).toISOString(),
        end_time: moment(meetingForm.end_time).toISOString(),
        location: meetingForm.location,
        project_id: meetingForm.project_id || null,
        invite_user_ids: meetingForm.invite_user_ids || []
      };
      
      if (editingMeeting) {
        await meetingsAPI.update(editingMeeting.id, payload);
        addToast('Meeting updated successfully', { type: 'success' });
      } else {
        await meetingsAPI.create(payload);
        addToast('Meeting created successfully', { type: 'success' });
      }
      
      setShowMeetingModal(false);
      setEditingMeeting(null);
      setMeetingForm({
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        location: '',
        project_id: '',
        invite_user_ids: []
      });
      clearMeetingErrors();
      fetchData();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to save meeting', 'Error');
    }
  };

  const handleDeleteReminder = async (reminderId) => {
    const proceed = showConfirm ? await showConfirm('Are you sure you want to delete this reminder?', 'Delete Reminder') : window.confirm('Are you sure you want to delete this reminder?');
    if (!proceed) return;
    try {
      await remindersAPI.delete(reminderId);
      setReminders(reminders.filter(r => r.id !== reminderId));
      addToast('Reminder deleted successfully', { type: 'success' });
    } catch (error) {
      console.error('Failed to delete reminder:', error);
      showError(error.response?.data?.error || 'Failed to delete reminder', 'Error');
    }
  };

  const handleDeleteMeeting = async (meetingId) => {
    console.log('[DELETE DEBUG] handleDeleteMeeting called with meetingId:', meetingId);
    
    if (isDeleting) {
      console.log('[DELETE DEBUG] Already deleting, ignoring duplicate call');
      return;
    }
    
    setIsDeleting(true);
    console.log('[DELETE DEBUG] showConfirm available:', !!showConfirm);
    
    let proceed = false;
    try {
      if (showConfirm) {
        proceed = await showConfirm('Are you sure you want to delete this meeting?', 'Delete Meeting');
      } else {
        proceed = window.confirm('Are you sure you want to delete this meeting?');
      }
      console.log('[DELETE DEBUG] User confirmed:', proceed);
    } catch (err) {
      console.error('[DELETE DEBUG] Error showing confirmation:', err);
      setIsDeleting(false);
      return;
    }
    
    if (!proceed) {
      console.log('[DELETE DEBUG] User cancelled deletion');
      setIsDeleting(false);
      return;
    }
    
    try {
      console.log('[DELETE DEBUG] Calling API to delete meeting...');
      await meetingsAPI.delete(meetingId);
      setMeetings(meetings.filter(m => m.id !== meetingId));
      addToast('Meeting deleted successfully', { type: 'success' });
      console.log('[DELETE DEBUG] Meeting deleted successfully');
    } catch (error) {
      console.error('[DELETE DEBUG] Failed to delete meeting:', error);
      console.error('[DELETE DEBUG] Error response:', error.response?.data);
      showError(error.response?.data?.error || 'Failed to delete meeting', 'Error');
    } finally {
      setIsDeleting(false);
    }
  };

  // Get available users for meeting invitations based on role
  const getAvailableUsersForInvitation = () => {
    // All roles (admin/manager/team_lead/developer/viewer) can invite any user (excluding self)
    return users.filter(u => u.id !== user.id);
  };

  const getFilteredReminders = () => {
    const now = new Date();
    if (filter === 'upcoming') {
      return reminders.filter(r => new Date(r.reminder_date) >= now);
    } else if (filter === 'past') {
      return reminders.filter(r => new Date(r.reminder_date) < now);
    }
    return reminders;
  };

  const getFilteredMeetings = () => {
    const now = new Date();
    if (filter === 'upcoming') {
      return meetings.filter(m => new Date(m.start_time) >= now);
    } else if (filter === 'past') {
      return meetings.filter(m => new Date(m.start_time) < now);
    }
    return meetings;
  };

  const sortedReminders = getFilteredReminders().sort((a, b) => 
    new Date(a.reminder_date) - new Date(b.reminder_date)
  );

  const sortedMeetings = getFilteredMeetings().sort((a, b) => 
    new Date(a.start_time) - new Date(b.start_time)
  );

  if (loading) {
    return <div className="spinner" />;
  }

  return (
    <div className="reminders-meetings-page">
      <div className="page-header">
        <h1>My Reminders & Meetings</h1>
        <div className="header-actions">
          <button
            className={`btn btn-outline ${showFilters ? 'active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
          >
            <FiFilter /> Filter
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>Time Period:</label>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">All</option>
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
            </select>
          </div>
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'reminders' ? 'active' : ''}`}
          onClick={() => setActiveTab('reminders')}
        >
          <FiBell /> Reminders ({reminders.length})
        </button>
        <button
          className={`tab ${activeTab === 'meetings' ? 'active' : ''}`}
          onClick={() => setActiveTab('meetings')}
        >
          <FiUsers /> Meetings ({meetings.length})
        </button>
      </div>

      <div className="content-panel">
        {activeTab === 'reminders' && (
          <div className="reminders-list">
            {sortedReminders.length === 0 ? (
              <div className="empty-state">
                <FiBell size={48} />
                <p>No reminders found</p>
              </div>
            ) : (
              sortedReminders.map(reminder => (
                <div key={reminder.id} className="reminder-card">
                  <div className="card-header">
                    <div className="card-title">
                      <FiBell className="icon" />
                      <h3>{reminder.title}</h3>
                    </div>
                    <div className="card-actions">
                      <button
                        className="btn-icon"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleEditReminder(reminder);
                        }}
                        title="Edit"
                        type="button"
                      >
                        <FiEdit />
                      </button>
                      <button
                        className="btn-icon"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteReminder(reminder.id);
                        }}
                        title="Delete"
                        type="button"
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </div>
                  {reminder.description && (
                    <p className="card-description">{reminder.description}</p>
                  )}
                  <div className="card-meta">
                    <div className="meta-item">
                      <FiCalendar />
                      <span>{moment.utc(reminder.reminder_date).local().format('MMMM DD, YYYY')}</span>
                    </div>
                    <div className="meta-item">
                      <FiClock />
                      <span>{moment.utc(reminder.reminder_date).local().format('HH:mm')}</span>
                    </div>
                    <div className="meta-item">
                      <span className={`badge badge-${reminder.reminder_type}`}>
                        {reminder.reminder_type}
                      </span>
                    </div>
                    {reminder.is_sent && (
                      <div className="meta-item">
                        <span className="badge badge-sent">Sent</span>
                      </div>
                    )}
                  </div>
                  {reminder.task_id && (
                    <div className="card-footer">
                      <span>Related to Task ID: {reminder.task_id}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'meetings' && (
          <div className="meetings-list">
            {sortedMeetings.length === 0 ? (
              <div className="empty-state">
                <FiUsers size={48} />
                <p>No meetings found</p>
              </div>
            ) : (
              sortedMeetings.map(meeting => (
                <div key={meeting.id} className="meeting-card">
                  <div className="card-header">
                    <div className="card-title">
                      <FiUsers className="icon" />
                      <h3>{meeting.title}</h3>
                    </div>
                    <div className="card-actions">
                      {/* Show edit/delete if user is creator or admin */}
                      {(meeting.created_by === user.id || isAdminRole()) && (
                        <>
                          <button
                            className="btn-icon"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleEditMeeting(meeting);
                            }}
                            title="Edit"
                            type="button"
                          >
                            <FiEdit />
                          </button>
                          <button
                            className="btn-icon"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleDeleteMeeting(meeting.id);
                            }}
                            title="Delete"
                            aria-label="Delete meeting"
                            type="button"
                            disabled={isDeleting}
                            style={{ pointerEvents: isDeleting ? 'none' : 'auto' }}
                          >
                            <FiTrash2 />
                          </button>
                        </>
                      )}
                      {/* For invited users, show that they're invited */}
                      {meeting.created_by !== user.id && (
                        <span className="status-badge invited" title="You are invited to this meeting">
                          Invited
                        </span>
                      )}
                    </div>
                  </div>
                  {meeting.description && (
                    <p className="card-description">{meeting.description}</p>
                  )}
                  <div className="card-meta">
                    <div className="meta-item">
                      <FiCalendar />
                      <span>{moment.utc(meeting.start_time).local().format('MMMM DD, YYYY')}</span>
                    </div>
                    <div className="meta-item">
                      <FiClock />
                      <span>
                        {moment.utc(meeting.start_time).local().format('HH:mm')} - {moment.utc(meeting.end_time).local().format('HH:mm')}
                      </span>
                    </div>
                    {meeting.location && (
                      <div className="meta-item">
                        <span>📍 {meeting.location}</span>
                      </div>
                    )}
                  </div>
                  {meeting.project_id && (
                    <div className="card-footer">
                      <span>Project ID: {meeting.project_id}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Edit/Create Reminder Modal */}
      {showReminderModal && (
        <Modal
          isOpen={showReminderModal}
          onClose={() => {
            setShowReminderModal(false);
            setEditingReminder(null);
            setReminderForm({
              title: '',
              description: '',
              reminder_date: '',
              reminder_type: 'custom',
              task_id: '',
              days_before: '',
              time_based: ''
            });
            clearReminderErrors();
          }}
          title={editingReminder ? 'Edit Reminder' : 'Create Reminder'}
        >
          <form onSubmit={handleSaveReminder} className="reminder-meeting-form">
            <div className="form-group">
              <label>Title * (3-100 characters)</label>
              <input
                type="text"
                className={reminderErrors.title ? 'error' : ''}
                value={reminderForm.title}
                maxLength={100}
                onChange={(e) => {
                  const value = e.target.value;
                  setReminderForm(prev => ({ ...prev, title: value }));
                  validateReminderField('title', value, reminderForm);
                }}
                required
              />
              {reminderErrors.title && <div className="error-message">{reminderErrors.title}</div>}
              <CharacterCounter current={reminderForm.title.length} max={100} warningThreshold={0.9} />
            </div>
            
            <div className="form-group">
              <label>Description (max 500 characters)</label>
              <textarea
                className={reminderErrors.description ? 'error' : ''}
                value={reminderForm.description}
                maxLength={500}
                onChange={(e) => {
                  const value = e.target.value;
                  setReminderForm(prev => ({ ...prev, description: value }));
                  validateReminderField('description', value, reminderForm);
                }}
                rows="3"
              />
              {reminderErrors.description && <div className="error-message">{reminderErrors.description}</div>}
              <CharacterCounter current={reminderForm.description.length} max={500} warningThreshold={0.95} />
            </div>
            
            <div className="form-group">
              <label>Reminder Type *</label>
              <select
                value={reminderForm.reminder_type}
                onChange={(e) => setReminderForm(prev => ({ ...prev, reminder_type: e.target.value }))}
                required
              >
                <option value="custom">Custom Date/Time</option>
                <option value="task_deadline">Task Deadline</option>
                <option value="days_before">Days Before Task Deadline</option>
                <option value="time_based">Specific Time</option>
              </select>
            </div>
            
            {reminderForm.reminder_type === 'custom' && (
              <div className="form-group">
                <label>Reminder Date/Time *</label>
                <input
                  type="datetime-local"
                  className={reminderErrors.reminder_date ? 'error' : ''}
                  value={reminderForm.reminder_date}
                  onChange={(e) => {
                    const value = e.target.value;
                    setReminderForm(prev => ({ ...prev, reminder_date: value }));
                    validateReminderField('reminder_date', value, reminderForm);
                  }}
                  required
                />
                {reminderErrors.reminder_date && <div className="error-message">{reminderErrors.reminder_date}</div>}
                {reminderWarnings.reminder_date && <div className="warning-message">{reminderWarnings.reminder_date}</div>}
              </div>
            )}
            
            {reminderForm.reminder_type === 'days_before' && (
              <>
                <div className="form-group">
                  <label>Task *</label>
                  <select
                    value={reminderForm.task_id}
                    onChange={(e) => setReminderForm(prev => ({ ...prev, task_id: e.target.value }))}
                    required
                  >
                    <option value="">Select Task</option>
                    {tasks.map(task => (
                      <option key={task.id} value={task.id}>
                        {task.title}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Days Before * (1-365)</label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    className={reminderErrors.days_before ? 'error' : ''}
                    value={reminderForm.days_before}
                    onChange={(e) => {
                      const value = e.target.value;
                      setReminderForm(prev => ({ ...prev, days_before: value }));
                      validateReminderField('days_before', value, reminderForm);
                    }}
                    required
                  />
                  {reminderErrors.days_before && <div className="error-message">{reminderErrors.days_before}</div>}
                </div>
              </>
            )}
            
            {reminderForm.reminder_type === 'task_deadline' && (
              <div className="form-group">
                <label>Task *</label>
                <select
                  value={reminderForm.task_id}
                  onChange={(e) => setReminderForm(prev => ({ ...prev, task_id: e.target.value }))}
                  required
                >
                  <option value="">Select Task</option>
                  {tasks.map(task => (
                    <option key={task.id} value={task.id}>
                      {task.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            {reminderForm.reminder_type === 'time_based' && (
              <div className="form-group">
                <label>Time *</label>
                <input
                  type="datetime-local"
                  className={reminderErrors.time_based ? 'error' : ''}
                  value={reminderForm.time_based}
                  onChange={(e) => {
                    const value = e.target.value;
                    setReminderForm(prev => ({ ...prev, time_based: value }));
                    validateReminderField('time_based', value, reminderForm);
                  }}
                  required
                />
                {reminderErrors.time_based && <div className="error-message">{reminderErrors.time_based}</div>}
                {reminderWarnings.time_based && <div className="warning-message">{reminderWarnings.time_based}</div>}
              </div>
            )}
            
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">
                {editingReminder ? 'Update Reminder' : 'Create Reminder'}
              </button>
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => {
                  setShowReminderModal(false);
                  setEditingReminder(null);
                  setReminderForm({
                    title: '',
                    description: '',
                    reminder_date: '',
                    reminder_type: 'custom',
                    task_id: '',
                    days_before: '',
                    time_based: ''
                  });
                  clearReminderErrors();
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Edit/Create Meeting Modal */}
      {showMeetingModal && (
        <Modal
          isOpen={showMeetingModal}
          onClose={() => {
            setShowMeetingModal(false);
            setEditingMeeting(null);
            setMeetingForm({
              title: '',
              description: '',
              start_time: '',
              end_time: '',
              location: '',
              project_id: '',
              invite_user_ids: []
            });
            clearMeetingErrors();
          }}
          title={editingMeeting ? 'Edit Meeting' : 'Create Meeting'}
        >
          <form onSubmit={handleSaveMeeting} className="reminder-meeting-form">
            <div className="form-group">
              <label>Title * (3-100 characters)</label>
              <input
                type="text"
                className={meetingErrors.title ? 'error' : ''}
                value={meetingForm.title}
                maxLength={100}
                onChange={(e) => {
                  const value = e.target.value;
                  setMeetingForm(prev => ({ ...prev, title: value }));
                  validateMeetingField('title', value, meetingForm);
                }}
                required
              />
              {meetingErrors.title && <div className="error-message">{meetingErrors.title}</div>}
              <CharacterCounter current={meetingForm.title.length} max={100} warningThreshold={0.9} />
            </div>
            
            <div className="form-group">
              <label>Description (max 500 characters)</label>
              <textarea
                className={meetingErrors.description ? 'error' : ''}
                value={meetingForm.description}
                maxLength={500}
                onChange={(e) => {
                  const value = e.target.value;
                  setMeetingForm(prev => ({ ...prev, description: value }));
                  validateMeetingField('description', value, meetingForm);
                }}
                rows="3"
              />
              {meetingErrors.description && <div className="error-message">{meetingErrors.description}</div>}
              <CharacterCounter current={meetingForm.description.length} max={500} warningThreshold={0.95} />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>Start Time * (must be future, max 1 year ahead)</label>
                <input
                  type="datetime-local"
                  className={meetingErrors.start_time ? 'error' : ''}
                  value={meetingForm.start_time}
                  onChange={(e) => {
                    const value = e.target.value;
                    setMeetingForm(prev => ({ ...prev, start_time: value }));
                    validateMeetingField('start_time', value, meetingForm);
                  }}
                  required
                />
                {meetingErrors.start_time && <div className="error-message">{meetingErrors.start_time}</div>}
                {meetingWarnings.start_time && <div className="warning-message">⚠️ {meetingWarnings.start_time}</div>}
                <small style={{ color: 'var(--text-light)', fontSize: '0.85rem' }}>Business hours: 7 AM - 6 PM</small>
              </div>
              <div className="form-group">
                <label>End Time * (max 8 hours duration)</label>
                <input
                  type="datetime-local"
                  className={meetingErrors.end_time ? 'error' : ''}
                  value={meetingForm.end_time}
                  onChange={(e) => {
                    const value = e.target.value;
                    setMeetingForm(prev => ({ ...prev, end_time: value }));
                    validateMeetingField('end_time', value, meetingForm);
                  }}
                  required
                />
                {meetingErrors.end_time && <div className="error-message">{meetingErrors.end_time}</div>}
                {meetingWarnings.end_time && <div className="warning-message">⚠️ {meetingWarnings.end_time}</div>}
              </div>
            </div>
            
            <div className="form-group">
              <label>Location</label>
              <input
                type="text"
                value={meetingForm.location}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, location: e.target.value }))}
              />
            </div>
            
            <div className="form-group">
              <label>Project</label>
              <select
                value={meetingForm.project_id}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, project_id: e.target.value }))}
              >
                <option value="">No Project</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Invite Users</label>
              <select
                multiple
                value={meetingForm.invite_user_ids}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                  setMeetingForm(prev => ({ ...prev, invite_user_ids: selected }));
                }}
                style={{ minHeight: '100px' }}
              >
                {getAvailableUsersForInvitation().map(userOption => (
                  <option key={userOption.id} value={userOption.id}>
                    {userOption.name} ({userOption.email})
                  </option>
                ))}
              </select>
              <small>
                Hold Ctrl/Cmd to select multiple users
                {isManagerOrLead() && 
                  ' (limited to users in your projects)'}
              </small>
            </div>
            
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">
                {editingMeeting ? 'Update Meeting' : 'Create Meeting'}
              </button>
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => {
                  setShowMeetingModal(false);
                  setEditingMeeting(null);
                  setMeetingForm({
                    title: '',
                    description: '',
                    start_time: '',
                    end_time: '',
                    location: '',
                    project_id: '',
                    invite_user_ids: []
                  });
                  clearMeetingErrors();
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </Modal>
      )}
      {/* Global confirm/alert modal used by useModal hook */}
      <Modal
        isOpen={modalState?.isOpen}
        onClose={closeModal}
        onConfirm={modalState?.onConfirm}
        title={modalState?.title}
        message={modalState?.message}
        type={modalState?.type}
        confirmText={modalState?.confirmText}
        cancelText={modalState?.cancelText}
        showCancel={modalState?.showCancel}
      >
        {modalState?.children}
      </Modal>
    </div>
  );
};

export default RemindersAndMeetings;


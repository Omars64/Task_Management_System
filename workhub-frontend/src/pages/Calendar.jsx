import React, { useState, useEffect } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import 'react-big-calendar/lib/addons/dragAndDrop/styles.css';
import { tasksAPI, projectsAPI, sprintsAPI, usersAPI, remindersAPI, meetingsAPI, projectMembersAPI } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ValidationUtils } from '../utils/validation';
import { useAuth } from '../context/AuthContext';
import { FiFilter, FiX, FiPlus, FiClock, FiUsers, FiCalendar as FiCalendarIcon, FiBell } from 'react-icons/fi';
import { useModal } from '../hooks/useModal';
import Modal from '../components/Modal';
import './Calendar.css';

const localizer = momentLocalizer(moment);
const DnDCalendar = withDragAndDrop(Calendar);

const CalendarPage = () => {
  const { user, isAdmin } = useAuth();
  const { addToast } = useToast();
  const { modalState, showError, showSuccess, closeModal, showConfirm } = useModal();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState('month');
  const [filters, setFilters] = useState({
    project_id: '',
    sprint_id: '',
    assigned_to: '',
    status: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [projects, setProjects] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [users, setUsers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [projectMembers, setProjectMembers] = useState([]);

  // Normalize role helpers
  const normalizedRole = () => (user?.role || '').toLowerCase().replace(/\s+/g, '_');
  const isManagerOrLead = () => {
    const r = normalizedRole();
    return r === 'manager' || r === 'team_lead';
  };
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showEventDetail, setShowEventDetail] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [showDayEventsModal, setShowDayEventsModal] = useState(false);
  const [dayEvents, setDayEvents] = useState([]);
  
  // Modals
  const [showReminderModal, setShowReminderModal] = useState(false);
  const [showMeetingModal, setShowMeetingModal] = useState(false);
  const [showMeetingInvitationModal, setShowMeetingInvitationModal] = useState(false);
  const [pendingInvitations, setPendingInvitations] = useState([]);
  
  // Forms
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
    fetchProjects();
    fetchSprints();
    fetchUsers();
    fetchPendingInvitations();
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await tasksAPI.getAll({});
      setTasks(Array.isArray(response.data) ? response.data : response.data.items || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      setTasks([]);
    }
  };

  useEffect(() => {
    fetchCalendarData();
  }, [currentDate, view, filters]);

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.getAll();
      setProjects(response.data);
      
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
    }
  };

  const fetchSprints = async () => {
    try {
      const response = await sprintsAPI.getAll();
      setSprints(response.data);
    } catch (error) {
      console.error('Failed to fetch sprints:', error);
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

  const fetchPendingInvitations = async () => {
    try {
      const meetingsResponse = await meetingsAPI.getAll({});
      const meetings = meetingsResponse.data || [];
      const allInvitations = [];
      
      for (const meeting of meetings) {
        if (meeting.invitations) {
          const pending = meeting.invitations.filter(inv => 
            inv.user_id === user?.id && inv.status === 'pending'
          );
          allInvitations.push(...pending.map(inv => ({ ...inv, meeting })));
        }
      }
      
      setPendingInvitations(allInvitations);
    } catch (error) {
      console.error('Failed to fetch invitations:', error);
    }
  };

  const fetchCalendarData = async () => {
    setLoading(true);
    try {
      const startDate = moment(currentDate).startOf(view === 'month' ? 'month' : view === 'week' ? 'week' : 'day').toISOString();
      const endDate = moment(currentDate).endOf(view === 'month' ? 'month' : view === 'week' ? 'week' : 'day').toISOString();

      // Fetch tasks, reminders, and meetings in parallel
      const [tasksResponse, remindersResponse, meetingsResponse] = await Promise.all([
        tasksAPI.getCalendarTasks({
          start_date: startDate,
          end_date: endDate,
          ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
        }),
        remindersAPI.getAll(),
        meetingsAPI.getAll({ start_date: startDate, end_date: endDate })
      ]);

      const calendarEvents = [];

      // Add tasks
      const tasksByDate = tasksResponse.data.tasks_by_date || {};
      Object.keys(tasksByDate).forEach(dateKey => {
        tasksByDate[dateKey].forEach(task => {
          const dueDate = new Date(task.due_date);
          calendarEvents.push({
            id: `task-${task.id}`,
            title: `📋 ${task.title}`,
            start: dueDate,
            end: dueDate,
            resource: { type: 'task', data: task },
            priority: task.priority,
            status: task.status
          });
        });
      });

      // Add reminders
      const reminders = remindersResponse.data || [];
      reminders.forEach(reminder => {
        const reminderDate = moment.utc(reminder.reminder_date).local().toDate();
        if (reminderDate >= new Date(startDate) && reminderDate <= new Date(endDate)) {
          calendarEvents.push({
            id: `reminder-${reminder.id}`,
            title: `🔔 ${reminder.title}`,
            start: reminderDate,
            end: reminderDate,
            resource: { type: 'reminder', data: reminder },
            priority: 'medium'
          });
        }
      });

      // Add meetings
      const meetings = meetingsResponse.data || [];
      meetings.forEach(meeting => {
        calendarEvents.push({
          id: `meeting-${meeting.id}`,
          title: `👥 ${meeting.title}`,
          start: moment.utc(meeting.start_time).local().toDate(),
          end: moment.utc(meeting.end_time).local().toDate(),
          resource: { type: 'meeting', data: meeting },
          priority: 'medium'
        });
      });

      setEvents(calendarEvents);
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to load calendar data', 'Error Loading Calendar');
    } finally {
      setLoading(false);
    }
  };

  const handleEventClick = async (event) => {
    setSelectedEvent(event);
    setShowEventDetail(true);
  };

  const handleEventDrop = async ({ event, start }) => {
    if (event.resource.type === 'task') {
      try {
        const newDueDate = moment(start).startOf('day').toISOString();
        await tasksAPI.updateTaskDueDate(event.resource.data.id, newDueDate);
        showSuccess('Task due date updated');
        fetchCalendarData();
      } catch (error) {
        showError(error.response?.data?.error || 'Failed to update task due date', 'Error');
        fetchCalendarData();
      }
    } else if (event.resource.type === 'reminder') {
      try {
        await remindersAPI.update(event.resource.data.id, {
          reminder_date: moment(start).toISOString()
        });
        showSuccess('Reminder date updated');
        fetchCalendarData();
      } catch (error) {
        showError(error.response?.data?.error || 'Failed to update reminder', 'Error');
        fetchCalendarData();
      }
    } else if (event.resource.type === 'meeting') {
      try {
        const duration = moment(event.resource.data.end_time).diff(moment(event.resource.data.start_time));
        const newStart = moment(start);
        const newEnd = moment(newStart).add(duration, 'milliseconds');
        
        await meetingsAPI.update(event.resource.data.id, {
          start_time: newStart.toISOString(),
          end_time: newEnd.toISOString()
        });
        showSuccess('Meeting time updated');
        fetchCalendarData();
      } catch (error) {
        showError(error.response?.data?.error || 'Failed to update meeting', 'Error');
        fetchCalendarData();
      }
    }
  };

  const handleSelectSlot = ({ start, end }) => {
    // Pre-fill meeting form with selected time slot
    setMeetingForm(prev => ({
      ...prev,
      start_time: moment(start).format('YYYY-MM-DDTHH:mm'),
      end_time: moment(end || start).add(1, 'hour').format('YYYY-MM-DDTHH:mm')
    }));
    setShowMeetingModal(true);
  };

  const handleDayClick = (date) => {
    const clickedDate = moment(date).startOf('day');
    const eventsForDay = events.filter(event => {
      const eventDate = moment(event.start).startOf('day');
      return eventDate.isSame(clickedDate, 'day');
    });
    
    setSelectedDate(date);
    setDayEvents(eventsForDay);
    setShowDayEventsModal(true);
  };

  const handleCreateReminder = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        title: reminderForm.title,
        description: reminderForm.description,
        reminder_type: reminderForm.reminder_type,
        task_id: reminderForm.task_id || null,
        days_before: reminderForm.days_before ? parseInt(reminderForm.days_before) : null,
        time_based: reminderForm.time_based ? moment(reminderForm.time_based).toISOString() : null
      };
      
      // Add reminder_date only for custom type
      if (reminderForm.reminder_type === 'custom' && reminderForm.reminder_date) {
        payload.reminder_date = moment(reminderForm.reminder_date).toISOString();
      }
      
      await remindersAPI.create(payload);
      showSuccess('Reminder created successfully');
      setShowReminderModal(false);
      setReminderForm({
        title: '',
        description: '',
        reminder_date: '',
        reminder_type: 'custom',
        task_id: '',
        days_before: '',
        time_based: ''
      });
      fetchCalendarData();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to create reminder', 'Error');
    }
  };

  const handleCreateMeeting = async (e) => {
    e.preventDefault();
    // Validate meeting times (block past dates and >1 year ahead, etc.)
    const times = ValidationUtils.validateMeetingTimes(meetingForm.start_time, meetingForm.end_time);
    if (!times.isValid) {
      addToast(`Meeting validation failed: ${times.message}`, { type: 'error' });
      return;
    }
    // Optionally validate title length for basic UX consistency
    const title = ValidationUtils.validateReminderTitle(meetingForm.title);
    if (!title.isValid) {
      addToast(`Title validation failed: ${title.message}`, { type: 'error' });
      return;
    }
    try {
      // Ensure invite_user_ids are integers
      const inviteUserIds = Array.isArray(meetingForm.invite_user_ids) 
        ? meetingForm.invite_user_ids.map(id => {
            const numId = typeof id === 'string' ? parseInt(id, 10) : id;
            return Number.isInteger(numId) && numId > 0 ? numId : null;
          }).filter(id => id !== null)
        : [];
      
      const payload = {
        title: meetingForm.title.trim(),
        description: (meetingForm.description || '').trim(),
        start_time: moment(meetingForm.start_time).toISOString(),
        end_time: moment(meetingForm.end_time).toISOString(),
        location: (meetingForm.location || '').trim(),
        project_id: meetingForm.project_id ? parseInt(meetingForm.project_id, 10) : null,
        invite_user_ids: inviteUserIds
      };
      
      await meetingsAPI.create(payload);
      showSuccess('Meeting created successfully');
      setShowMeetingModal(false);
      setMeetingForm({
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        location: '',
        project_id: '',
        invite_user_ids: []
      });
      fetchCalendarData();
      fetchPendingInvitations();
    } catch (error) {
      console.error('Meeting creation error:', error);
      const msg = error.response?.data?.error || error.message || 'Failed to create meeting';
      addToast(msg, { type: 'error' });
      showError(msg, 'Error Creating Meeting');
    }
  };

  const handleRespondToInvitation = async (invitation, status, rejectionReason = '') => {
    try {
      await meetingsAPI.respondToInvitation(invitation.meeting.id, invitation.id, {
        status,
        rejection_reason: rejectionReason
      });
      showSuccess(`Invitation ${status} successfully`);
      fetchPendingInvitations();
      fetchCalendarData();
      setShowMeetingInvitationModal(false);
    } catch (error) {
      showError(error.response?.data?.error || `Failed to ${status} invitation`, 'Error');
    }
  };

  // Get available users for meeting invitations based on role
  const getAvailableUsersForInvitation = () => {
    // All roles can invite any user (excluding self)
    return users.filter(u => u.id !== user?.id);
  };

  // Group events by date for day markers
  const eventsByDate = {};
  events.forEach(event => {
    const dateKey = moment(event.start).format('YYYY-MM-DD');
    if (!eventsByDate[dateKey]) {
      eventsByDate[dateKey] = [];
    }
    eventsByDate[dateKey].push(event);
  });

  const dayPropGetter = (date) => {
    const dateKey = moment(date).format('YYYY-MM-DD');
    const dayEvents = eventsByDate[dateKey] || [];
    const hasEvents = dayEvents.length > 0;
    
    return {
      className: hasEvents ? 'day-with-events' : '',
      style: hasEvents ? {
        position: 'relative'
      } : {}
    };
  };

  const eventStyleGetter = (event) => {
    let backgroundColor = '#68939d';
    let borderColor = '#68939d';

    if (event.resource?.type === 'meeting') {
      backgroundColor = '#3b82f6';
      borderColor = '#2563eb';
    } else if (event.resource?.type === 'reminder') {
      backgroundColor = '#f59e0b';
      borderColor = '#d97706';
    } else if (event.resource?.type === 'task') {
      switch (event.priority) {
        case 'high':
          backgroundColor = '#ef4444';
          borderColor = '#dc2626';
          break;
        case 'medium':
          backgroundColor = '#f59e0b';
          borderColor = '#d97706';
          break;
        case 'low':
          backgroundColor = '#10b981';
          borderColor = '#059669';
          break;
      }
    }

    if (event.status === 'completed') {
      backgroundColor = '#6b7280';
      borderColor = '#4b5563';
    }

    return {
      style: {
        backgroundColor,
        borderColor,
        borderWidth: '2px',
        borderRadius: '4px',
        opacity: event.status === 'completed' ? 0.7 : 1,
        color: '#fff',
        padding: '2px 4px',
        fontSize: '0.875rem'
      }
    };
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      project_id: '',
      sprint_id: '',
      assigned_to: '',
      status: ''
    });
  };

  const activeFiltersCount = Object.values(filters).filter(v => v !== '').length;

  return (
    <div className="calendar-page">
      <div className="calendar-header">
        <h1>Calendar</h1>
        <div className="calendar-controls">
          <button
            className={`btn btn-outline ${view === 'month' ? 'active' : ''}`}
            onClick={() => setView('month')}
          >
            Month
          </button>
          <button
            className={`btn btn-outline ${view === 'week' ? 'active' : ''}`}
            onClick={() => setView('week')}
          >
            Week
          </button>
          <button
            className={`btn btn-outline ${view === 'day' ? 'active' : ''}`}
            onClick={() => setView('day')}
          >
            Day
          </button>
          <button
            className="btn btn-outline"
            onClick={() => setCurrentDate(new Date())}
          >
            Today
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setShowReminderModal(true)}
            title="Create Reminder"
          >
            <FiBell /> Reminder
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setShowMeetingModal(true)}
            title="Create Meeting"
          >
            <FiUsers /> Meeting
          </button>
          {pendingInvitations.length > 0 && (
            <button
              className="btn btn-primary"
              onClick={() => setShowMeetingInvitationModal(true)}
              title={`${pendingInvitations.length} pending invitation(s)`}
            >
              <FiUsers /> Invitations ({pendingInvitations.length})
            </button>
          )}
          <button
            className={`btn btn-outline ${showFilters ? 'active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
          >
            <FiFilter /> Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="calendar-filters">
          <div className="filter-group">
            <label>Project</label>
            <select
              value={filters.project_id}
              onChange={(e) => handleFilterChange('project_id', e.target.value)}
            >
              <option value="">All Projects</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Sprint</label>
            <select
              value={filters.sprint_id}
              onChange={(e) => handleFilterChange('sprint_id', e.target.value)}
            >
              <option value="">All Sprints</option>
              {sprints.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          {isAdmin() && (
            <div className="filter-group">
              <label>Assigned To</label>
              <select
                value={filters.assigned_to}
                onChange={(e) => handleFilterChange('assigned_to', e.target.value)}
              >
                <option value="">All Users</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>
          )}

          <div className="filter-group">
            <label>Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>

          <button className="btn btn-outline btn-sm" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>
      )}

      <div className="calendar-container">
        {loading ? (
          <div className="spinner" />
        ) : (
          <DnDCalendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            style={{ height: 600 }}
            view={view}
            onView={setView}
            date={currentDate}
            onNavigate={setCurrentDate}
            onSelectEvent={handleEventClick}
            onSelectSlot={handleSelectSlot}
            onEventDrop={handleEventDrop}
            selectable
            eventPropGetter={eventStyleGetter}
            showMultiDayTimes
            popup
            resizable={false}
            draggableAccessor={() => true}
            dayPropGetter={dayPropGetter}
            components={{
              month: {
                dateHeader: ({ date, label, ...props }) => {
                  const dateKey = moment(date).format('YYYY-MM-DD');
                  const dayEvents = eventsByDate[dateKey] || [];
                  const hasEvents = dayEvents.length > 0;
                  
                  return (
                    <div
                      {...props}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (hasEvents) {
                          handleDayClick(date);
                        }
                      }}
                      style={{ 
                        cursor: hasEvents ? 'pointer' : 'default', 
                        width: '100%',
                        position: 'relative'
                      }}
                      title={hasEvents ? `Click to view ${dayEvents.length} event(s)` : ''}
                    >
                      {label}
                    </div>
                  );
                }
              }
            }}
          />
        )}
      </div>

      {/* Event Detail Modal */}
      {showEventDetail && selectedEvent && (
        <Modal
          isOpen={showEventDetail}
          onClose={() => {
            setShowEventDetail(false);
            setSelectedEvent(null);
          }}
          title={selectedEvent.title}
        >
          <div className="event-detail-modal">
            {selectedEvent.resource?.type === 'task' && (
              <>
                <div className="task-detail-item">
                  <strong>Status:</strong> <span className={`status-badge status-${selectedEvent.resource.data.status}`}>
                    {selectedEvent.resource.data.status}
                  </span>
                </div>
                <div className="task-detail-item">
                  <strong>Priority:</strong> <span className={`priority-badge priority-${selectedEvent.resource.data.priority}`}>
                    {selectedEvent.resource.data.priority}
                  </span>
                </div>
                {selectedEvent.resource.data.description && (
                  <div className="task-detail-item">
                    <strong>Description:</strong>
                    <p>{selectedEvent.resource.data.description}</p>
                  </div>
                )}
                <div className="task-detail-item">
                  <strong>Due Date:</strong> {moment(selectedEvent.start).format('MMMM DD, YYYY HH:mm')}
                </div>
              </>
            )}
            
            {selectedEvent.resource?.type === 'reminder' && (
              <>
                <div className="task-detail-item">
                  <strong>Reminder Type:</strong> {selectedEvent.resource.data.reminder_type}
                </div>
                {selectedEvent.resource.data.description && (
                  <div className="task-detail-item">
                    <strong>Description:</strong>
                    <p>{selectedEvent.resource.data.description}</p>
                  </div>
                )}
                <div className="task-detail-item">
                  <strong>Reminder Date:</strong> {moment(selectedEvent.resource.data.reminder_date).format('MMMM DD, YYYY HH:mm')}
                </div>
              </>
            )}
            
            {selectedEvent.resource?.type === 'meeting' && (
              <>
                <div className="task-detail-item">
                  <strong>Organizer:</strong> {selectedEvent.resource.data.creator_name}
                </div>
                {selectedEvent.resource.data.description && (
                  <div className="task-detail-item">
                    <strong>Description:</strong>
                    <p>{selectedEvent.resource.data.description}</p>
                  </div>
                )}
                <div className="task-detail-item">
                  <strong>Time:</strong> {moment.utc(selectedEvent.resource.data.start_time).local().format('MMMM DD, YYYY HH:mm')} - {moment.utc(selectedEvent.resource.data.end_time).local().format('HH:mm')}
                </div>
                {selectedEvent.resource.data.location && (
                  <div className="task-detail-item">
                    <strong>Location:</strong> {selectedEvent.resource.data.location}
                  </div>
                )}
              </>
            )}
          </div>
        </Modal>
      )}

      {/* Create Reminder Modal */}
      {showReminderModal && (
        <Modal
          isOpen={showReminderModal}
          onClose={() => setShowReminderModal(false)}
          title="Create Reminder"
        >
          <form onSubmit={handleCreateReminder} className="reminder-meeting-form">
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                value={reminderForm.title}
                onChange={(e) => setReminderForm(prev => ({ ...prev, title: e.target.value }))}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={reminderForm.description}
                onChange={(e) => setReminderForm(prev => ({ ...prev, description: e.target.value }))}
                rows="3"
              />
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
                  value={reminderForm.reminder_date}
                  onChange={(e) => setReminderForm(prev => ({ ...prev, reminder_date: e.target.value }))}
                  required
                />
              </div>
            )}
            
            {reminderForm.reminder_type === 'days_before' && (
              <>
                <div className="form-group">
                  <label>Task</label>
                  <select
                    value={reminderForm.task_id}
                    onChange={(e) => setReminderForm(prev => ({ ...prev, task_id: e.target.value }))}
                    required
                  >
                    <option value="">Select Task</option>
                    {tasks.filter(t => t.due_date).map(task => (
                      <option key={task.id} value={task.id}>
                        {task.title}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Days Before *</label>
                  <input
                    type="number"
                    value={reminderForm.days_before}
                    onChange={(e) => setReminderForm(prev => ({ ...prev, days_before: e.target.value }))}
                    min="1"
                    required
                  />
                </div>
              </>
            )}
            
            {reminderForm.reminder_type === 'task_deadline' && (
              <div className="form-group">
                <label>Task</label>
                <select
                  value={reminderForm.task_id}
                  onChange={(e) => setReminderForm(prev => ({ ...prev, task_id: e.target.value }))}
                  required
                >
                  <option value="">Select Task</option>
                  {events.filter(e => e.resource?.type === 'task').map(e => (
                    <option key={e.resource.data.id} value={e.resource.data.id}>
                      {e.resource.data.title}
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
                  value={reminderForm.time_based}
                  onChange={(e) => setReminderForm(prev => ({ ...prev, time_based: e.target.value }))}
                  required
                />
              </div>
            )}
            
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Create Reminder</button>
              <button type="button" className="btn btn-outline" onClick={() => setShowReminderModal(false)}>
                Cancel
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Create Meeting Modal */}
      {showMeetingModal && (
        <Modal
          isOpen={showMeetingModal}
          onClose={() => setShowMeetingModal(false)}
          title="Create Meeting"
        >
          <form onSubmit={handleCreateMeeting} className="reminder-meeting-form">
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                value={meetingForm.title}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, title: e.target.value }))}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={meetingForm.description}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, description: e.target.value }))}
                rows="3"
              />
            </div>
            
            <div className="form-group">
              <label>Start Time *</label>
              <input
                type="datetime-local"
                value={meetingForm.start_time}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, start_time: e.target.value }))}
                required
              />
            </div>
            
            <div className="form-group">
              <label>End Time *</label>
              <input
                type="datetime-local"
                value={meetingForm.end_time}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, end_time: e.target.value }))}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Location</label>
              <input
                type="text"
                value={meetingForm.location}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, location: e.target.value }))}
                placeholder="e.g., Conference Room A, Zoom Link"
              />
            </div>
            
            <div className="form-group">
              <label>Project (Optional)</label>
              <select
                value={meetingForm.project_id}
                onChange={(e) => setMeetingForm(prev => ({ ...prev, project_id: e.target.value }))}
              >
                <option value="">No Project</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Invite Users</label>
              <select
                multiple
                value={meetingForm.invite_user_ids.map(String)}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => {
                    const val = parseInt(option.value, 10);
                    return Number.isInteger(val) && val > 0 ? val : null;
                  }).filter(id => id !== null);
                  setMeetingForm(prev => ({ ...prev, invite_user_ids: selected }));
                }}
                style={{ minHeight: '100px' }}
              >
                {getAvailableUsersForInvitation().length > 0 ? (
                  getAvailableUsersForInvitation().map(u => (
                    <option key={u.id} value={String(u.id)}>{u.name}</option>
                  ))
                ) : (
                  <option disabled>No users available to invite</option>
                )}
              </select>
              <small>
                Hold Ctrl/Cmd to select multiple users
                {meetingForm.invite_user_ids.length > 0 && (
                  <span style={{ display: 'block', marginTop: '4px', color: 'var(--primary-color)' }}>
                    {meetingForm.invite_user_ids.length} user(s) selected
                  </span>
                )}
                {(user?.role === 'Team Lead' || user?.role === 'Manager') && 
                  ' (limited to users in your projects)'}
              </small>
            </div>
            
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Create Meeting</button>
              <button type="button" className="btn btn-outline" onClick={() => setShowMeetingModal(false)}>
                Cancel
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Meeting Invitation Modal */}
      {showMeetingInvitationModal && (
        <Modal
          isOpen={showMeetingInvitationModal}
          onClose={() => setShowMeetingInvitationModal(false)}
          title="Meeting Invitations"
        >
          <div className="invitations-list">
            {pendingInvitations.length === 0 ? (
              <p>No pending invitations</p>
            ) : (
              pendingInvitations.map((invitation) => (
                <div key={invitation.id} className="invitation-item">
                  <div className="invitation-header">
                    <strong>{invitation.meeting.title}</strong>
                    <span className="invitation-status">Pending</span>
                  </div>
                  <p><strong>Organizer:</strong> {invitation.meeting.creator_name}</p>
                  <p><strong>Time:</strong> {moment(invitation.meeting.start_time).format('MMMM DD, YYYY HH:mm')} - {moment(invitation.meeting.end_time).format('HH:mm')}</p>
                  {invitation.meeting.location && (
                    <p><strong>Location:</strong> {invitation.meeting.location}</p>
                  )}
                  {invitation.meeting.description && (
                    <p><strong>Description:</strong> {invitation.meeting.description}</p>
                  )}
                  
                  <InvitationResponseForm
                    invitation={invitation}
                    onRespond={handleRespondToInvitation}
                  />
                </div>
              ))
            )}
          </div>
        </Modal>
      )}

      {/* Day Events Modal */}
      {showDayEventsModal && selectedDate && (
        <Modal
          isOpen={showDayEventsModal}
          onClose={() => {
            setShowDayEventsModal(false);
            setSelectedDate(null);
            setDayEvents([]);
          }}
          title={`Events for ${moment(selectedDate).format('MMMM DD, YYYY')}`}
        >
          <div className="day-events-list">
            {dayEvents.length === 0 ? (
              <p className="text-light">No events scheduled for this day</p>
            ) : (
              dayEvents.map((event, index) => (
                <div 
                  key={event.id || index} 
                  className="day-event-item"
                  onClick={() => {
                    handleEventClick(event);
                    setShowDayEventsModal(false);
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="day-event-header">
                    <strong>{event.title}</strong>
                    <span className={`event-type-badge ${event.resource?.type || 'task'}`}>
                      {event.resource?.type === 'meeting' ? '👥 Meeting' : 
                       event.resource?.type === 'reminder' ? '🔔 Reminder' : 
                       '📋 Task'}
                    </span>
                  </div>
                  <div className="day-event-time">
                    {moment(event.start).format('HH:mm')}
                    {event.end && ` - ${moment(event.end).format('HH:mm')}`}
                  </div>
                  {event.resource?.type === 'task' && (
                    <div className="day-event-details">
                      <span className={`priority-badge priority-${event.priority}`}>
                        {event.priority}
                      </span>
                      <span className={`status-badge status-${event.status}`}>
                        {event.status}
                      </span>
                    </div>
                  )}
                  {event.resource?.type === 'meeting' && event.resource.data.location && (
                    <div className="day-event-details">
                      📍 {event.resource.data.location}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};

// Separate component for invitation response
const InvitationResponseForm = ({ invitation, onRespond }) => {
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  const handleConfirm = () => {
    onRespond(invitation, 'confirmed');
  };

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    onRespond(invitation, 'rejected', rejectionReason);
    setShowRejectForm(false);
    setRejectionReason('');
  };

  return (
    <div className="invitation-actions">
      {!showRejectForm ? (
        <>
          <button className="btn btn-primary btn-sm" onClick={handleConfirm}>
            Confirm
          </button>
          <button className="btn btn-outline btn-sm" onClick={() => setShowRejectForm(true)}>
            Reject
          </button>
        </>
      ) : (
        <div className="reject-form">
          <textarea
            placeholder="Please provide a reason for rejecting this meeting invitation..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            rows="3"
            required
          />
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button className="btn btn-primary btn-sm" onClick={handleReject}>
              Submit Rejection
            </button>
            <button className="btn btn-outline btn-sm" onClick={() => {
              setShowRejectForm(false);
              setRejectionReason('');
            }}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarPage;

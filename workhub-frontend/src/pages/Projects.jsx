import React, { useEffect, useMemo, useState } from 'react';
import { projectsAPI, sprintsAPI, tasksAPI, projectMembersAPI, usersAPI } from '../services/api';
import { useDebounce } from '../hooks/useDebounce';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useModal } from '../hooks/useModal';
import Modal from '../components/Modal';

export default function Projects() {
  const { user, isAdmin } = useAuth();
  const { addToast } = useToast();
  const { modalState, showConfirm, closeModal } = useModal();
  const [expandedProjectId, setExpandedProjectId] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 400);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      let data;
      if (isAdmin()) {
        ({ data } = await projectsAPI.getAll(debouncedSearch ? { search: debouncedSearch } : undefined));
      } else {
        ({ data } = await projectsAPI.getMine());
        if (debouncedSearch) {
          const s = debouncedSearch.toLowerCase();
          data = Array.isArray(data) ? data.filter(p => (p.name || '').toLowerCase().includes(s)) : [];
        }
      }
      setProjects(data);
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to load projects');
      addToast('Failed to load projects', { type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [debouncedSearch]);

  return (
    <div className="page projects">
      <div className="page-header">
        <h2 style={{ display:'flex', alignItems:'center', gap:8 }}>
          Projects <span className="badge badge-count">{projects.length}</span>
        </h2>
        <div className="actions" style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
          <div className="searchbar" style={{ display:'flex', alignItems:'center', gap:8, border:'1px solid var(--border-color)', borderRadius:8, padding:'6px 10px', background:'#fff', minWidth:260 }}>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search projects by name..."
              style={{ border:'none', outline:'none', flex:1, background:'transparent' }}
            />
          </div>
          <button className="btn btn-outline" onClick={load}>Refresh</button>
          {isAdmin() && (
            <button className="btn btn-primary" onClick={() => setShowCreate(true)} style={{ marginLeft: 0 }}>Add Project</button>
          )}
        </div>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && (
        <div className="cards">
          {projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onChanged={load}
              user={user}
              isAdmin={isAdmin}
              expanded={expandedProjectId === p.id}
              onToggle={() => setExpandedProjectId(prev => (prev === p.id ? null : p.id))}
              showConfirm={showConfirm}
            />
          ))}
          {projects.length === 0 && <div>No projects found.</div>}
        </div>
      )}

      {/* Shared modal for confirmations */}
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

      {showCreate && (
        <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Create Project</h3>
            <div className="form-row">
              <label>Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="form-row">
              <label>Description</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div style={{ display:'flex', gap:8, marginTop:12 }}>
              <button onClick={() => setShowCreate(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                style={{ background:'#68939d', borderColor:'#68939d', color:'#fff' }}
                onClick={async () => {
                  try {
                    await projectsAPI.create({ name: form.name, description: form.description });
                    setShowCreate(false);
                    setForm({ name: '', description: '' });
                    await load();
                    addToast('Project created', { type: 'success' });
                  } catch (e) {
                    addToast(e?.response?.data?.error || 'Failed to create project', { type: 'error' });
                  }
                }}
                disabled={!form.name.trim()}
              >Create</button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .modal-backdrop { position:fixed; inset:0; background:rgba(0,0,0,.4); display:flex; align-items:center; justify-content:center; }
        .modal { background:#fff; padding:16px; border-radius:12px; width: 520px; max-width: 92vw; box-shadow: var(--shadow-lg); }
        .form-row { display:flex; flex-direction:column; gap:8px; margin:10px 0; }
        .form-row label { font-weight:600; color: var(--text-color); }
        .form-row input, .form-row textarea, .form-row select { padding:10px 12px; border:1px solid var(--border-color); border-radius:8px; font-size:14px; }
        .form-row input:focus, .form-row textarea:focus, .form-row select:focus { outline:none; border-color:#68939d; box-shadow:0 0 0 2px rgba(104,147,157,0.2); }
        .cards { display:grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
        .card { padding:0; overflow:hidden; border:1px solid var(--border-color); background:#fff; border-radius:12px; }
        .card-header { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; background:#f7fafc; border-bottom:1px solid var(--border-color); cursor:pointer; }
        .card-header .title { font-weight:700; }
        .card-header .subtitle { font-size:12px; color:var(--text-light); }
        .card-body { padding:16px 18px; display:grid; gap:16px; background:#fff; }
        .members h4, .sprints h4 { margin:0 0 8px 0; }
        .members ul { list-style:none; padding:0; margin:0; display:grid; gap:8px; }
        .members li { padding:10px 12px; background:#f9fbfc; border:1px solid var(--border-color); border-radius:10px; }
        .sprint { border:1px solid var(--border-color); border-radius:8px; padding:8px 10px; background:#fafafa; }
        .sprint-title { font-weight:600; }
        .sprint-dates { font-size:12px; color:var(--text-light); }
        .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:600; }
        .badge-count { background:#e0eef1; color:#4f7e86; }
      `}</style>
    </div>
  );
}

function ProjectCard({ project, onChanged, user, isAdmin, expanded, onToggle, showConfirm }) {
  const [sprints, setSprints] = useState([]);
  const [members, setMembers] = useState([]);
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMemberId, setNewMemberId] = useState('');
  const [users, setUsers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [taskForm, setTaskForm] = useState({ title: '', description: '', priority: 'medium', assigned_to: '', due_date: '' });
  const [taskFilters, setTaskFilters] = useState({ status: '', priority: '' });
  const [taskPage, setTaskPage] = useState(1);
  const taskPageSize = 3; // fixed per requirements
  const [taskMeta, setTaskMeta] = useState(null);
  const filteredTasks = useMemo(() => tasks, [tasks]);
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState({ name: project.name || '', description: project.description || '', owner_id: project.owner_id || '' });

  const loadSprints = async () => {
    try {
      const { data } = await sprintsAPI.getAll({ project_id: project.id });
      setSprints(data);
    } catch (_) {
      setSprints([]);
    }
  };

  const loadMembers = async () => {
    try {
      const { data } = await projectMembersAPI.list(project.id);
      setMembers(Array.isArray(data) ? data : []);
    } catch (_) {
      setMembers([]);
    }
  };

  const loadTasks = async () => {
    try {
      const params = { project_id: project.id, page: taskPage, page_size: taskPageSize };
      if (taskFilters.status) params.status = taskFilters.status;
      if (taskFilters.priority) params.priority = taskFilters.priority;
      const { data } = await tasksAPI.getAll(params);
      if (Array.isArray(data.items)) {
        setTasks(data.items);
        setTaskMeta(data.meta || null);
      } else {
        setTasks(Array.isArray(data) ? data : []);
        setTaskMeta(null);
      }
    } catch (_) {
      setTasks([]);
      setTaskMeta(null);
    }
  };

  useEffect(() => {
    if (expanded) {
      loadSprints();
      loadMembers();
      loadTasks();
      if (isAdmin() || user?.role === 'manager') {
        usersAPI.getAll().then(({ data }) => setUsers(Array.isArray(data) ? data : [])).catch(() => setUsers([]));
      }
    }
  }, [expanded, taskPage, taskFilters]);

  // Ensure owner dropdown has options when edit opens (admin only)
  useEffect(() => {
    if (showEdit && isAdmin() && users.length === 0) {
      usersAPI.getAll().then(({ data }) => setUsers(Array.isArray(data) ? data : [])).catch(() => setUsers([]));
    }
  }, [showEdit]);

  return (
    <div className="card">
      <div className="card-header" onClick={onToggle}>
        <div>
          <div className="title">{project.name}</div>
          <div className="subtitle">Owner: {project.owner_name || '—'}</div>
        </div>
        <div className="meta" style={{ display:'flex', alignItems:'center', gap:8 }}>
          <span>{new Date(project.created_at).toLocaleDateString()}</span>
          {isAdmin() && (
            <button
              className="btn btn-outline btn-sm"
              onClick={(e) => { e.stopPropagation(); setEditForm({ name: project.name || '', description: project.description || '', owner_id: project.owner_id || '' }); setShowEdit(true); }}
              title="Edit project"
            >Edit</button>
          )}
        </div>
      </div>
      {expanded && (
        <div className="card-body">
          <p>{project.description || 'No description'}</p>
          <div className="members">
            <h4>Members</h4>
            {members.length === 0 && <div>No members</div>}
            <ul>
              {members.map(m => (
                <li key={m.user_id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', gap:8 }}>
                  <span>{m.name || m.email}</span>
                  {(isAdmin() || (user?.role === 'manager')) && (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={async () => {
                        const confirmed = await showConfirm('Remove this member from project?', 'Remove Member');
                        if (!confirmed) return;
                        try {
                          await projectMembersAPI.remove(project.id, m.user_id);
                          await loadMembers();
                          onChanged && onChanged();
                        } catch (e) {}
                      }}
                    >Remove</button>
                  )}
                </li>
              ))}
            </ul>
            {isAdmin() && (
              <button onClick={() => setShowAddMember(true)} className="btn btn-primary" style={{ marginTop:8, background:'#68939d', borderColor:'#68939d' }}>
                Assign Member
              </button>
            )}
          </div>
          <div className="sprints" style={{ marginTop: 12 }}>
            <h4>Tasks</h4>
            <div style={{ display:'flex', flexWrap:'wrap', gap:8, alignItems:'center', marginBottom:8 }}>
              <span className="badge badge-count">{taskMeta ? `${tasks.length} / ${taskMeta.total_items}` : `${filteredTasks.length}`} shown</span>
              <select className="form-select" value={taskFilters.status} onChange={(e)=> { setTaskFilters({ ...taskFilters, status: e.target.value }); setTaskPage(1); }} style={{ maxWidth:160 }}>
                <option value="">All Statuses</option>
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
              <select className="form-select" value={taskFilters.priority} onChange={(e)=> { setTaskFilters({ ...taskFilters, priority: e.target.value }); setTaskPage(1); }} style={{ maxWidth:160 }}>
                <option value="">All Priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              <div style={{ marginLeft:'auto', display:'flex', gap:8, alignItems:'center' }}>
                <button className="btn btn-outline" disabled={taskMeta && !taskMeta.has_prev} onClick={() => setTaskPage(p => Math.max(1, p - 1))}>Prev</button>
                <span style={{ color:'var(--text-light)' }}>{taskMeta ? `Page ${taskMeta.page} of ${taskMeta.total_pages || 1}` : ''}</span>
                <button className="btn btn-outline" disabled={taskMeta && !taskMeta.has_next} onClick={() => setTaskPage(p => p + 1)}>Next</button>
              </div>
            </div>
            <div style={{ display:'grid', gap:8 }}>
              {filteredTasks.map(t => (
                <div key={t.id} style={{ border:'1px solid var(--border-color)', borderRadius:6, padding:10, background:'#fff' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', gap:12, flexWrap:'wrap' }}>
                    <div style={{ fontWeight:600 }}>{t.title}</div>
                    <div style={{ display:'flex', gap:8, alignItems:'center', flexWrap:'wrap' }}>
                      <span className={`badge badge-${t.priority}`}>{t.priority}</span>
                      {(isAdmin() || user?.role === 'manager' || user?.role === 'team_lead') && (
                        <>
                          <select
                            className="form-select"
                            value={t.status}
                            onChange={async (e) => {
                              const newStatus = e.target.value;
                              try {
                                await tasksAPI.update(t.id, { status: newStatus });
                                await loadTasks();
                              } catch (err) {}
                            }}
                            style={{ maxWidth:150 }}
                          >
                            <option value="todo">To Do</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                          </select>
                          <select
                            className="form-select"
                            value={t.priority}
                            onChange={async (e) => {
                              const newPriority = e.target.value;
                              try {
                                await tasksAPI.update(t.id, { priority: newPriority });
                                await loadTasks();
                              } catch (err) {}
                            }}
                            style={{ maxWidth:140 }}
                          >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                          </select>
                        </>
                      )}
                    </div>
                  </div>
                  <div style={{ fontSize:12, color:'var(--text-light)' }}>
                    Status: {t.status.replace('_',' ')}{t.assignee_name ? ` • Assignee: ${t.assignee_name}` : ''}
                  </div>
                </div>
              ))}
              {filteredTasks.length === 0 && <div style={{ color:'var(--text-light)'}}>No tasks match current filters</div>}
            </div>
          </div>
          <div className="sprints">
            <h4>Sprints</h4>
            {sprints.length === 0 && <div>No sprints</div>}
            {sprints.map((s) => (
              <div key={s.id} className="sprint">
                <div className="sprint-title">{s.name}</div>
                <div className="sprint-dates">
                  {new Date(s.start_date).toLocaleDateString()} → {new Date(s.end_date).toLocaleDateString()}
                </div>
                <div className="sprint-goal">{s.goal || '—'}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {showAddMember && (
        <div className="modal-backdrop" onClick={() => setShowAddMember(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Assign Member</h3>
            {(isAdmin() || user?.role === 'manager') && users.length > 0 ? (
              <div className="form-row">
                <label>User</label>
                <select value={newMemberId} onChange={(e) => setNewMemberId(e.target.value)}>
                  <option value="">Select user</option>
                  {users.map(u => (<option key={u.id} value={u.id}>{u.name} ({u.email})</option>))}
                </select>
              </div>
            ) : (
              <div className="form-row">
                <label>User ID</label>
                <input value={newMemberId} onChange={(e) => setNewMemberId(e.target.value)} placeholder="Enter user ID" />
              </div>
            )}
            <div style={{ display:'flex', gap:8, marginTop:12 }}>
              <button onClick={() => setShowAddMember(false)} className="btn btn-outline">Cancel</button>
              <button
                className="btn btn-primary"
                style={{ background:'#68939d', borderColor:'#68939d', color:'#fff' }}
                onClick={async () => {
                  try {
                    const uid = Number(newMemberId);
                    if (!uid) return;
                    await projectMembersAPI.add(project.id, { user_id: uid });
                    {
                      setShowAddMember(false);
                      setNewMemberId('');
                      await loadMembers();
                      onChanged && onChanged();
                    }
                  } catch (e) {}
                }}
                disabled={!newMemberId}
              >Assign</button>
            </div>
          </div>
        </div>
      )}
      {showEdit && (
        <div className="modal-backdrop" onClick={() => setShowEdit(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Project</h3>
            <div className="form-row">
              <label>Name</label>
              <input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
            </div>
            <div className="form-row">
              <label>Description</label>
              <textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} />
            </div>
            {isAdmin() && (
              <div className="form-row">
                <label>Owner</label>
                <select value={editForm.owner_id || ''} onChange={(e) => setEditForm({ ...editForm, owner_id: e.target.value })}>
                  <option value="">Unassigned</option>
                  {users
                    .filter(u => ['admin','super_admin'].includes((u.role || '').toLowerCase()))
                    .map(u => (<option key={u.id} value={u.id}>{u.name} ({u.email})</option>))}
                </select>
              </div>
            )}
            <div style={{ display:'flex', gap:8, marginTop:12 }}>
              <button onClick={() => setShowEdit(false)} className="btn btn-outline">Cancel</button>
              <button
                className="btn btn-primary"
                style={{ background:'#68939d', borderColor:'#68939d', color:'#fff' }}
                onClick={async () => {
                  try {
                    const payload = { name: editForm.name, description: editForm.description, owner_id: editForm.owner_id ? Number(editForm.owner_id) : null };
                    await projectsAPI.update(project.id, payload);
                    setShowEdit(false);
                    await onChanged();
                  } catch (e) {}
                }}
                disabled={!editForm.name.trim()}
              >Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



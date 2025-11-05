import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { tasksAPI } from '../services/api';

const STATUSES = [
  { key: 'todo', title: 'To Do' },
  { key: 'in_progress', title: 'In Progress' },
  { key: 'completed', title: 'Completed' },
];

const Kanban = () => {
  const { user, isAdmin } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [draggedTask, setDraggedTask] = useState(null);

  const canEditTask = (task) => {
    if (!user) return false;
    return isAdmin() || task.assigned_to === user.id;
  };

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const res = await tasksAPI.getAll();
      setTasks(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error('Failed to load tasks', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const columns = useMemo(() => {
    const map = { todo: [], in_progress: [], completed: [] };
    for (const t of tasks) {
      (map[t.status] || map.todo).push(t);
    }
    return map;
  }, [tasks]);

  const onDragStart = (task) => setDraggedTask(task);
  const onDragEnd = () => setDraggedTask(null);

  const onDropTo = async (status) => {
    if (!draggedTask) return;
    if (draggedTask.status === status) return setDraggedTask(null);
    try {
      await tasksAPI.update(draggedTask.id, { status });
      setTasks((prev) => prev.map((t) => (t.id === draggedTask.id ? { ...t, status } : t)));
    } catch (e) {
      await fetchTasks(selectedProjectId);
    } finally {
      setDraggedTask(null);
    }
  };

  if (loading) return <div className="spinner" />;

  return (
    <div className="kanban-page">
        <div className="page-header" style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <h1>Kanban Board</h1>
        </div>

        <div className="kanban-board">
          {STATUSES.map((col) => (
            <div
              key={col.key}
              className={`kanban-column status-${col.key}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => onDropTo(col.key)}
            >
              <div className="kanban-column-header">
                <h3>{col.title}</h3>
                <span className="count">{columns[col.key]?.length || 0}</span>
              </div>
              <div className="kanban-column-body">
                {(columns[col.key] || []).map((task) => (
                  <div
                    key={task.id}
                    className={`kanban-card ${canEditTask(task) ? 'draggable' : 'readonly'}`}
                    draggable={canEditTask(task)}
                    onDragStart={() => onDragStart(task)}
                    onDragEnd={onDragEnd}
                    title={canEditTask(task) ? 'Drag to change status' : 'You cannot move this task'}
                  >
                    <div className="kanban-card-title">{task.title}</div>
                    <div className="kanban-card-meta">
                      <span className={`badge badge-${task.priority}`}>{task.priority}</span>
                      {Array.isArray(task.blocked_by) && task.blocked_by.some(b => b.status !== 'completed') && (
                        <span className="badge badge-danger">Blocked</span>
                      )}
                    </div>
                    {task.assignee_name && (
                      <div className="kanban-card-assignee">{task.assignee_name}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      
      <style>{`
        .kanban-board { display:grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .kanban-column { background:#fff; border:1px solid #eee; border-radius:10px; min-height: 60vh; display:flex; flex-direction:column; }
        .kanban-column-header { display:flex; justify-content:space-between; align-items:center; padding:12px 14px; border-bottom:1px solid #eee; }
        .kanban-column-body { padding:12px; display:flex; flex-direction:column; gap:12px; }
        .kanban-card { background:#fafafa; border:1px solid #e5e7eb; border-radius:10px; padding:10px; cursor:grab; }
        .kanban-card.readonly { opacity: .75; cursor: not-allowed; }
        .kanban-card-title { font-weight:600; margin-bottom:6px; }
        .kanban-card-meta { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
        .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:600; }
        .badge-low { background:#e8f5e9; color:#065f46; }
        .badge-medium { background:#fff7ed; color:#92400e; }
        .badge-high { background:#fee2e2; color:#991b1b; }
        .badge-danger { background:#fee2e2; color:#991b1b; }
        .count { color:#6b7280; font-size:12px; }
        @media (max-width: 900px) { .kanban-board { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

export default Kanban;



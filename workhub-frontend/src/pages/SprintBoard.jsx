import React, { useEffect, useMemo, useState } from 'react';
import { sprintsAPI, tasksAPI } from '../services/api';

export default function SprintBoard() {
  const [sprintId, setSprintId] = useState('');
  const [sprints, setSprints] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadSprints = async () => {
    try {
      const { data } = await sprintsAPI.getAll();
      setSprints(data);
    } catch (_) {
      setSprints([]);
    }
  };

  const loadTasks = async (sid) => {
    if (!sid) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await tasksAPI.getAll({ sprint_id: sid });
      setTasks(data);
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSprints(); }, []);
  useEffect(() => { loadTasks(sprintId); }, [sprintId]);

  const grouped = useMemo(() => {
    const by = { todo: [], in_progress: [], completed: [] };
    tasks.forEach(t => { (by[t.status] || (by[t.status] = [])).push(t); });
    return by;
  }, [tasks]);

  return (
    <div className="page sprint-board">
      <div className="page-header">
        <h2>Sprint Board</h2>
        <div className="actions">
          <select value={sprintId} onChange={(e) => setSprintId(e.target.value)}>
            <option value="">Select sprint…</option>
            {sprints.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>
      {loading && <div>Loading…</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && sprintId && (
        <div className="kanban-grid">
          {['todo','in_progress','completed'].map(col => (
            <div className="kanban-column" key={col}>
              <div className="kanban-title">{col.replace('_',' ')}</div>
              {grouped[col]?.map(t => (
                <div key={t.id} className="kanban-card">
                  <div className="title">{t.title}</div>
                  <div className="meta">{t.priority} • {t.assignee_name || 'Unassigned'}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}



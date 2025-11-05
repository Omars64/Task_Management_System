import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { reportsAPI, projectsAPI, sprintsAPI } from '../services/api';
import { FiDownload, FiPieChart, FiClock, FiTrendingUp } from 'react-icons/fi';
import { useModal } from '../hooks/useModal';
import Modal from '../components/Modal';

const Reports = () => {
  const { isAdmin } = useAuth();
  const { modalState, showError, showSuccess, closeModal } = useModal();
  const [activeTab, setActiveTab] = useState('overview');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [burndown, setBurndown] = useState(null);
  const [velocity, setVelocity] = useState(null);
  const [projects, setProjects] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [filters, setFilters] = useState({ project_id: '', sprint_id: '' });
  const [exportParams, setExportParams] = useState({ period: 'daily', start_date: '', end_date: '' });
  const [dailyStats, setDailyStats] = useState(null);
  const [overdue, setOverdue] = useState(null);
  const [topProjects, setTopProjects] = useState([]);

  useEffect(() => {
    // preload projects for admin filters
    (async () => {
      if (isAdmin()) {
        try { const { data } = await projectsAPI.getAll(); setProjects(Array.isArray(data) ? data : []); } catch (_) {}
      }
    })();
  }, [isAdmin]);

  useEffect(() => {
    fetchReportData();
  }, [activeTab, filters]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      let response;
      const commonParams = {};
      if (filters.project_id) commonParams.project_id = filters.project_id;
      if (filters.sprint_id) commonParams.sprint_id = filters.sprint_id;

      if (activeTab === 'overview') {
        response = isAdmin()
          ? await reportsAPI.getAdminOverview(commonParams)
          : await reportsAPI.getPersonalTaskStatus();
        if (isAdmin()) {
          try {
            const ds = await reportsAPI.getDailyStats({ days: 14, ...commonParams });
            setDailyStats(ds?.data || null);
            const ov = await reportsAPI.getOverdue({ limit: 20, ...commonParams });
            setOverdue(ov?.data || null);
            const tp = await reportsAPI.getTopProjectsThroughput({ days: 14 });
            setTopProjects(tp?.data || []);
          } catch (_) { setDailyStats(null); setOverdue(null); setTopProjects([]); }
        }
      } else if (activeTab === 'activity') {
        response = await reportsAPI.getPersonalActivity(30);
      } else if (activeTab === 'sprint' && isAdmin()) {
        response = await reportsAPI.getSprintSummary(14);
        try {
          const [b, v] = await Promise.all([
            reportsAPI.getSprintBurndown(commonParams.project_id || commonParams.sprint_id ? commonParams : { days: 14 }),
            reportsAPI.getSprintVelocity(commonParams.project_id || commonParams.sprint_id ? {} : { weeks: 4 }),
          ]);
          setBurndown(b?.data || null);
          setVelocity(v?.data || null);
        } catch (_) {
          setBurndown(null);
          setVelocity(null);
        }
      }

      setReportData(response?.data || null);
    } catch (error) {
      console.error('Failed to fetch report data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await reportsAPI.exportToCSV('tasks');
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tasks_report_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      showSuccess('Report exported successfully!', 'Export Complete');
    } catch (error) {
      showError('Failed to export report. Please try again.', 'Export Failed');
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:12, flexWrap:'wrap' }}>
        <h1>Reports</h1>
        <div style={{ display:'flex', gap:8, alignItems:'center' }}>
          {isAdmin() && (
            <>
              <select
                className="form-select"
                value={filters.project_id}
                onChange={async (e) => {
                  const project_id = e.target.value;
                  setFilters({ project_id, sprint_id: '' });
                  if (project_id) {
                    try { const { data } = await sprintsAPI.getAll({ project_id }); setSprints(Array.isArray(data) ? data : []); } catch (_) { setSprints([]); }
                  } else { setSprints([]); }
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
            </>
          )}
          <button className="btn btn-primary" onClick={handleExportCSV}>
            <FiDownload /> Export CSV
          </button>
        </div>
      </div>

      <div className="card">
        <div style={{ borderBottom: '1px solid var(--border-color)', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '24px' }}>
            <button
              onClick={() => setActiveTab('overview')}
              style={{
                padding: '12px 0',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'overview' ? '2px solid var(--primary-color)' : 'none',
                color: activeTab === 'overview' ? 'var(--primary-color)' : 'var(--text-light)',
                cursor: 'pointer',
                fontWeight: 500
              }}
            >
              <FiPieChart style={{ marginRight: '8px' }} />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              style={{
                padding: '12px 0',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'activity' ? '2px solid var(--primary-color)' : 'none',
                color: activeTab === 'activity' ? 'var(--primary-color)' : 'var(--text-light)',
                cursor: 'pointer',
                fontWeight: 500
              }}
            >
              <FiTrendingUp style={{ marginRight: '8px' }} />
              Activity
            </button>
            {isAdmin() && (
              <button
                onClick={() => setActiveTab('sprint')}
                style={{
                  padding: '12px 0',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'sprint' ? '2px solid var(--primary-color)' : 'none',
                  color: activeTab === 'sprint' ? 'var(--primary-color)' : 'var(--text-light)',
                  cursor: 'pointer',
                  fontWeight: 500
                }}
              >
                <FiClock style={{ marginRight: '8px' }} />
                Sprint Summary
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="spinner" />
        ) : (
          <>
            {activeTab === 'overview' && reportData && (
              <div>
                <h3 style={{ marginBottom: '20px' }}>Task Status Overview</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--primary-color)' }}>
                      {reportData.status_counts?.total || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Total Tasks</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--success-color)' }}>
                      {reportData.status_counts?.completed || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Completed</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--warning-color)' }}>
                      {reportData.status_counts?.in_progress || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>In Progress</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--danger-color)' }}>
                      {reportData.status_counts?.todo || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>To Do</div>
                  </div>
                </div>

                {isAdmin() && reportData.tasks_by_user && (
                  <div style={{ marginTop: 24 }}>
                    <h3 style={{ marginBottom: 12 }}>Tasks by User</h3>
                    <div style={{ overflowX:'auto' }}>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>User</th>
                            <th style={{ textAlign:'right' }}>Tasks</th>
                          </tr>
                        </thead>
                        <tbody>
                          {reportData.tasks_by_user.map((u) => (
                            <tr key={u.user_id}>
                              <td>{u.user_name || u.user_id}</td>
                              <td style={{ textAlign:'right' }}>{u.task_count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'activity' && reportData && (
              <div>
                <h3 style={{ marginBottom: '20px' }}>Activity (Last 30 Days)</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--primary-color)' }}>
                      {reportData.total_tasks || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Tasks Assigned</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--success-color)' }}>
                      {reportData.completed_tasks || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Completed</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--warning-color)' }}>
                      {Math.round(reportData.completion_rate || 0)}%
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Completion Rate</div>
                  </div>
                </div>

                {/* Charts */}
                <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(280px, 1fr))', gap:16, marginTop:16 }}>
                  <PieChart
                    title="Status"
                    id="status-pie"
                    data={[
                      { label:'To Do', value: reportData.status_counts?.todo || 0, color:'#9CA3AF' },
                      { label:'In Progress', value: reportData.status_counts?.in_progress || 0, color:'#F59E0B' },
                      { label:'Completed', value: reportData.status_counts?.completed || 0, color:'#10B981' },
                    ]}
                  />
                  <PieChart
                    title="Priority"
                    id="priority-pie"
                    data={[
                      { label:'Low', value: reportData.priority_counts?.low || 0, color:'#10B981' },
                      { label:'Medium', value: reportData.priority_counts?.medium || 0, color:'#F59E0B' },
                      { label:'High', value: reportData.priority_counts?.high || 0, color:'#EF4444' },
                    ]}
                  />
                </div>

                {dailyStats && (
                  <div style={{ marginTop:16 }}>
                    <LineChart
                      title="Created vs Completed (Last 14 Days)"
                      id="created-completed-line"
                      series={dailyStats.series}
                    />
                  </div>
                )}

                {/* Overdue and Top Projects */}
                <div style={{ display:'grid', gridTemplateColumns:'1.2fr 0.8fr', gap:16, marginTop:16 }}>
                  <div>
                    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                      <h4>Overdue Tasks</h4>
                      <span className="badge badge-count">{overdue?.count || 0}</span>
                    </div>
                    <div style={{ overflowX:'auto' }}>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Title</th>
                            <th>Due</th>
                            <th>Priority</th>
                            <th>Assignee</th>
                            <th>Project</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(overdue?.tasks || []).map(t => (
                            <tr key={t.id}>
                              <td>{t.title}</td>
                              <td>{t.due_date ? new Date(t.due_date).toLocaleDateString() : ''}</td>
                              <td>{t.priority}</td>
                              <td>{t.assignee || '—'}</td>
                              <td>{t.project || '—'}</td>
                            </tr>
                          ))}
                          {(overdue?.tasks || []).length === 0 && (
                            <tr><td colSpan="5" style={{ color:'var(--text-light)' }}>No overdue tasks</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div>
                    <h4>Top Projects by Throughput (14 days)</h4>
                    <div style={{ display:'grid', gap:8 }}>
                      {topProjects.map((p, idx) => (
                        <div key={p.project_id} style={{ border:'1px solid var(--border-color)', borderRadius:8, padding:10, background:'#fff', display:'flex', justifyContent:'space-between' }}>
                          <div><strong>{idx+1}. {p.project_name}</strong></div>
                          <div><span className="badge badge-count">{p.completed} completed</span></div>
                        </div>
                      ))}
                      {topProjects.length === 0 && <div style={{ color:'var(--text-light)' }}>No throughput data</div>}
                    </div>
                  </div>
                </div>

                {/* Export by period */}
                <div style={{ marginTop:20, display:'flex', gap:8, alignItems:'center', flexWrap:'wrap' }}>
                  <h4 style={{ marginRight:8 }}>Export by Period</h4>
                  <select className="form-select" value={exportParams.period} onChange={(e)=> setExportParams({ ...exportParams, period: e.target.value })}>
                    <option value="daily">Daily</option>
                    <option value="monthly">Monthly</option>
                    <option value="custom">Custom</option>
                  </select>
                  <input type="date" className="form-input" value={exportParams.start_date} onChange={(e)=> setExportParams({ ...exportParams, start_date: e.target.value })} />
                  <input type="date" className="form-input" value={exportParams.end_date} onChange={(e)=> setExportParams({ ...exportParams, end_date: e.target.value })} />
                  <button
                    className="btn btn-outline"
                    onClick={async () => {
                      try {
                        const params = {
                          period: exportParams.period,
                          ...(filters.project_id ? { project_id: filters.project_id } : {}),
                          ...(filters.sprint_id ? { sprint_id: filters.sprint_id } : {}),
                        };
                        if (exportParams.start_date) params.start_date = exportParams.start_date;
                        if (exportParams.end_date) params.end_date = exportParams.end_date;
                        const res = await reportsAPI.exportByPeriodCSV(params);
                        const url = window.URL.createObjectURL(new Blob([res.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', 'tasks_period_export.csv');
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                      } catch (_) {}
                    }}
                  >Export CSV</button>
                </div>
              </div>
            )}

            {activeTab === 'sprint' && reportData && (
              <div>
                <h3 style={{ marginBottom: '20px' }}>Sprint Summary ({reportData.sprint_days} days)</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--primary-color)' }}>
                      {reportData.total_tasks || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Sprint Tasks</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--success-color)' }}>
                      {reportData.completed || 0}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Completed</div>
                  </div>
                  <div style={{ padding: '20px', backgroundColor: 'var(--bg-color)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--warning-color)' }}>
                      {Math.round(reportData.completion_rate || 0)}%
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-light)' }}>Completion Rate</div>
                  </div>
                </div>
                {burndown && (
                  <div style={{ marginTop: 16 }}>
                    <h4>Burndown (Remaining Tasks)</h4>
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, maxWidth:520 }}>
                      <div style={{ fontWeight:600 }}>Date</div>
                      <div style={{ fontWeight:600 }}>Remaining</div>
                      {burndown.points.slice(-14).map((p) => (
                        <React.Fragment key={p.date}>
                          <div style={{ color:'var(--text-light)' }}>{p.date}</div>
                          <div>{p.remaining}</div>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                )}
                {velocity && (
                  <div style={{ marginTop: 16 }}>
                    <h4>Velocity (Completed/Week)</h4>
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, maxWidth:420 }}>
                      <div style={{ fontWeight:600 }}>Week</div>
                      <div style={{ fontWeight:600 }}>Completed</div>
                      {velocity.weekly.map((w, idx) => (
                        <React.Fragment key={`${w.year}-W${w.week}-${idx}`}>
                          <div style={{ color:'var(--text-light)' }}>{w.year}-W{w.week}</div>
                          <div>{w.completed}</div>
                        </React.Fragment>
                      ))}
                    </div>
                    <div style={{ marginTop:8, color:'var(--text-light)' }}>Average: {Math.round((velocity.average_completed_per_week || 0) * 10) / 10} tasks/week</div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

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

export default Reports;

// ------ Simple SVG charts (no extra deps) ------
function PieChart({ id, title, data }) {
  const total = data.reduce((s, d) => s + (Number(d.value) || 0), 0) || 1;
  let cumulative = 0;
  const radius = 70;
  const center = 80;
  const circumference = 2 * Math.PI * radius;
  const arcs = data.map((d, i) => {
    const val = Number(d.value) || 0;
    const portion = val / total;
    const length = portion * circumference;
    const dasharray = `${length} ${circumference - length}`;
    const offset = cumulative * circumference * -1;
    cumulative += portion;
    return { ...d, dasharray, offset };
  });

  return (
    <div style={{ background:'#fff', border:'1px solid var(--border-color)', borderRadius:8, padding:12 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
        <strong>{title}</strong>
      </div>
      <svg id={id} width="320" height="200" viewBox="0 0 320 200" xmlns="http://www.w3.org/2000/svg">
        <g transform={`translate(${center},${center})`}>
          {arcs.map((a, idx) => (
            <circle key={idx}
              r={radius}
              cx="0" cy="0"
              fill="transparent"
              stroke={a.color}
              strokeWidth="40"
              strokeDasharray={a.dasharray}
              strokeDashoffset={a.offset}
              transform="rotate(-90)"
            />
          ))}
        </g>
        <g transform="translate(170,20)" fontSize="12" fill="#374151">
          {data.map((d, i) => (
            <g key={i} transform={`translate(0, ${i * 18})`}>
              <rect width="12" height="12" fill={d.color} rx="2" />
              <text x="16" y="11">{d.label}: {d.value}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

function LineChart({ id, title, series }) {
  const width = 640; const height = 220; const padding = 32;
  const dates = series.map(s => s.date);
  const maxY = Math.max(1, ...series.map(s => Math.max(s.created, s.completed)));
  const x = (i) => padding + (i * (width - 2*padding)) / Math.max(1, series.length - 1);
  const y = (v) => height - padding - (v * (height - 2*padding)) / maxY;
  const pathFor = (key, color) => {
    let d = '';
    series.forEach((s, i) => { d += `${i===0?'M':'L'} ${x(i)} ${y(s[key])} `; });
    return (<path d={d} fill="none" stroke={color} strokeWidth="2" />);
  };
  return (
    <div style={{ background:'#fff', border:'1px solid var(--border-color)', borderRadius:8, padding:12 }}>
      <div style={{ marginBottom:8, fontWeight:600 }}>{title}</div>
      <svg id={id} width={width} height={height} xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width={width} height={height} fill="#ffffff" />
        {/* axes */}
        <line x1={padding} y1={height-padding} x2={width-padding} y2={height-padding} stroke="#e5e7eb" />
        <line x1={padding} y1={padding} x2={padding} y2={height-padding} stroke="#e5e7eb" />
        {pathFor('created', '#3B82F6')}
        {pathFor('completed', '#10B981')}
        {/* legend */}
        <g transform="translate(50,10)" fontSize="12" fill="#374151">
          <rect width="12" height="12" fill="#3B82F6" rx="2" />
          <text x="16" y="11">Created</text>
          <rect x="100" width="12" height="12" fill="#10B981" rx="2" />
          <text x="116" y="11">Completed</text>
        </g>
      </svg>
    </div>
  );
}
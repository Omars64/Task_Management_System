import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { reportsAPI } from '../services/api';
import { FiDownload, FiPieChart, FiClock, FiTrendingUp } from 'react-icons/fi';

const Reports = () => {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReportData();
  }, [activeTab]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      let response;
      
      if (activeTab === 'overview') {
        response = isAdmin() 
          ? await reportsAPI.getAdminOverview()
          : await reportsAPI.getPersonalTaskStatus();
      } else if (activeTab === 'activity') {
        response = await reportsAPI.getPersonalActivity(30);
      } else if (activeTab === 'sprint' && isAdmin()) {
        response = await reportsAPI.getSprintSummary(14);
      }
      
      setReportData(response?.data);
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
    } catch (error) {
      alert('Failed to export report');
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Reports</h1>
        <button className="btn btn-primary" onClick={handleExportCSV}>
          <FiDownload /> Export CSV
        </button>
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
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  {isAdmin() ? (
                    <>
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
                    </>
                  ) : (
                    <>
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
                    </>
                  )}
                </div>
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
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Reports;
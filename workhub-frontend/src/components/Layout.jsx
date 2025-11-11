import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { notificationsAPI, chatAPI } from '../services/api';
import { 
  FiHome, FiCheckSquare, FiUsers, FiBell, FiBarChart2, 
  FiSettings, FiLogOut, FiMenu, FiX, FiList, FiCalendar, FiClock, FiMessageCircle 
} from 'react-icons/fi';
import './Layout.css';

const Layout = () => {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [chatUnreadCount, setChatUnreadCount] = useState(0);

  useEffect(() => {
    fetchUnreadCount();
    fetchChatUnreadCount();
    const notifInterval = setInterval(fetchUnreadCount, 30000); // notifications every 30s
    const chatInterval = setInterval(fetchChatUnreadCount, 5000); // chat every 5s
    // Listen for notification updates from other components
    const onRefresh = () => fetchUnreadCount();
    window.addEventListener('notifications:refresh-count', onRefresh);
    return () => { 
      clearInterval(notifInterval); 
      clearInterval(chatInterval);
      window.removeEventListener('notifications:refresh-count', onRefresh);
    };
  }, []);

  // When route changes (e.g., navigating to /notifications), refresh badge immediately
  useEffect(() => {
    fetchUnreadCount();
  }, [location.pathname]);

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const fetchChatUnreadCount = async () => {
    try {
      const convsRes = await chatAPI.getConversations();
      const convs = convsRes.data || [];
      const total = convs.reduce((sum, c) => sum + (c.unread_count || 0), 0);
      setChatUnreadCount(total);
    } catch (error) {
      // silent fail to avoid spam
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: FiHome, show: true },
    { path: '/tasks', label: 'Tasks', icon: FiCheckSquare, show: true },
    { path: '/kanban', label: 'Kanban', icon: FiList, show: true },
    { path: '/calendar', label: 'Calendar', icon: FiCalendar, show: true },
    { path: '/projects', label: 'Projects', icon: FiList, show: true },
    { path: '/reminders-meetings', label: 'Reminders & Meetings', icon: FiClock, show: true },
    { path: '/chat', label: 'Chat', icon: FiMessageCircle, show: true, badge: chatUnreadCount },
    { path: '/groups', label: 'Groups', icon: FiUsers, show: true },
    { path: '/users', label: 'Users', icon: FiUsers, show: isAdmin() },
    { path: '/notifications', label: 'Notifications', icon: FiBell, show: true, badge: unreadCount },
    { path: '/reports', label: 'Reports', icon: FiBarChart2, show: true },
    { path: '/thingstodo', label: 'Things to do', icon: FiList, show: true },
    { path: '/settings', label: 'Settings', icon: FiSettings, show: true },
  ];

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h1 className="sidebar-title">Work Hub</h1>
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <FiX /> : <FiMenu />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {menuItems.filter(item => item.show).map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <item.icon className="nav-icon" />
              {sidebarOpen && (
                <>
                  <span className="nav-label">{item.label}</span>
                  {item.badge > 0 && (
                    <span className="nav-badge">{item.badge}</span>
                  )}
                </>
              )}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            {sidebarOpen && (
              <div className="user-details">
                <div className="user-name">{user?.name}</div>
                <div className="user-role">{user?.role}</div>
              </div>
            )}
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Logout">
            <FiLogOut />
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
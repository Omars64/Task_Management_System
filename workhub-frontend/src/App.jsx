import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import Users from './pages/Users';
import Notifications from './pages/Notifications';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import ThingsToDo from './pages/ThingsToDo';
import Kanban from './pages/Kanban';
import Projects from './pages/Projects';
import SprintBoard from './pages/SprintBoard';
import Calendar from './pages/Calendar';
import RemindersAndMeetings from './pages/RemindersAndMeetings';
import Chat from './pages/Chat';
import { ToastProvider } from './context/ToastContext';
import { I18nProvider } from './i18n';
import ToastContainer from './components/ToastContainer';

const PrivateRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="spinner" />;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && !['admin', 'super_admin'].includes(user.role)) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="kanban" element={<Kanban />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="projects" element={<Projects />} />
        <Route path="reminders-meetings" element={<RemindersAndMeetings />} />
        <Route path="chat" element={<Chat />} />
        <Route path="sprint-board" element={<SprintBoard />} />
        <Route path="users" element={
          <PrivateRoute adminOnly>
            <Users />
          </PrivateRoute>
        } />
        <Route path="notifications" element={<Notifications />} />
        <Route path="reports" element={<Reports />} />
        <Route path="thingstodo" element={<ThingsToDo />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <I18nProvider>
        <ToastProvider>
          <Router>
            <AppRoutes />
            <ToastContainer />
          </Router>
        </ToastProvider>
      </I18nProvider>
    </AuthProvider>
  );
}

export default App;
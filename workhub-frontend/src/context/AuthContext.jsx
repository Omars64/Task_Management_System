import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const response = await authAPI.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user:', error);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    localStorage.setItem('token', response.data.access_token);
    setUser(response.data.user);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  const isAdmin = () => {
    return user?.role === 'admin' || user?.role === 'super_admin';
  };

  const canCreateTasks = () => {
    const role = user?.role?.toLowerCase();
    return ['super_admin', 'admin', 'manager', 'team_lead', 'developer'].includes(role);
  };

  const canDeleteUsers = () => {
    const role = user?.role?.toLowerCase();
    return ['super_admin', 'admin'].includes(role);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    updateUser,
    isAdmin,
    canCreateTasks,
    canDeleteUsers,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
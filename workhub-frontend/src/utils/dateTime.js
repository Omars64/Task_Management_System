/**
 * Date and Time Utility Functions
 * 
 * This module provides consistent date/time formatting that respects the user's local timezone.
 * All dates from the backend are in UTC and need to be converted to local time for display.
 */

/**
 * Converts a UTC date string (ISO 8601) to a local Date object
 * Handles both timezone-aware and naive datetime strings
 * 
 * @param {string} utcDateString - ISO 8601 date string from backend (UTC)
 * @returns {Date} - Date object in local timezone
 */
export const utcToLocal = (utcDateString) => {
  if (!utcDateString) return null;
  
  // If the string already has timezone info (Z or +00:00), parse it directly
  if (utcDateString.includes('Z') || utcDateString.includes('+') || utcDateString.includes('-', 10)) {
    return new Date(utcDateString);
  }
  
  // If it's a naive datetime string (no timezone), treat it as UTC
  // Append 'Z' to indicate UTC
  return new Date(utcDateString + 'Z');
};

/**
 * Formats a UTC date string to local date string
 * 
 * @param {string} utcDateString - ISO 8601 date string from backend (UTC)
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted date string in local timezone
 */
export const formatLocalDate = (utcDateString, options = {}) => {
  const date = utcToLocal(utcDateString);
  if (!date) return '';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };
  
  return date.toLocaleDateString(undefined, defaultOptions);
};

/**
 * Formats a UTC date string to local time string
 * 
 * @param {string} utcDateString - ISO 8601 date string from backend (UTC)
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted time string in local timezone
 */
export const formatLocalTime = (utcDateString, options = {}) => {
  const date = utcToLocal(utcDateString);
  if (!date) return '';
  
  const defaultOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    ...options
  };
  
  return date.toLocaleTimeString(undefined, defaultOptions);
};

/**
 * Formats a UTC date string to local date and time string
 * 
 * @param {string} utcDateString - ISO 8601 date string from backend (UTC)
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted date and time string in local timezone
 */
export const formatLocalDateTime = (utcDateString, options = {}) => {
  const date = utcToLocal(utcDateString);
  if (!date) return '';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    ...options
  };
  
  return date.toLocaleString(undefined, defaultOptions);
};

/**
 * Formats a UTC date string for input fields (datetime-local format)
 * Converts UTC to local time and formats as YYYY-MM-DDTHH:mm
 * 
 * @param {string} utcDateString - ISO 8601 date string from backend (UTC)
 * @returns {string} - Formatted string for datetime-local input (YYYY-MM-DDTHH:mm)
 */
export const formatForInput = (utcDateString) => {
  const date = utcToLocal(utcDateString);
  if (!date) return '';
  
  // Format as YYYY-MM-DDTHH:mm for datetime-local input
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

/**
 * Converts a local datetime string (from input) to UTC ISO string for backend
 * 
 * @param {string} localDateTimeString - Local datetime string (YYYY-MM-DDTHH:mm)
 * @returns {string} - ISO 8601 UTC string for backend
 */
export const localToUTC = (localDateTimeString) => {
  if (!localDateTimeString) return null;
  
  // Parse the local datetime string
  const localDate = new Date(localDateTimeString);
  
  // Convert to UTC ISO string
  return localDate.toISOString();
};

/**
 * Gets relative time string (e.g., "2 hours ago", "in 3 days")
 * 
 * @param {string} utcDateString - ISO 8601 date string from backend (UTC)
 * @returns {string} - Relative time string
 */
export const getRelativeTime = (utcDateString) => {
  const date = utcToLocal(utcDateString);
  if (!date) return '';
  
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (Math.abs(diffSecs) < 60) {
    return diffSecs < 0 ? `${Math.abs(diffSecs)} seconds ago` : `in ${diffSecs} seconds`;
  } else if (Math.abs(diffMins) < 60) {
    return diffMins < 0 ? `${Math.abs(diffMins)} minutes ago` : `in ${diffMins} minutes`;
  } else if (Math.abs(diffHours) < 24) {
    return diffHours < 0 ? `${Math.abs(diffHours)} hours ago` : `in ${diffHours} hours`;
  } else if (Math.abs(diffDays) < 7) {
    return diffDays < 0 ? `${Math.abs(diffDays)} days ago` : `in ${diffDays} days`;
  } else {
    return formatLocalDate(utcDateString);
  }
};


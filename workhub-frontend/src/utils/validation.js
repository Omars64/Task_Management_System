/**
 * Frontend validation utilities aligned with backend (relaxed password rules)
 * - Name: letters/spaces/hyphen/apostrophe only, 2–50 chars (NO digits)
 * - Password: 8–128, must include upper+lower+digit+special (any non-alphanumeric)
 * Other validators preserved.
 */
import { useState } from 'react';

// NOTE: Removed COMMON_PASSWORDS + profanity expansions to stay relaxed as requested.

// Regex allowlists
const NAME_REGEX = /^[A-Za-z\s\-']{2,50}$/; // letters/space/hyphen/apostrophe; NO digits
const EMAIL_REGEX = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;

// Lightweight profanity list remains (used by comment validator)
const PROFANITY_WORDS = ['damn', 'hell', 'crap', 'stupid', 'idiot', 'moron', 'fool'];

export const ValidationUtils = {
  // Trim whitespace from string values
  trimString: (value) => (typeof value === 'string' ? value.trim() : value),

  // Email
  validateEmail: (email) => {
    if (!email) return { isValid: false, message: 'Email is required' };
    const v = ValidationUtils.trimString(email);
    if (!EMAIL_REGEX.test(v)) return { isValid: false, message: 'Invalid email format' };
    return { isValid: true, value: v };
  },

  // Password (ENHANCED - P0: 10 chars minimum, 3 of 4 character classes)
  validatePassword: (password) => {
    if (!password) return { isValid: false, message: 'Password is required' };
    
    // P0: Minimum 10 characters (increased from 8)
    if (password.length < 10) 
      return { isValid: false, message: 'Password must be at least 10 characters long' };
    if (password.length > 128) 
      return { isValid: false, message: 'Password must be less than 128 characters' };

    // P0: Require at least 3 of 4 character classes
    let charClasses = 0;
    if (/[A-Z]/.test(password)) charClasses++;
    if (/[a-z]/.test(password)) charClasses++;
    if (/\d/.test(password)) charClasses++;
    if (/[^A-Za-z0-9]/.test(password)) charClasses++;
    
    if (charClasses < 3) 
      return { isValid: false, message: 'Password must include at least 3 of: uppercase, lowercase, digit, special character' };

    // P0: Check for common weak passwords
    const commonPasswords = [
      'password123', 'qwerty123', 'abc123456', 'welcome123', 'admin123',
      'letmein123', 'monkey123', '1234567890', 'password1', 'iloveyou'
    ];
    if (commonPasswords.includes(password.toLowerCase())) 
      return { isValid: false, message: 'Password is too common. Please choose a stronger password' };
    
    // P0: Check for sequential patterns
    if (/(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)/i.test(password))
      return { isValid: false, message: 'Password contains sequential patterns. Please choose a stronger password' };

    return { isValid: true, value: password };
  },

  // Confirm password
  validatePasswordConfirmation: (password, confirmPassword) => {
    if (confirmPassword === undefined || confirmPassword === null || confirmPassword === '')
      return { isValid: false, message: 'Password confirmation is required' };
    if (password !== confirmPassword) return { isValid: false, message: 'Passwords do not match' };
    return { isValid: true, value: confirmPassword };
  },

  // Name (NO digits)
  validateName: (name) => {
    if (!name) return { isValid: false, message: 'Name is required' };
    const v = ValidationUtils.trimString(name);
    if (!NAME_REGEX.test(v))
      return { isValid: false, message: 'Name must be 2–50 characters and cannot contain numbers or symbols' };
    return { isValid: true, value: v };
  },

  // Task title (P1: 3-100 characters)
  validateTaskTitle: (title) => {
    if (!title) return { isValid: false, message: 'Task title is required' };
    const v = ValidationUtils.trimString(title);
    
    // P1: Minimum 3 characters
    if (v.length < 3) return { isValid: false, message: 'Task title must be at least 3 characters' };
    if (v.length > 100) return { isValid: false, message: 'Task title must be 100 characters or less' };
    
    if (/^[!@#$%^&*()_+=\[\]{}|\\:";'<>?,./\s]+$/.test(v))
      return { isValid: false, message: 'Task title cannot consist only of symbols' };
    
    return { isValid: true, value: v };
  },

  // Task description
  validateTaskDescription: (description) => {
    if (!description) return { isValid: false, message: 'Task description is required' };
    const v = ValidationUtils.trimString(description);
    if (v.length < 10) return { isValid: false, message: 'Task description must be at least 10 characters' };
    if (v.length > 1000) return { isValid: false, message: 'Task description must be less than 1000 characters' };

    // Basic XSS hardening
    if (/<script[^>]*>.*?<\/script>/i.test(v)) return { isValid: false, message: 'Description cannot contain script tags' };
    const dangerous = [/javascript:/i, /vbscript:/i, /onload\s*=/i, /onerror\s*=/i, /onclick\s*=/i, /onmouseover\s*=/i];
    if (dangerous.some((re) => re.test(v)))
      return { isValid: false, message: 'Description contains potentially dangerous content' };

    return { isValid: true, value: v };
  },

  // Due date (P1: min 1 hour lead time, max 1 year)
  validateDueDate: (dueDate) => {
    if (!dueDate) return { isValid: true, value: null };
    
    const date = new Date(dueDate);
    if (isNaN(date.getTime())) return { isValid: false, message: 'Invalid date format' };
    
    const now = new Date();
    
    // P1: Minimum lead time of 1 hour
    const minDueDate = new Date(now.getTime() + 60 * 60 * 1000); // 1 hour from now
    if (date < minDueDate) 
      return { isValid: false, message: 'Due date must be at least 1 hour from now' };
    
    // P1: Maximum horizon of 1 year
    const maxFuture = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);
    if (date > maxFuture) 
      return { isValid: false, message: 'Due date cannot be more than 1 year in the future' };
    
    return { isValid: true, value: dueDate };
  },

  // Priority
  validatePriority: (priority) => {
    const valid = ['low', 'medium', 'high'];
    if (!priority) return { isValid: true, value: 'medium' };
    const v = String(priority).toLowerCase().trim();
    if (!valid.includes(v)) return { isValid: false, message: `Priority must be one of: ${valid.join(', ')}` };
    return { isValid: true, value: v };
  },

  // Comment
  validateComment: (content) => {
    if (!content) return { isValid: false, message: 'Comment content is required' };
    const v = ValidationUtils.trimString(content);
    if (v.length > 500) return { isValid: false, message: 'Comment must be less than 500 characters' };
    const lower = v.toLowerCase();
    // Use word boundary check to avoid false positives (e.g., "ass" in "Cassey", "pass", "class")
    const hasProfanity = PROFANITY_WORDS.some((word) => {
      const pattern = new RegExp(`\\b${word}\\b`, 'i');
      return pattern.test(lower);
    });
    if (hasProfanity)
      return { isValid: false, message: 'Comment contains inappropriate content' };
    return { isValid: true, value: v };
  },

  // Generic numeric range
  validateNumericRange: (value, min, max, fieldName) => {
    const num = parseFloat(value);
    if (isNaN(num)) return { isValid: false, message: `${fieldName} must be a valid number` };
    if (num < min || num > max) return { isValid: false, message: `${fieldName} must be between ${min} and ${max}` };
    return { isValid: true, value: num };
  },

  // Hours (time logs)
  validateHours: (hours) => ValidationUtils.validateNumericRange(hours, 0.1, 24.0, 'Hours'),

  // Reminder/Meeting title (3-100 characters)
  validateReminderTitle: (title) => {
    if (!title) return { isValid: false, message: 'Title is required' };
    const v = ValidationUtils.trimString(title);
    
    if (v.length < 3) return { isValid: false, message: 'Title must be at least 3 characters' };
    if (v.length > 100) return { isValid: false, message: 'Title must be 100 characters or less' };
    
    if (/^[!@#$%^&*()_+=\[\]{}|\\:";'<>?,./\s]+$/.test(v))
      return { isValid: false, message: 'Title cannot consist only of symbols' };
    
    return { isValid: true, value: v };
  },

  // Reminder/Meeting description (max 500 characters)
  validateReminderDescription: (description) => {
    if (!description) return { isValid: true, value: '' }; // Optional
    const v = ValidationUtils.trimString(description);
    if (v.length > 500) return { isValid: false, message: 'Description must be 500 characters or less' };

    // Basic XSS hardening
    if (/<script[^>]*>.*?<\/script>/i.test(v)) return { isValid: false, message: 'Description cannot contain script tags' };
    const dangerous = [/javascript:/i, /vbscript:/i, /onload\s*=/i, /onerror\s*=/i, /onclick\s*=/i, /onmouseover\s*=/i];
    if (dangerous.some((re) => re.test(v)))
      return { isValid: false, message: 'Description contains potentially dangerous content' };

    return { isValid: true, value: v };
  },

  // Reminder date validation
  validateReminderDate: (reminderDate) => {
    if (!reminderDate) return { isValid: false, message: 'Reminder date is required' };
    
    const date = new Date(reminderDate);
    if (isNaN(date.getTime())) return { isValid: false, message: 'Invalid date format' };
    
    const now = new Date();
    
    // Cannot set reminder in the past
    if (date < now) 
      return { isValid: false, message: 'Reminder date cannot be in the past' };
    
    // Warn if reminder is too far in the future (>1 year)
    const maxFuture = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);
    if (date > maxFuture) 
      return { isValid: false, message: 'Reminder date cannot be more than 1 year in the future', warning: true };
    
    return { isValid: true, value: reminderDate };
  },

  // Days before validation (1-365)
  validateDaysBefore: (days) => {
    if (!days) return { isValid: false, message: 'Days before is required' };
    const num = parseInt(days, 10);
    if (isNaN(num)) return { isValid: false, message: 'Days before must be a valid number' };
    if (num < 1) return { isValid: false, message: 'Days before must be at least 1' };
    if (num > 365) return { isValid: false, message: 'Days before cannot exceed 365 days' };
    return { isValid: true, value: num };
  },

  // Meeting time validation
  validateMeetingTimes: (startTime, endTime) => {
    if (!startTime) return { isValid: false, message: 'Start time is required', field: 'start_time' };
    if (!endTime) return { isValid: false, message: 'End time is required', field: 'end_time' };
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    
    if (isNaN(start.getTime())) return { isValid: false, message: 'Invalid start time format', field: 'start_time' };
    if (isNaN(end.getTime())) return { isValid: false, message: 'Invalid end time format', field: 'end_time' };
    
    const now = new Date();
    // Get today's date at midnight for date comparison
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startDate = new Date(start.getFullYear(), start.getMonth(), start.getDate());
    
    // Prevent scheduling before today (no past dates at all)
    if (startDate < today) 
      return { isValid: false, message: 'Meeting cannot be scheduled on a past date', field: 'start_time' };
    
    // If scheduling today, must be in the future (not in past hours)
    if (startDate.getTime() === today.getTime() && start < now) 
      return { isValid: false, message: 'Meeting start time cannot be in the past', field: 'start_time' };
    
    // Prevent scheduling more than 1 year ahead
    const maxFuture = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);
    if (start > maxFuture) 
      return { isValid: false, message: 'Meeting cannot be scheduled more than 1 year in advance', field: 'start_time' };
    
    if (end > maxFuture) 
      return { isValid: false, message: 'Meeting end time cannot be more than 1 year in advance', field: 'end_time' };
    
    // End time must be after start time
    if (end <= start) 
      return { isValid: false, message: 'End time must be after start time', field: 'end_time' };
    
    // Meeting duration limits (max 8 hours)
    const durationHours = (end - start) / (1000 * 60 * 60);
    if (durationHours > 8) 
      return { isValid: false, message: 'Meeting duration cannot exceed 8 hours', field: 'end_time' };
    
    // Warn if meeting is outside business hours (7 AM to 6 PM)
    const startHour = start.getHours();
    const endHour = end.getHours();
    const endMinute = end.getMinutes();
    
    // Check if start is before 7 AM or after 6 PM
    if (startHour < 7 || startHour >= 18) {
      return { 
        isValid: true, 
        value: { startTime, endTime }, 
        warning: 'Meeting is scheduled outside business hours (7 AM - 6 PM)',
        field: 'start_time'
      };
    }
    
    // Check if end is after 6 PM (18:00)
    if (endHour > 18 || (endHour === 18 && endMinute > 0)) {
      return { 
        isValid: true, 
        value: { startTime, endTime }, 
        warning: 'Meeting ends outside business hours (7 AM - 6 PM)',
        field: 'end_time'
      };
    }
    
    return { isValid: true, value: { startTime, endTime } };
  },

  // File upload
  validateFileUpload: (file, allowedTypes = ['jpg', 'jpeg', 'png', 'pdf'], maxSizeMB = 2) => {
    if (!file) return { isValid: false, message: 'File is required' };
    const ext = (file.name || '').toLowerCase().split('.').pop();
    if (!allowedTypes.includes(ext))
      return { isValid: false, message: `File type not allowed. Allowed types: ${allowedTypes.join(', ')}` };
    const maxBytes = maxSizeMB * 1024 * 1024;
    if ((file.size || 0) > maxBytes) return { isValid: false, message: `File size must be less than ${maxSizeMB}MB` };
    const blocked = ['exe', 'bat', 'cmd', 'com', 'scr', 'pif', 'vbs', 'js', 'jar'];
    if (blocked.includes(ext)) return { isValid: false, message: 'Executable files are not allowed' };
    return { isValid: true, value: file };
  },

  // Form-level helper to keep compatibility with existing callers
  validateForm: (formData, formType) => {
    const errors = {};
    const warnings = {};

    switch (formType) {
      case 'userRegistration': {
        const e1 = ValidationUtils.validateEmail(formData.email);
        if (!e1.isValid) errors.email = e1.message;

        const e2 = ValidationUtils.validatePassword(formData.password);
        if (!e2.isValid) errors.password = e2.message;

        const e3 = ValidationUtils.validatePasswordConfirmation(formData.password, formData.confirmPassword);
        if (!e3.isValid) errors.confirmPassword = e3.message;

        const e4 = ValidationUtils.validateName(formData.name);
        if (!e4.isValid) errors.name = e4.message;
        break;
      }

      case 'taskCreation': {
        const t = ValidationUtils.validateTaskTitle(formData.title);
        if (!t.isValid) errors.title = t.message;

        const d = ValidationUtils.validateTaskDescription(formData.description);
        if (!d.isValid) errors.description = d.message;

        const dd = ValidationUtils.validateDueDate(formData.due_date);
        if (!dd.isValid) errors.due_date = dd.message;

        const p = ValidationUtils.validatePriority(formData.priority);
        if (!p.isValid) errors.priority = p.message;
        break;
      }

      case 'comment': {
        const c = ValidationUtils.validateComment(formData.content);
        if (!c.isValid) errors.content = c.message;
        break;
      }

      case 'timeLog': {
        const h = ValidationUtils.validateHours(formData.hours);
        if (!h.isValid) errors.hours = h.message;
        break;
      }

      case 'reminder': {
        const title = ValidationUtils.validateReminderTitle(formData.title);
        if (!title.isValid) errors.title = title.message;

        const desc = ValidationUtils.validateReminderDescription(formData.description);
        if (!desc.isValid) errors.description = desc.message;

        // Validate based on reminder type
        if (formData.reminder_type === 'custom' && formData.reminder_date) {
          const date = ValidationUtils.validateReminderDate(formData.reminder_date);
          if (!date.isValid) errors.reminder_date = date.message;
          if (date.warning) warnings.reminder_date = date.message;
        }

        if (formData.reminder_type === 'time_based' && formData.time_based) {
          const date = ValidationUtils.validateReminderDate(formData.time_based);
          if (!date.isValid) errors.time_based = date.message;
          if (date.warning) warnings.time_based = date.message;
        }

        if ((formData.reminder_type === 'days_before') && formData.days_before) {
          const days = ValidationUtils.validateDaysBefore(formData.days_before);
          if (!days.isValid) errors.days_before = days.message;
        }
        break;
      }

      case 'meeting': {
        const title = ValidationUtils.validateReminderTitle(formData.title);
        if (!title.isValid) errors.title = title.message;

        const desc = ValidationUtils.validateReminderDescription(formData.description);
        if (!desc.isValid) errors.description = desc.message;

        const times = ValidationUtils.validateMeetingTimes(formData.start_time, formData.end_time);
        if (!times.isValid) {
          errors[times.field] = times.message;
        }
        if (times.warning) {
          warnings[times.field] = times.warning;
        }
        break;
      }

      default:
        break;
    }

    return { isValid: Object.keys(errors).length === 0, errors, warnings };
  },
};

// Hook with real-time feedback (unchanged API)
export const useFormValidation = (formType) => {
  const [errors, setErrors] = useState({});
  const [warnings, setWarnings] = useState({});

  const validateField = (fieldName, value, formData = {}) => {
    let r = { isValid: true };

    switch (fieldName) {
      case 'email': r = ValidationUtils.validateEmail(value); break;
      case 'password': r = ValidationUtils.validatePassword(value); break;
      case 'confirmPassword': r = ValidationUtils.validatePasswordConfirmation(formData.password, value); break;
      case 'name': r = ValidationUtils.validateName(value); break;
      case 'title': 
        // Use appropriate validator based on form type
        if (formType === 'reminder' || formType === 'meeting') {
          r = ValidationUtils.validateReminderTitle(value);
        } else {
          r = ValidationUtils.validateTaskTitle(value);
        }
        break;
      case 'description': 
        if (formType === 'reminder' || formType === 'meeting') {
          r = ValidationUtils.validateReminderDescription(value);
        } else {
          r = ValidationUtils.validateTaskDescription(value);
        }
        break;
      case 'due_date': r = ValidationUtils.validateDueDate(value); break;
      case 'priority': r = ValidationUtils.validatePriority(value); break;
      case 'content': r = ValidationUtils.validateComment(value); break;
      case 'hours': r = ValidationUtils.validateHours(value); break;
      case 'reminder_date': r = ValidationUtils.validateReminderDate(value); break;
      case 'time_based': r = ValidationUtils.validateReminderDate(value); break;
      case 'days_before': r = ValidationUtils.validateDaysBefore(value); break;
      case 'start_time':
      case 'end_time':
        r = ValidationUtils.validateMeetingTimes(formData.start_time || value, formData.end_time || value);
        break;
      default: break;
    }

    if (!r.isValid) {
      setErrors((prev) => ({ ...prev, [fieldName]: r.message }));
      setWarnings((prev) => {
        const next = { ...prev };
        delete next[fieldName];
        return next;
      });
    } else {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[fieldName];
        return next;
      });
      // Handle warnings
      if (r.warning) {
        setWarnings((prev) => ({ ...prev, [fieldName]: r.warning }));
      } else {
        setWarnings((prev) => {
          const next = { ...prev };
          delete next[fieldName];
          return next;
        });
      }
    }
    return r.isValid;
  };

  const validateForm = (formData) => {
    const res = ValidationUtils.validateForm(formData, formType);
    setErrors(res.errors);
    setWarnings(res.warnings);
    return res.isValid;
    };

  const clearErrors = () => { setErrors({}); setWarnings({}); };

  return { errors, warnings, validateField, validateForm, clearErrors };
};

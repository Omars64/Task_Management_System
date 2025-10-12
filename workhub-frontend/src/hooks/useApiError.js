import { useNotification } from '../context/NotificationContext';

export const useApiError = () => {
  const { error: showError, success: showSuccess } = useNotification();

  const handleApiError = (error, customMessage = null) => {
    let message = customMessage;
    
    if (!message) {
      if (error.response?.data?.error) {
        message = error.response.data.error;
      } else if (error.response?.data?.message) {
        message = error.response.data.message;
      } else if (error.message) {
        message = error.message;
      } else {
        message = 'An unexpected error occurred. Please try again.';
      }
    }
    
    showError(message);
  };

  const handleApiSuccess = (message) => {
    showSuccess(message);
  };

  return {
    handleApiError,
    handleApiSuccess,
  };
};
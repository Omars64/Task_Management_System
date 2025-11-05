import React, { useState, useRef } from 'react';
import { FiUpload, FiX, FiFile, FiDownload, FiTrash2 } from 'react-icons/fi';
import { filesAPI } from '../services/api';

export const FileUpload = ({ taskId, onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFiles(e.dataTransfer.files[0]);
    }
  };

  const handleChange = async (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await handleFiles(e.target.files[0]);
    }
  };

  const handleFiles = async (file) => {
    setError('');
    
    // Validate file size (50 MB max)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File is too large. Maximum size is 50 MB.');
      return;
    }

    // Validate file type
    const allowedTypes = [
      'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx',
      'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z',
      'mp4', 'avi', 'mov', 'mp3', 'wav',
      'csv', 'json', 'xml', 'md', 'log'
    ];
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      setError(`File type .${fileExt} is not allowed.`);
      return;
    }

    // Upload file
    setUploading(true);
    try {
      await filesAPI.uploadToTask(taskId, file);
      if (onUploadSuccess) {
        onUploadSuccess();
      }
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div>
      <form
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onSubmit={(e) => e.preventDefault()}
        style={{
          border: `2px dashed ${dragActive ? 'var(--primary-color)' : 'var(--border-color)'}`,
          borderRadius: '8px',
          padding: '24px',
          textAlign: 'center',
          backgroundColor: dragActive ? 'var(--background-light)' : 'transparent',
          transition: 'all 0.3s ease',
          cursor: 'pointer'
        }}
        onClick={onButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple={false}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        
        <FiUpload style={{ fontSize: '48px', color: 'var(--text-light)', marginBottom: '12px' }} />
        
        <p style={{ marginBottom: '8px', color: 'var(--text-color)', fontWeight: 500 }}>
          {uploading ? 'Uploading...' : 'Drag and drop file here'}
        </p>
        
        <p style={{ fontSize: '0.875rem', color: 'var(--text-light)', marginBottom: '12px' }}>
          or click to select a file
        </p>
        
        <p style={{ fontSize: '0.75rem', color: 'var(--text-light)' }}>
          Maximum file size: 50 MB
        </p>
        
        <p style={{ fontSize: '0.75rem', color: 'var(--text-light)' }}>
          Allowed types: PDF, images, documents, archives, videos, audio
        </p>
      </form>
      
      {error && (
        <div style={{
          marginTop: '12px',
          padding: '12px',
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '6px',
          color: '#dc2626',
          fontSize: '0.875rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>{error}</span>
          <button
            onClick={() => setError('')}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#dc2626',
              padding: '4px',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <FiX />
          </button>
        </div>
      )}
    </div>
  );
};

export const AttachmentsList = ({ attachments, onDelete, onDownload }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (fileType) => {
    if (fileType?.startsWith('image/')) return '🖼️';
    if (fileType?.startsWith('video/')) return '🎥';
    if (fileType?.startsWith('audio/')) return '🎵';
    if (fileType?.includes('pdf')) return '📄';
    if (fileType?.includes('zip') || fileType?.includes('rar')) return '📦';
    if (fileType?.includes('word') || fileType?.includes('document')) return '📝';
    if (fileType?.includes('excel') || fileType?.includes('spreadsheet')) return '📊';
    if (fileType?.includes('powerpoint') || fileType?.includes('presentation')) return '📽️';
    return '📁';
  };

  if (!attachments || attachments.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '32px',
        color: 'var(--text-light)',
        fontSize: '0.95rem'
      }}>
        <FiFile style={{ fontSize: '48px', marginBottom: '12px', opacity: 0.5 }} />
        <p>No attachments yet</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {attachments.map((attachment) => (
        <div
          key={attachment.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            backgroundColor: 'var(--background-light)',
            transition: 'all 0.2s ease'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
            <span style={{ fontSize: '24px' }}>{getFileIcon(attachment.file_type)}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                margin: 0,
                fontWeight: 500,
                color: 'var(--text-color)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {attachment.original_filename}
              </p>
              <p style={{
                margin: 0,
                fontSize: '0.8125rem',
                color: 'var(--text-light)'
              }}>
                {formatFileSize(attachment.file_size)} • Uploaded by {attachment.user_name}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => onDownload(attachment)}
              style={{
                padding: '8px',
                background: 'none',
                border: '1px solid var(--border-color)',
                borderRadius: '4px',
                cursor: 'pointer',
                color: 'var(--primary-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title="Download"
            >
              <FiDownload />
            </button>
            <button
              onClick={() => onDelete(attachment)}
              style={{
                padding: '8px',
                background: 'none',
                border: '1px solid var(--border-color)',
                borderRadius: '4px',
                cursor: 'pointer',
                color: '#dc2626',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title="Delete"
            >
              <FiTrash2 />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};


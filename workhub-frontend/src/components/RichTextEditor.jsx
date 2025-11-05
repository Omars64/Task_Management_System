import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import './RichTextEditor.css';

const RichTextEditor = ({ 
  value, 
  onChange, 
  placeholder = 'Write a comment...', 
  maxLength = 500,
  users = [],
  onMention 
}) => {
  const quillRef = useRef(null);
  const [showMentionList, setShowMentionList] = useState(false);
  const [mentionSearch, setMentionSearch] = useState('');
  const [mentionPosition, setMentionPosition] = useState({ top: 0, left: 0 });
  const [mentionStart, setMentionStart] = useState(-1);
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);

  const handleMentionSelect = useCallback((user) => {
    if (!quillRef.current || mentionStart === -1) return;
    
    const quill = quillRef.current.getEditor();
    const cursorPos = quill.getSelection()?.index || 0;
    
    // Delete the partial @mention
    quill.deleteText(mentionStart, cursorPos - mentionStart);
    
    // Insert the mention
    quill.insertText(mentionStart, `@${user.name}`, 'user', user.id);
    
    // Add space after mention
    quill.insertText(mentionStart + user.name.length + 1, ' ', 'user', null);
    
    setShowMentionList(false);
    setMentionStart(-1);
    setSelectedMentionIndex(0);
    
    if (onMention) {
      onMention(user);
    }
  }, [mentionStart, onMention]);

  // Calculate filtered users based on search term
  const filteredUsers = mentionSearch.trim() === '' 
    ? users.slice(0, 5)
    : users.filter(user => 
        user.name.toLowerCase().includes(mentionSearch.toLowerCase()) ||
        (user.email && user.email.toLowerCase().includes(mentionSearch.toLowerCase()))
      ).slice(0, 5);

  useEffect(() => {
    if (!quillRef.current) return;

    const quill = quillRef.current.getEditor();
    
    // Handle @mention triggers
    quill.on('text-change', (delta, oldDelta, source) => {
      if (source === 'user') {
        const text = quill.getText();
        const cursorPos = quill.getSelection()?.index || 0;
        const textBeforeCursor = text.substring(0, cursorPos);
        
        // Find @mentions - show dropdown when @ is typed, even with no text after
        const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
        
        if (mentionMatch || textBeforeCursor.endsWith('@')) {
          const matchStart = textBeforeCursor.lastIndexOf('@');
          setMentionStart(matchStart);
          // Extract search term (empty string if just "@")
          setMentionSearch(mentionMatch ? mentionMatch[1] : '');
          setSelectedMentionIndex(0); // Reset selection when search changes
          
          // Get cursor position for dropdown
          const bounds = quill.getBounds(cursorPos);
          if (bounds) {
            setMentionPosition({
              top: bounds.top + 20,
              left: bounds.left
            });
            setShowMentionList(true);
          }
        } else {
          setShowMentionList(false);
          setMentionStart(-1);
          setSelectedMentionIndex(0);
        }
      }
    });

    // Close mention list on click outside
    const handleClickOutside = (e) => {
      if (!e.target.closest('.mention-dropdown') && !e.target.closest('.ql-editor')) {
        setShowMentionList(false);
        setMentionStart(-1);
        setSelectedMentionIndex(0);
      }
    };
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [users]);

  // Separate effect for keyboard navigation
  useEffect(() => {
    if (!showMentionList || filteredUsers.length === 0) return;
    
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedMentionIndex(prev => Math.min(prev + 1, filteredUsers.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedMentionIndex(prev => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && filteredUsers[selectedMentionIndex]) {
        e.preventDefault();
        handleMentionSelect(filteredUsers[selectedMentionIndex]);
      } else if (e.key === 'Escape') {
        setShowMentionList(false);
        setMentionStart(-1);
        setSelectedMentionIndex(0);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showMentionList, filteredUsers, selectedMentionIndex, handleMentionSelect]);


  const modules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      ['link'],
      ['clean']
    ]
    // Note: Mention functionality is handled manually via text-change events
    // We don't use Quill's mention module to avoid import errors
  };

  const formats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'list', 'bullet', 'link'
  ];

  // Calculate character count (strip HTML tags)
  const getPlainTextLength = (html) => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html || '';
    return tmp.textContent?.length || 0;
  };

  const plainTextLength = getPlainTextLength(value);

  return (
    <div className="rich-text-editor-wrapper">
      <ReactQuill
        ref={quillRef}
        theme="snow"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        modules={modules}
        formats={formats}
        className="rich-text-editor"
      />
      
      {showMentionList && (
        <div 
          className="mention-dropdown"
          style={{
            position: 'absolute',
            top: mentionPosition.top + 'px',
            left: mentionPosition.left + 'px',
            zIndex: 1000
          }}
        >
          {filteredUsers.length > 0 ? (
            filteredUsers.map((user, index) => (
              <div
                key={user.id}
                className={`mention-option ${index === selectedMentionIndex ? 'mention-option-selected' : ''}`}
                onClick={() => handleMentionSelect(user)}
                onMouseEnter={() => setSelectedMentionIndex(index)}
              >
                <strong>{user.name}</strong>
                {user.email && <span className="mention-email">{user.email}</span>}
              </div>
            ))
          ) : (
            <div className="mention-option" style={{ color: 'var(--text-light, #999)', fontStyle: 'italic' }}>
              No users found
            </div>
          )}
        </div>
      )}
      
      <div className="rich-text-editor-footer">
        <span className={plainTextLength > maxLength * 0.9 ? 'char-count-warning' : 'char-count'}>
          {plainTextLength} / {maxLength} characters
        </span>
      </div>
    </div>
  );
};

export default RichTextEditor;

